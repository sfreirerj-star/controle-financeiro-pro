from datetime import datetime
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Novo Lançamento & Aportes", page_icon="➕", layout="wide"
)


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def garantir_tabelas():
  try:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    # Tabela de lançamentos gerais
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
    # Tabela de aportes da reserva
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

st.subheader("➕ Central de Lançamentos & Aportes na Reserva")
st.write(
    "Registre suas despesas, receitas ou faça o aporte direto na sua reserva"
    " diversificada com praticidade."
)

with st.form("form_lancamento", clear_on_submit=True):
  tipo_operacao = st.selectbox(
      "Tipo de Operação",
      ["📉 Despesa", "📈 Receita", "🛡️ Aporte na Reserva / Investimento"],
  )

  st.markdown("---")

  # Campos dinâmicos conforme a escolha
  if "Reserva" in tipo_operacao:
    locais_disponiveis = [
        "Sofisa Direto (CDB 105% CDI)",
        "Banco Inter (CDB Liquidez Diária)",
        "Nubank (Caixinha / RDB 100% CDI)",
        "Tesouro Selic (Tesouro Direto)",
        "Banco XP / Rico (CDB ou LCI)",
        "Outro (Personalizado)",
    ]
    local_selecionado = st.selectbox(
        "🏦 Banco ou Corretora (Local da Aplicação)", locais_disponiveis
    )
    categoria = "Reserva Financeira"
    descricao = f"Aporte via CPROEIS - {local_selecionado}"
    tipo = "Reserva"
  else:
    tipo = "Despesa" if "Despesa" in tipo_operacao else "Receita"
    categoria = st.text_input(
        "Categoria (Ex: Alimentação, Moradia, Transporte, Cartão)"
    )
    descricao = st.text_input("Descrição / Estabelecimento")

  # Seu campo de valor inteligente original mantido com perfeição
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

  enviar = st.form_submit_button(
      "🚀 Salvar Lançamento / Aporte", use_container_width=True
  )

  if enviar:
    try:
      data_obj = datetime.strptime(data_texto.strip(), "%d/%m/%Y")
      data_formatada = data_obj.strftime("%d/%m/%Y")
      data_valida = True
    except ValueError:
      data_valida = False

    # Validação condicional: se for despesa/receita exige categoria, se for reserva usa a padrão
    tem_categoria = (
        True
        if "Reserva" in tipo_operacao
        else (bool(categoria.strip()) if categoria else False)
    )

    if valor_final > 0 and data_valida and tem_categoria:
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()

        if "Reserva" in tipo_operacao:
          cursor.execute(
              """
                INSERT INTO desafio_aportes (data, valor, local_aplicacao)
                VALUES (%s, %s, %s)
                """,
              (data_formatada, valor_final, local_selecionado),
          )
          conexao.commit()
          st.success(
              f"🛡️ Aporte de {fmt_moeda(valor_final)} guardado com sucesso"
              f" no(a) **{local_selecionado}**!"
          )
        else:
          cursor.execute(
              """
                INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)
                VALUES (%s, %s, %s, %s, %s)
                """,
              (data_formatada, tipo, categoria, descricao, valor_final),
          )
          conexao.commit()
          st.success(f"✅ {tipo} salva com sucesso no banco em nuvem!")

        cursor.close()
        conexao.close()
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao salvar: {e}")
    else:
      st.error(
          "Preencha a categoria, um valor válido e uma data correta no formato"
          " DD/MM/AAAA."
      )