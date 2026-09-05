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

  col_v1, col_v2 = st.columns(2)
  with col_v1:
    valor_real = st.number_input(
        "Valor (R$ com casas decimais)", min_value=0.0, format="%.2f", value=0.0
    )

  with col_v2:
    # Checkbox para alternar facilmente se deseja usar a data de hoje de forma automática
    usar_data_hoje = st.checkbox("Usar data de hoje", value=True)

  if usar_data_hoje:
    data_selecionada = datetime.now()
  else:
    data_selecionada = st.date_input("Data do Lançamento", value=datetime.now())

  enviar = st.form_submit_button("Salvar Lançamento")

  if enviar:
    data_formatada = data_selecionada.strftime("%d/%m/%Y")
    
    # Validação inteligente: se preencheu valor em centavos mas esqueceu o real, podemos converter automaticamente
    valor_final = valor_real if valor_real > 0 else (valor_centavos / 100.0 if valor_centavos > 0 else 0.0)

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
