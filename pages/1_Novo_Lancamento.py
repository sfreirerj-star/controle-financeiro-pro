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

  # Campo de texto livre para o valor (começa totalmente vazio)
  valor_texto = st.text_input(
      "Valor (Ex: digite 12 para 12,00 ou 1250 para 12,50)",
      value="",
      placeholder="Ex: 12 ou 15050"
  )

  # Lógica inteligente para converter o texto digitado em valor real
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
      return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

  if valor_final > 0:
      st.info(f"Valor a ser lançado: **{fmt_moeda(valor_final)}**")

  usar_data_hoje = st.checkbox("Usar data de hoje", value=True)

  if usar_data_hoje:
    data_selecionada = datetime.now()
    st.write(f"Data do lançamento: **{data_selecionada.strftime('%d/%m/%Y')}** (Hoje)")
  else:
    # Se desmarcar, abrimos o seletor e mostramos logo abaixo o formato formatado DD/MM/AAAA
    data_selecionada = st.date_input("Selecione a Data do Lançamento", value=datetime.now())
    st.write(f"Data escolhida: **{data_selecionada.strftime('%d/%m/%Y')}**")

  enviar = st.form_submit_button("Salvar Lançamento")

  if enviar:
    data_formatada = data_selecionada.strftime("%d/%m/%Y")

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
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("Preencha a categoria e um valor válido.")
