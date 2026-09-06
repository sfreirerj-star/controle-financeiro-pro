from datetime import datetime
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

# Abas para separar com perfeição o dia a dia do investimento
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

    # Seu campo de valor inteligente original
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


    def fmt_moeda(v):
      return (
          f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
      )


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

# --- ABA 2: APORTE NA RESERVA (LAYOUT IDÊNTICO AO DESAFIO) ---
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