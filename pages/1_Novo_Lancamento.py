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

  # Campo de valor inteligente (vazio, digite direto os números)
  valor_texto = st.text_input(
      "Valor (Ex: digite 12 para 12,00 ou 1250 para 12,50)",
      value="",
      placeholder="Ex: 12 ou 15050"
  )

  # Conversão do valor
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

  # Campo de data limpo e direto: já vem com a data de hoje, mas é totalmente editável para passado ou futuro
  data_hoje_str = datetime.now().strftime("%d/%m/%Y")
  data_texto = st.text_input(
      "Data do Lançamento (DD/MM/AAAA)",
      value=data_hoje_str,
      placeholder="Ex: 05/09/2026"
  )

  enviar = st.form_submit_button("Salvar Lançamento")

  if enviar:
    # Valida e converte a data digitada pelo usuário
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
        st.error("Preencha a categoria, um valor válido e uma data correta no formato DD/MM/AAAA.")
