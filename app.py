from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro Pro", page_icon="💰", layout="centered"
)


# Conexão com o Banco de Dados PostgreSQL no Supabase via Secrets
def obter_conexao():
  url_conexao = st.secrets["DATABASE_URL"]
  return psycopg2.connect(url_conexao)


# Inicializar as tabelas no Supabase caso não existam
def inicializar_banco():
  try:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT,
                tipo TEXT,
                categoria TEXT,
                descricao TEXT,
                valor REAL
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id SERIAL PRIMARY KEY,
                credor TEXT,
                valor_total REAL,
                juros_mensal REAL,
                status TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS desafio_aportes (
                id SERIAL PRIMARY KEY,
                data TEXT,
                valor REAL,
                local_aplicacao TEXT
            )
        """)
    conexao.commit()
    cursor.close()
    conexao.close()
  except Exception as e:
    st.error(
        f"Erro ao conectar com o banco de dados no Supabase: {e}. Verifique a"
        " URL nos Secrets."
    )
    st.stop()


inicializar_banco()

menu = st.sidebar.selectbox(
    "Menu Principal",
    [
        "📊 Painel & Gráficos",
        "➕ Novo Lançamento",
        "🎯 Desafio Reserva / Aportes",
        "⚠️ Raio-X de Dívidas",
        "💡 Orientação & Investimentos",
    ],
)

# Carregar dados do Supabase para DataFrames do Pandas
try:
  conexao = obter_conexao()
  df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
  df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
  df_aportes = pd.read_sql_query("SELECT * FROM desafio_aportes", conexao)
  conexao.close()
except Exception:
  df_lancamentos = pd.DataFrame(
      columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
  )
  df_dividas = pd.DataFrame(
      columns=["id", "credor", "valor_total", "juros_mensal", "status"]
  )
  df_aportes = pd.DataFrame(
      columns=["id", "data", "valor", "local_aplicacao"]
  )


def fmt_moeda(valor):
  return (
      f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  )


if menu == "📊 Painel & Gráficos":
  st.title("💰 Controle Financeiro - Sair do Vermelho")
  st.write("Aplicativo de controle total de créditos, débitos e investimentos.")

  if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor"] = pd.to_numeric(
        df_lancamentos["valor"], errors="coerce"
    ).fillna(0.0)

    total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"][
        "valor"
    ].sum()
    total_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"][
        "valor"
    ].sum()
    saldo = total_receitas - total_despesas

    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", fmt_moeda(total_receitas))
    col2.metric("Saídas", fmt_moeda(total_despesas))

    if saldo >= 0:
      col3.metric("Saldo Atual", fmt_moeda(saldo), delta="No Azul 💙")
    else:
      col3.metric(
          "Saldo Atual",
          fmt_moeda(saldo),
          delta="No Vermelho 🔴",
          delta_color="inverse",
      )

    st.divider()
    st.subheader("Histórico de Lançamentos")
    df_exibicao = df_lancamentos.tail(10).copy()
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
  else:
    st.info("Nenhum lançamento registrado ainda.")

elif menu == "➕ Novo Lançamento":
  st.title("➕ Central de Lançamentos e Aportes")

  tipo_registro = st.radio(
      "O que deseja registrar?",
      ["Gasto ou Receita Comum", "Aporte / Investimento na Reserva"],
  )

  if tipo_registro == "Gasto ou Receita Comum":
    st.subheader("Registrar Nova Receita ou Despesa")
    with st.form("form_comum"):
      data_l = st.text_input(
          "Data (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y")
      )
      tipo_l = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria_l = st.text_input("Categoria (Ex: Aluguel, Alimentação)")
      descricao_l = st.text_input("Descrição")
      valor_l = st.number_input(
          "Valor (R$)", min_value=0.01, step=10.0, format="%.2f"
      )

      if st.form_submit_button("Salvar Lançamento"):
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              "INSERT INTO lancamentos (data, tipo, categoria, descricao,"
              " valor) VALUES (%s, %s, %s, %s, %s)",
              (
                  data_l,
                  tipo_l,
                  categoria_l,
                  descricao_l,
                  float(valor_l),
              ),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento salvo com sucesso!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")
  else:
    st.subheader("📥 Registrar Novo Depósito / Aporte na Reserva")
    st.write(
        "Ao salvar por aqui, o valor será somado ao seu Desafio e lançado"
        " automaticamente como uma **Despesa** no seu fluxo de caixa, abatendo"
        " do seu saldo atual."
    )

    with st.form("form_aporte_integrado"):
      col_i1, col_i2 = st.columns(2)
      with col_i1:
        data_aporte = st.text_input(
            "Data do Depósito (DD/MM/AAAA)",
            value=datetime.now().strftime("%d/%m/%Y"),
        )
      with col_i2:
        valor_aporte = st.number_input(
            "Valor Depositado (R$)",
            min_value=1.0,
            value=532.00,
            step=10.0,
            format="%.2f",
        )

      locais_geral = [
          "Banco Itaú",
          "Nomad (Investimentos em Dólar)",
          "Sofisa Direto (CDB 105% CDI)",
          "Banco Inter (CDB Liquidez Diária)",
          "Nubank (Caixinha / RDB 100% CDI)",
          "Tesouro Selic (Tesouro Direto)",
          "Outro (Personalizado)",
      ]
      local_sel = st.selectbox("Local da Aplicação", locais_geral)
      local_outro = st.text_input(
          "Se selecionou 'Outro (Personalizado)' acima, digite o nome do Banco"
          " ou Corretora:"
      )

      if st.form_submit_button(
          "💾 Salvar Aporte (Atualiza Desafio e Abate do Saldo)"
      ):
        if local_sel == "Outro (Personalizado)":
          local_final = local_outro.strip() if local_outro.strip() else "Outro"
        else:
          local_final = local_sel

        try:
          datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
          conexao = obter_conexao()
          cursor = conexao.cursor()

          # 1. Salva na tabela do Desafio
          cursor.execute(
              "INSERT INTO desafio_aportes (data, valor, local_aplicacao)"
              " VALUES (%s, %s, %s)",
              (
                  data_aporte.strip(),
                  float(valor_aporte),
                  local_final,
              ),
          )

          # 2. Insere automaticamente como despesa para abater do saldo
          cursor.execute(
              "INSERT INTO lancamentos (data, tipo, categoria, descricao,"
              " valor) VALUES (%s, %s, %s, %s, %s)",
              (
                  data_aporte.strip(),
                  "Despesa",
                  "Investimento / Reserva",
                  f"Aporte: {local_final}",
                  float(valor_aporte),
              ),
          )

          conexao.commit()
          cursor.close()
          conexao.close()
          st.success(
              "Aporte registrado com sucesso! Adicionado ao desafio e abatido"
              " do saldo."
          )
          st.rerun()
        except ValueError:
          st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")

elif menu == "🎯 Desafio Reserva / Aportes":
  st.title("🎯 Gerenciamento do Desafio de Reserva")

  if not df_aportes.empty:
    df_aportes["valor_num"] = (
        pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    )
    total_guardado = df_aportes["valor_num"].sum()

    st.metric("Total Geral Guardado em Reservas", fmt_moeda(total_guardado))

    st.subheader("📊 Distribuição por Banco / Corretora")
    df_resumo = (
        df_aportes.groupby("local_aplicacao")["valor_num"].sum().reset_index()
    )
    df_resumo["% do Total"] = (
        (df_resumo["valor_num"] / total_guardado) * 100
    ).apply(lambda x: f"{x:.1f}%")
    df_resumo["Valor Acumulado"] = df_resumo["valor_num"].apply(fmt_moeda)
    df_tabela = df_resumo[
        ["local_aplicacao", "Valor Acumulado", "% do Total"]
    ].rename(columns={"local_aplicacao": "Instituição / Local"})
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.subheader("📋 Extrato de Aportes")
    df_extrato = df_aportes[["id", "data", "local_aplicacao", "valor_num"]].rename(
        columns={"local_aplicacao": "Local da Aplicação", "valor_num": "Valor"}
    )
    df_extrato["Valor"] = df_extrato["Valor"].apply(fmt_moeda)
    st.dataframe(df_extrato.set_index("id"), use_container_width=True)
  else:
    st.info(
        "Nenhum aporte registrado ainda. Utilize a aba '➕ Novo Lançamento'"
        " para cadastrar."
    )

elif menu == "⚠️ Raio-X de Dívidas":
  st.title("⚠️ Raio-X de Dívidas Ativas")
  if not df_dividas.empty:
    st.dataframe(df_dividas.set_index("id"), use_container_width=True)
  else:
    st.info("Nenhuma dívida cadastrada no momento.")

elif menu == "💡 Orientação & Investimentos":
  st.title("💡 Orientação e Estratégias de Investimento")
  st.write(
      "Aqui você encontra orientações para organizar suas finanças e fazer sua"
      " reserva de emergência render com segurança."
  )
