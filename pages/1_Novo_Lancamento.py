from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import configurar_sidebar_competencia, obter_conexao

st.set_page_config(
    page_title="Novo Lançamento - Marcelo", page_icon="📝", layout="wide"
)

# Inicializar tabela no banco se não existir
def garantir_tabelas():
  try:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL
            )
        """)
    conexao.commit()
    cursor.close()
    conexao.close()
  except Exception:
    pass

garantir_tabelas()

# 1. Chamar o filtro de competência na barra lateral
try:
  conexao_temp = obter_conexao()
  competencia_selecionada, ordem_selecionada = configurar_sidebar_competencia(
      conexao_temp, prefixo_key="novo_lancamento"
  )
  conexao_temp.close()
except Exception:
  competencia_selecionada = datetime.now().strftime("%m/%Y")

st.title("💰 Controle Financeiro — Painel do Marcelo")
st.subheader("📝 Novo Lançamento & Registro de Caixa")
st.write(
    "Registre as suas receitas e despesas do dia a dia com abatimento automático"
    " dos aportes de investimentos."
)

# Formulário organizado nas 3 colunas, com a sequência perfeita: Data, Tipo, Categoria, Descrição, Valor
with st.form("form_novo_lancamento", clear_on_submit=True):
  col1, col2, col3 = st.columns(3)

  with col1:
    data_lancamento = st.text_input(
        "Data do Lançamento (DD/MM/AAAA)",
        value=datetime.now().strftime("%d/%m/%Y"),
    )
    tipo = st.selectbox("Tipo", ["Despesa", "Receita"])

  with col2:
    categoria = st.text_input(
        "Categoria (Ex: Alimentação, Transporte...)", value=""
    )
    valor = st.number_input(
        "Valor (R$)", min_value=0.0, value=0.0, step=10.0, format="%.2f"
    )

  with col3:
    descricao = st.text_input("Descrição / Estabelecimento", value="")

  submitted = st.form_submit_button("Salvar Lançamento")
  if submitted:
    try:
      datetime.strptime(data_lancamento.strip(), "%d/%m/%Y")
      conexao = obter_conexao()
      cursor = conexao.cursor()
      cursor.execute(
          "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor)"
          " VALUES (%s, %s, %s, %s, %s)",
          (data_lancamento.strip(), tipo, categoria, descricao, valor),
      )
      conexao.commit()
      cursor.close()
      conexao.close()
      st.success("Lançamento salvo com sucesso!")
      st.rerun()
    except ValueError:
      st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
    except Exception as e:
      st.error(f"Erro ao salvar: {e}")

st.divider()

# Carregamento robusto dos dados (Lançamentos e Aportes)
df_lancamentos = pd.DataFrame(
    columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
)
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

try:
  conexao = obter_conexao()
  try:
    df_lancamentos = pd.read_sql_query(
        "SELECT * FROM lancamentos ORDER BY id DESC", conexao
    )
  except Exception:
    conexao.rollback()

  try:
    df_aportes = pd.read_sql_query(
        "SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao
    )
  except Exception:
    conexao.rollback()
  conexao.close()
except Exception as e:
  st.error(f"Erro ao carregar dados do banco: {e}")


def extrair_competencia(data_str):
  try:
    dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
      dt = pd.to_datetime(data_str, errors="coerce")
    if pd.notna(dt):
      return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
  except Exception:
    pass
  return "Indefinido", "9999-99"


# Tratamento e limpeza dos dados
if not df_lancamentos.empty and "data" in df_lancamentos.columns:
  res_lanc = df_lancamentos["data"].apply(extrair_competencia)
  df_lancamentos["competencia"] = [x[0] for x in res_lanc]
  df_lancamentos["valor_num"] = pd.to_numeric(
      df_lancamentos["valor"], errors="coerce"
  ).fillna(0.0)
  df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()
else:
  df_lancamentos["competencia"] = "Indefinido"
  df_lancamentos["tipo_clean"] = ""

# Filtrar lançamentos para a competência selecionada na barra lateral
if not df_lancamentos.empty:
  df_lanc_mes = df_lancamentos[
      df_lancamentos["competencia"] == competencia_selecionada
  ].copy()
else:
  df_lanc_mes = pd.DataFrame(columns=df_lancamentos.columns)

if not df_aportes.empty and "valor" in df_aportes.columns:
  df_aportes["valor_num"] = pd.to_numeric(
      df_aportes["valor"], errors="coerce"
  ).fillna(0.0)
  total_aportes = df_aportes["valor_num"].sum()
else:
  total_aportes = 0.0

total_receitas = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(
            ["receita", "crédito", "credito", "entrada"]
        )
    ]["valor_num"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

total_gastos = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
    ]["valor_num"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

# Saldo Real Atualizado para o mês selecionado
saldo_atual = total_receitas - total_gastos


def fmt_moeda(v):
  return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.subheader(
    f"📊 Resumo Consolidado de Créditos e Débitos ({competencia_selecionada})"
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Créditos", fmt_moeda(total_receitas))
c2.metric("Total Débitos", fmt_moeda(total_gastos))
c3.metric("Total em Aportes", fmt_moeda(total_aportes))

if saldo_atual >= 0:
  c4.metric(
      "Saldo do Mês", fmt_moeda(saldo_atual), delta="No Azul 💙"
  )
else:
  c4.metric(
      "Saldo do Mês",
      fmt_moeda(saldo_atual),
      delta="No Vermelho 🔴",
      delta_color="inverse",
  )

st.divider()

st.subheader(f"Histórico de Lançamentos ({competencia_selecionada})")
if not df_lanc_mes.empty:
  df_exibicao = df_lanc_mes.drop(
      columns=["tipo_clean", "valor_num", "competencia"], errors="ignore"
  )
  df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
  st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
  st.info("Nenhum lançamento registrado nesta competência.")
