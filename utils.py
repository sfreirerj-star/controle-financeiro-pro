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
  mes_atual_sistema = datetime.now().strftime("%m/%Y")
  competencias_disponiveis = [mes_atual_sistema]
  mapeamento_comps = pd.DataFrame(
      {
          "competencia": [mes_atual_sistema],
          "comp_ordem": [datetime.now().strftime("%Y-%m")],
      }
  )

  try:
    df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
  except Exception:
    df_l = pd.DataFrame(columns=["data"])

  try:
    df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
  except Exception:
    df_a = pd.DataFrame(columns=["data"])

  for df in [df_l, df_a]:
    if not df.empty and "data" in df.columns:
      res = df["data"].apply(extrair_competencia)
      df["competencia"] = [x[0] for x in res]
      df["comp_ordem"] = [x[1] for x in res]

  if not df_l.empty or not df_a.empty:
    mapeamento_comps = pd.concat([
        df_l[["competencia", "comp_ordem"]]
        if not df_l.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
        df_a[["competencia", "comp_ordem"]]
        if not df_a.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
    ]).drop_duplicates()

    mapeamento_comps = mapeamento_comps[
        mapeamento_comps["competencia"] != "Indefinido"
    ].sort_values("comp_ordem", ascending=False)

    if not mapeamento_comps.empty:
      competencias_disponiveis = mapeamento_comps["competencia"].tolist()

  if mes_atual_sistema not in competencias_disponiveis:
    competencias_disponiveis.insert(0, mes_atual_sistema)

  key_selectbox = f"selectbox_competencia_{prefixo_key}"

  if key_selectbox not in st.session_state:
    st.session_state[key_selectbox] = mes_atual_sistema

  try:
    index_atual = competencias_disponiveis.index(st.session_state[key_selectbox])
  except ValueError:
    index_atual = 0

  st.sidebar.markdown("---")
  st.sidebar.header("📅 Filtro de Competência")
  competencia_selecionada = st.sidebar.selectbox(
      "Selecione o Mês/Ano de Referência",
      options=competencias_disponiveis,
      index=index_atual,
      key=key_selectbox,
  )

  ordem_sel = (
      mapeamento_comps[
          mapeamento_comps["competencia"] == competencia_selecionada
      ]["comp_ordem"].values[0]
      if not mapeamento_comps.empty
      and competencia_selecionada in mapeamento_comps["competencia"].values
      else datetime.now().strftime("%Y-%m")
  )

  return competencia_selecionada, ordem_sel
