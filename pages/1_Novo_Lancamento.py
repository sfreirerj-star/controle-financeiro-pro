from datetime import datetime
import psycopg2
import streamlit as st

st.set_page_config(page_title="Novo Lançamento", page_icon="➕")

def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])

st.subheader("➕ Registrar Gasto ou Receita")

with st.form("form_lancamento", clear_on_submit=True):
  tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
  categoria = st.text_input(
      "Categoria (Ex: Alimentação, Moradia, Transporte, Cartão)"
  )
  descricao = st.text_input("Descrição / Estabelecimento")

  # Campo único de valor inteligente em centavos (ex: digite 12345 e ele calcula R$ 123,45)
  valor_centavos = st.number_input(
      "Valor (Digite os números sem vírgula, ex: 12345 para 123,45)",
      min_value=0,
      step=1,
      value=0,
      help=(
          "Digite o valor sem pontos ou vírgulas. "
          "Exemplo: Para R$ 150,50 digite 15050. Os dois últimos dígitos são os centavos."
      ),
  )

  # Mostra na hora o valor formatado para você conferir antes de salvar
  valor_final = valor_centavos / 100.0
  
  def fmt_moeda(v):
      return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  
  st.info(f"Valor a ser lançado: **{fmt_moeda(valor_final)}**")

  usar_data_hoje = st.checkbox("Usar data de hoje", value=True)

  if usar_data_hoje:
    data_selecionada = datetime.now()
  else:
    data_selecionada = st.date_input("Data do Lançamento", value=datetime.now())

  enviar = st.form_submit_button("Salvar Lançamento")

  if enviar:
    data_formatada = data_selenicada = data_selecionada.strftime("%d/%m/%Y")

    if categoria and valor_final > 0:
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
      except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("Preencha a categoria e um valor válido.")
