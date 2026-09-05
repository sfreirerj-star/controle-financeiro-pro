import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Raio-X de Dívidas", page_icon="⚠️")


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


st.subheader("⚠️ Gerenciar Dívidas e Juros")

with st.form("form_divida", clear_on_submit=True):
  credor = st.text_input("Credor / Nome da Dívida (Ex: Cartão de Crédito)")
  valor_total = st.number_input(
      "Valor Total Devido (R$)", min_value=0.0, format="%.2f"
  )
  juros_mensal = st.number_input(
      "Taxa de Juros Mensal (%)", min_value=0.0, format="%.2f"
  )

  salvar_divida = st.form_submit_button("Cadastrar Dívida")

  if salvar_divida:
    if credor and valor_total > 0:
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            """
                    INSERT INTO dividas (credor, valor_total, juros_mensal, status)
                    VALUES (%s, %s, %s, %s)
                """,
            (credor, valor_total, juros_mensal, "Pendente"),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success("Dívida cadastrada com sucesso!")
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao salvar dívida: {e}")
    else:
      st.error("Preencha o credor e o valor total.")

try:
  conexao = obter_conexao()
  df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
  conexao.close()
except Exception:
  df_dividas = pd.DataFrame()

if not df_dividas.empty:
  st.write("### Suas Dívidas Ativas")
  st.dataframe(df_dividas, use_container_width=True)
else:
  st.info("Nenhuma dívida cadastrada no momento.")
