from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Central de Lançamentos", page_icon="➕", layout="wide"
)


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def garantir_tabelas():
  try:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor NUMERIC(10,2) NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS desafio_aportes (
            id SERIAL PRIMARY KEY,
            data TEXT NOT NULL,
            valor NUMERIC(10,2) NOT NULL,
            local_aplicacao TEXT NOT NULL
        )
    """
    )
    conexao.commit()
    cursor.close()
    conexao.close()
  except Exception:
    pass


garantir_tabelas()

st.subheader("➕ Central de Lançamentos e Aportes")
st.write(
    "Escolha abaixo entre registrar um gasto/receita corriqueiro ou fazer o"
    " seu aporte direto na reserva diversificada."
)


def fmt_moeda(v):
  return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Abas para separar o dia a dia do investimento
aba_lancamento, aba_aporte = st.tabs(
    ["📝 Gasto ou Receita", "🛡️ Registrar Aporte na Reserva"]
)

# --- ABA 1: GASTO OU RECEITA ---
with aba_lancamento:
  st.markdown("### Registrar Gasto ou Receita")
  with st.form("form_lancamento", clear_on_submit=True):
    tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
    categoria = st.text_input(
        "Categoria (Ex: Alimentação, Moradia, Transporte, Cartão)"
    )
    descricao = st.text_input("Descrição / Estabelecimento")

    valor_texto = st.text_input(
        "Valor (Ex: digite 12 para 12,00 ou 1250 para 12,50)",
        value="",
        placeholder="Ex: 12 ou 15050",
    )

    valor_final = 0.0
    if valor_texto:
      try:
        limpo = valor_texto.strip().replace(",", ".")
        if "." in limpo:
          valor_final = float(limpo)
        else:
          if len(limpo) <= 2:
            valor_final = float(limpo)
          else:
            valor_final = float(limpo) / 100.0
      except ValueError:
        valor_final = 0.0

    if valor_final > 0:
      st.info(f"Valor a ser lançado: **{fmt_moeda(valor_final)}**")

    data_hoje_str = datetime.now().strftime("%d/%m/%Y")
    data_texto = st.text_input(
        "Data do Lançamento (DD/MM/AAAA)",
        value=data_hoje_str,
        placeholder="Ex: 05/09/2026",
    )

    enviar = st.form_submit_button("Salvar Lançamento")

    if enviar:
      try:
        data_obj = datetime.strptime(data_texto.strip(), "%d/%m/%Y")
        data_formatada = data_obj.strftime("%d/%m/%Y")
        data_valida = True
      except ValueError:
        data_valida = False

      if categoria and valor_final > 0 and data_valida:
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              """
                    INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
              (data_formatada, tipo, categoria, descricao, valor_final),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento salvo com sucesso no banco em nuvem!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")
      else:
        st.error(
            "Preencha a categoria, um valor válido e uma data correta no"
            " formato DD/MM/AAAA."
        )

  st.divider()
  st.markdown("### 📊 Resumo de Créditos e Débitos Lançados")

  try:
    conexao = obter_conexao()
    df_lanc = pd.read_sql_query(
        "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos"
        " ORDER BY id DESC",
        conexao,
    )
    conexao.close()
  except Exception:
    df_lanc = pd.DataFrame(
        columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
    )

  if not df_lanc.empty:
    df_lanc["valor_num"] = pd.to_numeric(
        df_lanc["valor"], errors="coerce"
    ).fillna(0.0)
    total_receitas = df_lanc[df_lanc["tipo"] == "Receita"]["valor_num"].sum()
    total_despesas = df_lanc[df_lanc["tipo"] == "Despesa"]["valor_num"].sum()
    saldo_mes = total_receitas - total_despesas

    c1, c2, c3 = st.columns(3)
    with c1:
      st.metric("Total Créditos (Receitas)", fmt_moeda(total_receitas))
    with c2:
      st.metric("Total Débitos (Despesas)", fmt_moeda(total_despesas))
    with c3:
      st.metric("Balanço do Período", fmt_moeda(saldo_mes))

    st.write("")
    df_exibe_lanc = df_lanc[
        ["data", "tipo", "categoria", "descricao", "valor_num"]
    ].rename(
        columns={
            "data": "Data",
            "tipo": "Tipo",
            "categoria": "Categoria",
            "descricao": "Descrição",
            "valor_num": "Valor",
        }
    )
    df_exibe_lanc["Valor"] = df_exibe_lanc["Valor"].apply(fmt_moeda)
    st.dataframe(df_exibe_lanc.head(10), use_container_width=True, hide_index=True)
  else:
    st.info("Nenhum lançamento de receita ou despesa registrado até o momento.")

# --- ABA 2: APORTE NA RESERVA ---
with aba_aporte:
  st.markdown("### Registrar Novo Depósito / Aporte")
  with st.form("form_novo_aporte", clear_on_submit=True):
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
      data_aporte = st.text_input(
          "Data do Depósito (DD/MM/AAAA)",
          value=datetime.now().strftime("%d/%m/%Y"),
      )
    with col_a2:
      valor_aporte = st.number_input(
          "Valor Depositado (R$)",
          min_value=1.0,
          value=532.00,
          step=10.0,
          format="%.2f",
      )
    with col_a3:
      locais_disponiveis = [
          "Sofisa Direto (CDB 105% CDI)",
          "Banco Inter (CDB Liquidez Diária)",
          "Nubank (Caixinha / RDB 100% CDI)",
          "Tesouro Selic (Tesouro Direto)",
          "Banco XP / Rico (CDB ou LCI)",
          "Outro (Personalizado)",
      ]
      local_selecionado = st.selectbox("Local da Aplicação", locais_disponiveis)

    local_aporte = local_selecionado
    if local_selecionado == "Outro (Personalizado)":
      local_aporte = st.text_input("Especifique o Banco / Corretora")

    if st.form_submit_button("💾 Salvar Aporte no Desafio"):
      try:
        datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES"
            " (%s, %s, %s)",
            (data_aporte.strip(), valor_aporte, local_aporte.strip()),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success("Aporte registrado com sucesso!")
        st.rerun()
      except ValueError:
        st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
      except Exception as e:
        st.error(f"Erro ao salvar: {e}")

  st.divider()
  st.markdown("### 🏦 Saldos e Distribuição por Banco / Corretora")

  try:
    conexao = obter_conexao()
    df_aportes = pd.read_sql_query(
        "SELECT id, data, valor, local_aplicacao FROM desafio_aportes ORDER BY id"
        " DESC",
        conexao,
    )
    conexao.close()
  except Exception:
    df_aportes = pd.DataFrame(
        columns=["id", "data", "valor", "local_aplicacao"]
    )

  if not df_aportes.empty:
    df_aportes["valor_num"] = pd.to_numeric(
        df_aportes["valor"], errors="coerce"
    ).fillna(0.0)
    total_aportado = df_aportes["valor_num"].sum()

    st.metric("Total Geral Guardado em Reservas", fmt_moeda(total_aportado))
    st.write("")

    df_resumo_bancos = (
        df_aportes.groupby("local_aplicacao")["valor_num"].sum().reset_index()
    )
    df_resumo_bancos["Valor Acumulado"] = df_resumo_bancos["valor_num"].apply(
        fmt_moeda
    )
    df_resumo_bancos["% do Total"] = (
        (df_resumo_bancos["valor_num"] / total_aportado) * 100
    ).apply(lambda x: f"{x:.1f}%")

    df_tabela_bancos = df_resumo_bancos[
        ["local_aplicacao", "Valor Acumulado", "% do Total"]
    ].rename(columns={"local_aplicacao": "Instituição / Local"})
    st.dataframe(df_tabela_bancos, use_container_width=True, hide_index=True)
  else:
    st.info("Nenhum aporte registrado para calcular os saldos por banco ainda.")