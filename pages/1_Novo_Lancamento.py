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

  # Campo de valor inteligente (digite os centavos direto, ex: 15050 vira 150.50)
  valor_centavos = st.number_input(
      "Valor (Digite o valor em centavos ou completo)",
      min_value=0,
      step=1,
      value=0,
      help=(
          "Digite o valor. Exemplo: Para R$ 150,50 digite 15050 ou use o valor"
          " real."
      ),
  )

  # Se o usuário preferir digitar com ponto/vírgula tradicional, podemos dar opção ou converter:
  # Vamos usar um campo de texto formatado ou número padrão melhorado:
  col_v1, col_v2 = st.columns(2)
  with col_v1:
    valor_real = st.number_input(
        "Valor (R$ com casas decimais)", min_value=0.0, format="%.2f", value=0.0
    )

  data_selecionada = st.date_input("Data do Lançamento", value=datetime.now())

  enviar = st.form_submit_button("Salvar Lançamento")

  if enviar:
    data_formatada = data_selecionada.strftime("%d/%m/%Y")
    if categoria and valor_real > 0:
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            """
                    INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                    VALUES (%s, %s, %s, %s, %s)
                """,
            (data_formatada, tipo, categoria, descricao, valor_real),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success("Lançamento salvo com sucesso no banco em nuvem!")
      except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("Preencha a categoria e um valor válido.")
