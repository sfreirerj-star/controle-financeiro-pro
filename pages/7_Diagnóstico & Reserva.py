import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Diagnóstico & Reserva - Painel do Marcelo",
    page_icon="🎯",
    layout="wide",
)
aplicar_estilo_moderno()

st.title("💰 Controle Financeiro — Painel do Marcelo")
st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")


def carregar_dados():
  try:
    db_url = st.secrets.get("DATABASE_URL")
    if not db_url:
      for k, v in st.secrets.items():
        if isinstance(v, str) and "postgresql://" in v:
          db_url = v
          break

    if not db_url:
      st.error("⚠️ URL do banco não encontrada nos secrets.")
      return (
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
      )

    conn = psycopg2.connect(db_url)
    df_l = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
    df_d = pd.read_sql("SELECT * FROM dividas;", con=conn)

    try:
      df_a = pd.read_sql(
          "SELECT id, data, valor, local_aplicacao FROM desafio_aportes;",
          con=conn,
      )
    except Exception:
      df_a = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

    try:
      df_r = pd.read_sql("SELECT * FROM desafio_resgates;", con=conn)
    except Exception:
      df_r = pd.DataFrame(columns=["id", "data", "valor", "motivo"])

    conn.close()
    return df_l, df_d, df_a, df_r
  except Exception as e:
    st.error(f"Erro ao conectar ao banco: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


df_lancamentos, df_dividas, df_aportes, df_resgates = carregar_dados()

# Filtro de Competência
st.sidebar.header("📅 Filtro de Competência")
comps = []
if not df_lancamentos.empty and "data" in df_lancamentos.columns:
  df_lancamentos["data_dt"] = pd.to_datetime(
      df_lancamentos["data"], errors="coerce", dayfirst=True
  )
  df_lancamentos["competencia"] = df_lancamentos["data_dt"].dt.strftime(
      "%m/%Y"
  )
  comps = sorted(
      df_lancamentos["competencia"].dropna().unique().tolist(),
      key=lambda c: f"{c.split('/')[1]}{c.split('/')[0]}",
  )

opcoes = ["Todos os Meses"] + comps
comp_sel = st.sidebar.selectbox("Mês de Referência", options=opcoes, index=0)

df_filtrado = (
    df_lancamentos[df_lancamentos["competencia"] == comp_sel]
    if comp_sel != "Todos os Meses" and not df_lancamentos.empty
    else df_lancamentos.copy()
)

if df_filtrado.empty:
  st.info(f"Nenhum lançamento encontrado para {comp_sel}.")
else:
  df_filtrado["valor"] = pd.to_numeric(
      df_filtrado["valor"], errors="coerce"
  ).fillna(0.0)
  rec_tot = df_filtrado[df_filtrado["tipo"].str.lower() == "receita"][
      "valor"
  ].sum()
  desp_tot = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"][
      "valor"
  ].sum()

  tot_ap = (
      pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0).sum()
      if not df_aportes.empty
      else 0.0
  )
  tot_res = (
      pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0).sum()
      if not df_resgates.empty
      else 0.0
  )
  reserva_liq = tot_ap - tot_res
  saldo_atual = rec_tot - desp_tot

  st.subheader(f"📊 Panorama Atual ({comp_sel})")
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Receita Atual", f"R$ {rec_tot:,.2f}")
  c2.metric("Despesa Atual", f"R$ {desp_tot:,.2f}")
  c3.metric(
      "Reserva Atual (Aportes)",
      f"R$ {reserva_liq:,.2f}",
      delta="Líquido Guardado 💙",
  )
  c4.metric(
      "Resultado Líquido Atual",
      f"R$ {saldo_atual:,.2f}",
      delta=(
          f"{(saldo_atual/rec_tot)*100:.1f}% da Receita"
          if rec_tot > 0
          else "0%"
      ),
      delta_color="normal" if saldo_atual >= 0 else "inverse",
  )

  st.divider()
  st.subheader("🚀 Simulador Estratégico: Cenário Dezembro em Diante")

  df_despesas = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]
  aluguel = (
      df_despesas[
          df_despesas["categoria"].str.contains("Aluguel", case=False, na=False)
      ]["valor"].sum()
      if not df_despesas.empty
      else 0.0
  )

  col1, col2 = st.columns(2)
  with col1:
    entregar = st.checkbox(
        f"Entregar imóvel alugado em Dezembro (Zera Aluguel R$ {aluguel:,.2f})",
        value=True,
    )
    proeis = st.checkbox(
        "Considerar valor extra do PROEIS (R$ 5.320,00)", value=True
    )
    val_proeis = 5320.0 if proeis else 0.0
    tot_eco = aluguel if entregar else 0.0
    nova_despesa = desp_tot - tot_eco
    novo_saldo = rec_tot - nova_despesa
    meta_reserva = (nova_despesa / 30) * 180

  with col2:
    st.metric(
        "Nova Despesa Mensal",
        f"R$ {nova_despesa:,.2f}",
        delta=f"- R$ {tot_eco:,.2f} (Aluguel Eliminado)",
        delta_color="inverse",
    )
    st.metric(
        "Novo Saldo Líquido Mensal",
        f"R$ {novo_saldo:,.2f}",
        delta="Folga real garantida!",
    )
    if proeis:
      st.success(
          f"💰 **PROEIS:** R$ {val_proeis:,.2f} injetados na reserva inicial."
      )

  if novo_saldo > 1.0:
    meses = max(0.0, meta_reserva - val_proeis - reserva_liq) / novo_saldo
    st.info(
        f"🎯 **Previsão:** Você atinge sua meta de reserva (R$"
        f" {meta_reserva:,.2f}) em aproximadamente **{meses:.1f} meses** após"
        " dezembro!"
    )

  st.divider()
  st.subheader("🔍 Mapeamento Detalhado de Saídas")
  if not df_despesas.empty:
    gargalos = (
        df_despesas.groupby("categoria")["valor"]
        .sum()
        .reset_index()
        .sort_values(by="valor", ascending=False)
    )
    gargalos["% do Total"] = (
        (gargalos["valor"] / desp_tot) * 100 if desp_tot > 0 else 0
    )
    st.dataframe(
        gargalos.style.format({"valor": "R$ {:,.2f}", "% do Total": "{:.1f}%"}),
        use_container_width=True,
    )