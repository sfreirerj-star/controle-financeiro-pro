from datetime import datetime
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro - Marcelo", page_icon="💰", layout="wide"
)


def obter_conexao():
  """Retorna a conexão com a base de dados PostgreSQL centralizada nos secrets."""
  return psycopg2.connect(st.secrets["DATABASE_URL"])


# Inicialização segura dos DataFrames
df_lancamentos = pd.DataFrame(
    columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
)
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])
df_dividas = pd.DataFrame(
    columns=["id", "credor", "valor_total", "juros_mensal", "status"]
)

# Carregamento robusto direto das tabelas oficiais do projeto
try:
  conexao = obter_conexao()

  # 1. Carregar Lançamentos (Entradas e Gastos Comuns)
  try:
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
  except Exception:
    conexao.rollback()

  # 2. Carregar Aportes da tabela correta do Desafio de Reserva
  try:
    df_aportes = pd.read_sql_query(
        "SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao
    )
  except Exception:
    conexao.rollback()

  # 3. Carregar Dívidas
  try:
    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
  except Exception:
    conexao.rollback()

  conexao.close()
except Exception as e:
  st.sidebar.error(f"Erro geral de conexão com o banco: {e}")

# Tratamento e soma segura dos aportes
if not df_aportes.empty and "valor" in df_aportes.columns:
  df_aportes["valor_num"] = (
      pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
  )
  total_aportes_geral = df_aportes["valor_num"].sum()
else:
  total_aportes_geral = 0.0


def fmt_moeda(valor):
  return (
      f"R$ {valor:,.2f}".replace(",", "X")
      .replace(".", ",")
      .replace("X", ".")
  )


# --- PROCESSAMENTO DE COMPETÊNCIAS (MÊS/ANO) ---
def extrair_mes_ano(data_str):
  """Extrai o formato AAAA-MM de uma string de data (DD/MM/AAAA ou similar)."""
  try:
    dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
      dt = pd.to_datetime(data_str, errors="coerce")
    if pd.notna(dt):
      return dt.strftime("%Y-%m")
  except Exception:
    pass
  return "Indefinido"


if not df_lancamentos.empty and "data" in df_lancamentos.columns:
  df_lancamentos["competencia"] = df_lancamentos["data"].apply(extrair_mes_ano)
else:
  df_lancamentos["competencia"] = "Indefinido"

if not df_aportes.empty and "data" in df_aportes.columns:
  df_aportes["competencia"] = df_aportes["data"].apply(extrair_mes_ano)
else:
  df_aportes["competencia"] = "Indefinido"

# Obter lista de competências disponíveis ordenadas
competencias_disponiveis = sorted(
    [c for c in df_lancamentos["competencia"].unique() if c != "Indefinido"],
    reverse=True,
)
mes_atual_sistema = datetime.now().strftime("%Y-%m")
if not competencias_disponiveis:
  competencias_disponiveis = [mes_atual_sistema]

# --- BARRA LATERAL: SELETOR DE COMPETÊNCIA ---
st.sidebar.header("📅 Competência (Mês/Ano)")
competencia_selecionada = st.sidebar.selectbox(
    "Selecione o Mês de Referência",
    options=competencias_disponiveis,
    index=0
    if mes_atual_sistema in competencias_disponiveis
    else len(competencias_disponiveis) - 1,
)

# --- CORPO DA PÁGINA PRINCIPAL (PAINEL & GRÁFICOS) ---
st.title("💰 Controle Financeiro — Painel do Marcelo")
st.write(
    "Aplicativo unificado de controle de créditos, débitos e investimentos"
    f" (Competência: **{competencia_selecionada}**)."
)

# Tratamento flexível para capturar receitas e despesas de lançamentos
if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
  df_lancamentos["valor"] = (
      pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
  )
  df_lancamentos["tipo_clean"] = (
      df_lancamentos["tipo"].str.strip().str.lower()
  )
else:
  df_lancamentos["tipo_clean"] = ""

# Filtrar lançamentos do mês selecionado
df_lanc_mes = (
    df_lancamentos[
        df_lancamentos["competencia"] == competencia_selecionada
    ].copy()
    if not df_lancamentos.empty
    else pd.DataFrame()
)

total_receitas_mes = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(
            ["receita", "crédito", "credito", "entrada"]
        )
    ]["valor"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

total_gastos_mes = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
    ]["valor"].sum()
    if not df_lanc_mes.empty
    else 0.0
)

# Aportes específicos do mês selecionado
df_aportes_mes = (
    df_aportes[df_aportes["competencia"] == competencia_selecionada].copy()
    if not df_aportes.empty
    else pd.DataFrame()
)
total_aportes_mes = (
    df_aportes_mes["valor_num"].sum() if not df_aportes_mes.empty else 0.0
)


# --- CÁLCULO INTELIGENTE DE SALDO REMANESCENTE ACUMULADO ---
def calcular_saldo_ate_competencia(df_lan, df_ap, comp_alvo):
  """Calcula o saldo acumulado de todas as competências anteriores à selecionada."""
  try:
    comps = sorted(
        [c for c in df_lan["competencia"].unique() if c != "Indefinido"]
    )
    saldo_acumulado = 0.0
    for c in comps:
      if c < comp_alvo:
        rec = df_lan[
            (df_lan["competencia"] == c)
            & (
                df_lan["tipo_clean"].isin(
                    ["receita", "crédito", "credito", "entrada"]
                )
            )
        ]["valor"].sum()
        gas = df_lan[
            (df_lan["competencia"] == c)
            & (
                df_lan["tipo_clean"].isin(
                    ["despesa", "débito", "debito", "saida"]
                )
            )
        ]["valor"].sum()
        apo = (
            df_ap[df_ap["competencia"] == c]["valor_num"].sum()
            if not df_ap.empty
            else 0.0
        )
        saldo_acumulado += rec - gas - apo
    return saldo_acumulado
  except Exception:
    return 0.0


saldo_remanescente_anterior = calcular_saldo_ate_competencia(
    df_lancamentos, df_aportes, competencia_selecionada
)

# Saldo Atual do Mês = Saldo Anterior + Receitas do Mês - Gastos do Mês - Aportes do Mês
saldo_mes = (
    saldo_remanescente_anterior
    + total_receitas_mes
    - total_gastos_mes
    - total_aportes_mes
)

st.subheader(
    f"Resumo da Competência: {competencia_selecionada} e Visualização Gráfica"
)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Saldo Anterior", fmt_moeda(saldo_remanescente_anterior))
col2.metric("Entradas", fmt_moeda(total_receitas_mes))
col3.metric("Gastos Comuns", fmt_moeda(total_gastos_mes))
col4.metric("Aportes do Mês", fmt_moeda(total_aportes_mes))

if saldo_mes >= 0:
  col5.metric(
      "Saldo Final / Remanescente", fmt_moeda(saldo_mes), delta="No Azul 💙"
  )
else:
  col5.metric(
      "Saldo Final / Remanescente",
      fmt_moeda(saldo_mes),
      delta="No Vermelho 🔴",
      delta_color="inverse",
  )

st.divider()

st.subheader(
    "Distribuição de Gastos e Investimentos (Visão da Competência Selecionada)"
)

df_gastos_grafico = (
    df_lanc_mes[
        df_lanc_mes["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])
    ].copy()
    if not df_lanc_mes.empty
    else pd.DataFrame()
)

# Integrando os aportes do mês como fatias de investimento nos gráficos globais
if not df_aportes_mes.empty:
  df_ap_graf = pd.DataFrame()
  df_ap_graf["categoria"] = ["Investimento / Aporte"] * len(df_aportes_mes)
  df_ap_graf["valor"] = df_aportes_mes["valor_num"]
  df_gastos_grafico = pd.concat(
      [df_gastos_grafico, df_ap_graf], ignore_index=True
  )

if not df_gastos_grafico.empty and "valor" in df_gastos_grafico.columns:
  df_cat = df_gastos_grafico.groupby("categoria")["valor"].sum().reset_index()

  col_g1, col_g2 = st.columns(2)

  with col_g1:
    st.markdown("**Gráfico de Pizza**")
    fig_pizza = px.pie(
        df_cat,
        names="categoria",
        values="valor",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_pizza.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pizza, use_container_width=True)

  with col_g2:
    st.markdown("**Gráfico de Barras**")
    fig_barras = px.bar(
        df_cat,
        x="categoria",
        y="valor",
        text="valor",
        color="categoria",
        labels={"categoria": "Categoria", "valor": "Valor (R$)"},
    )
    fig_barras.update_traces(
        texttemplate="R$ %{text:.2f}", textposition="outside"
    )
    fig_barras.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_barras, use_container_width=True)
else:
  st.info("Nenhum registro encontrado para gerar gráficos nesta competência.")

st.divider()
st.subheader(
    f"Histórico de Lançamentos da Competência: {competencia_selecionada}"
)
if not df_lanc_mes.empty and "id" in df_lanc_mes.columns:
  df_exibicao = df_lanc_mes.copy()
  if "tipo_clean" in df_exibicao.columns:
    df_exibicao = df_exibicao.drop(columns=["tipo_clean"])
  if "competencia" in df_exibicao.columns:
    df_exibicao = df_exibicao.drop(columns=["competencia"])
  df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
  st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
  st.info("Nenhum lançamento encontrado para esta competência.")

# --- SEÇÃO DE BALANCETE COMPARATIVO MÊS A MÊS ---
st.divider()
st.subheader("📊 Balancete Comparativo Mensal (Evolução Contábil)")

competencias_todas = sorted(
    list(
        set(
            [c for c in df_lancamentos["competencia"].unique() if c != "Indefinido"]
            + [c for c in df_aportes["competencia"].unique() if c != "Indefinido"]
        )
    )
)

if competencias_todas:
  dados_balancete = []
  acum_saldo_loop = 0.0

  for comp in competencias_todas:
    rec_c = (
        df_lancamentos[
            (df_lancamentos["competencia"] == comp)
            & (
                df_lancamentos["tipo_clean"].isin(
                    ["receita", "crédito", "credito", "entrada"]
                )
            )
        ]["valor"].sum()
        if not df_lancamentos.empty
        else 0.0
    )

    gas_c = (
        df_lancamentos[
            (df_lancamentos["competencia"] == comp)
            & (
                df_lancamentos["tipo_clean"].isin(
                    ["despesa", "débito", "debito", "saida"]
                )
            )
        ]["valor"].sum()
        if not df_lancamentos.empty
        else 0.0
    )

    apo_c = (
        df_aportes[df_aportes["competencia"] == comp]["valor_num"].sum()
        if not df_aportes.empty
        else 0.0
    )

    saldo_final_c = acum_saldo_loop + rec_c - gas_c - apo_c

    dados_balancete.append({
        "Competência": comp,
        "Saldo Anterior": acum_saldo_loop,
        "Entradas": rec_c,
        "Gastos Comuns": gas_c,
        "Aportes": apo_c,
        "Saldo Final": saldo_final_c,
    })
    acum_saldo_loop = saldo_final_c

  df_resumo_mensal = pd.DataFrame(dados_balancete)

  # Formatar colunas para exibição em moeda
  df_resumo_formatado = df_resumo_mensal.copy()
  for col in [
      "Saldo Anterior",
      "Entradas",
      "Gastos Comuns",
      "Aportes",
      "Saldo Final",
  ]:
    df_resumo_formatado[col] = df_resumo_formatado[col].apply(fmt_moeda)

  st.dataframe(df_resumo_formatado, use_container_width=True)
else:
  st.info(
      "Ainda não há dados suficientes para gerar o balancete comparativo mensal."
  )