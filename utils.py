from datetime import datetime
import pandas as pd
import streamlit as st


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


def configurar_sidebar_competencia(
    conexao, prefixo_key="global"
) -> tuple[str, str]:
  """Lê as tabelas do banco, extrai as competências disponíveis,

  renderiza o seletor na barra lateral e retorna (competencia_selecionada, comp_ordem).
  """
  try:
    df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
    try:
      df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
    except Exception:
      df_a = pd.DataFrame(columns=["data"])
  except Exception:
    df_l = pd.DataFrame(columns=["data"])
    df_a = pd.DataFrame(columns=["data"])

  for df in [df_l, df_a]:
    if not df.empty and "data" in df.columns:
      res = df["data"].apply(extrair_competencia)
      df["competencia"] = [x[0] for x in res]
      df["comp_ordem"] = [x[1] for x in res]
    else:
      df["competencia"] = "Indefinido"
      df["comp_ordem"] = "9999-99"

  mapeamento_comps = pd.concat([
      df_l[["competencia", "comp_ordem"]],
      df_a[["competencia", "comp_ordem"]],
  ]).drop_duplicates()

  mapeamento_comps = mapeamento_comps[
      mapeamento_comps["competencia"] != "Indefinido"
  ].sort_values("comp_ordem", ascending=False)

  competencias_disponiveis = mapeamento_comps["competencia"].tolist()
  mes_atual_sistema = datetime.now().strftime("%m/%Y")

  if not competencias_disponiveis:
    competencias_disponiveis = [mes_atual_sistema]

  key_selectbox = f"selectbox_competencia_{prefixo_key}"

  if key_selectbox not in st.session_state:
    st.session_state[key_selectbox] = (
        mes_atual_sistema
        if mes_atual_sistema in competencias_disponiveis
        else competencias_disponiveis[0]
    )

  try:
    index_atual = competencias_disponiveis.index(st.session_state[key_selectbox])
  except ValueError:
    index_atual = 0

  st.sidebar.header("📅 Competência (Mês/Ano)")
  competencia_selecionada = st.sidebar.selectbox(
      "Selecione o Mês de Referência",
      options=competencias_disponiveis,
      index=index_atual,
      key=key_selectbox,
  )

  ordem_sel = (
      mapeamento_comps[
          mapeamento_comps["competencia"] == competencia_selecionada
      ]["comp_ordem"].values[0]
      if competencia_selecionada in mapeamento_comps["competencia"].values
      else datetime.now().strftime("%Y-%m")
  )

  return competencia_selecionada, ordem_sel
