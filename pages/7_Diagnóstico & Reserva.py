import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

# Configuração da Página e Estilo SaaS Moderno
st.set_page_config(
    page_title="Diagnóstico & Reserva - Painel do Marcelo",
    page_icon="🎯",
    layout="wide",
)
aplicar_estilo_moderno()

st.title("💰 Controle Financeiro — Painel do Marcelo")
st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos, simula o impacto da transição de"
    " moradia em dezembro, a entrada do extra do PROEIS e traça a rota para"
    " construir sua reserva de segurança."
)


# Função flexível para buscar a URL do banco e carregar os dados
def carregar_dados():
  try:
    db_url = None
    if "DATABASE_URL" in st.secrets:
      db_url = st.secrets["DATABASE_URL"]
    elif "database_url" in st.secrets:
      db_url = st.secrets["database_url"]
    elif "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
      db_url = st.secrets["connections"]["postgresql"]["url"]
    else:
      for key in st.secrets:
        if isinstance(st.secrets[key], str) and "postgresql://" in st.secrets[key]:
          db_url = st.secrets[key]
          break

    if not db_url:
      st.error(
          "⚠️ A chave de conexão com o banco não foi encontrada no arquivo"
          " `.streamlit/secrets.toml`."
      )
      return (
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
          pd.DataFrame(),
      )

    conn = psycopg2.connect(db_url)
    df_lancamentos = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
    df_dividas = pd.read_sql("SELECT * FROM dividas;", con=conn)

    try:
      df_aportes = pd.read_sql(
          "SELECT id, data, valor, local_aplicacao FROM desafio_aportes;",
          con=conn,
      )
    except Exception:
      try:
        df_aportes = pd.read_sql("SELECT * FROM aportes;", con=conn)
      except Exception:
        df_aportes = pd.DataFrame(
            columns=["id", "data", "valor", "local_aplicacao"]
        )

    try:
      df_resgates = pd.read_sql("SELECT * FROM desafio_resgates;", con=conn)
    except Exception:
      df_resgates = pd.DataFrame(columns=["id", "data", "valor", "motivo"])

    conn.close()
    return df_lancamentos, df_dividas, df_aportes, df_resgates
  except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados na nuvem: {e}")
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# Carregando os dados originais
df_lancamentos, df_dividas, df_aportes, df_resgates = carregar_dados()

# ==========================================================
# FILTRO DE COMPETÊNCIA DINÂMICO (APENAS MESES COM LANÇAMENTOS)
# ==========================================================
st.sidebar.header("📅 Filtro de Competência")

competencias_disponiveis = []

if not df_lancamentos.empty and "data" in df_lancamentos.columns:
  # Converte as datas com segurança
  df_lancamentos["data_dt"] = pd.to_datetime(
      df_lancamentos["data"], errors="coerce", dayfirst=True
  )
  mask = df_lancamentos["data_dt"].isna()
  if mask.any():
    df_lancamentos.loc[mask, "data_dt"] = pd.to_datetime(
        df_lancamentos.loc[mask, "data"], errors="coerce"
    )

  df_lancamentos["competencia"] = df_lancamentos["data_dt"].dt.strftime("%m/%Y")

  # Extrai apenas os meses reais presentes nos dados (filtrando nulos)
  comps_reais = df_lancamentos["competencia"].dropna().unique().tolist()


  # Ordena as competências cronologicamente (ex: 09/2026, 10/2026...)
  def ordenar_comp(c):
    try:
      m, a = c.split("/")
      return f"{a}{m}"
    except:
      return c


  competencias_disponiveis = sorted(comps_reais, key=ordenar_comp)

# Se houver meses reais, adiciona a opção "Todos os Meses" no topo
if competencias_disponiveis:
  opcoes_menu = ["Todos os Meses"] + competencias_disponiveis
else:
  opcoes_menu = ["Todos os Meses"]

# Menu Lateral Interativo
competencia_selecionada = st.sidebar.selectbox(
    "Mês de Referência", options=opcoes_menu, index=0
)

# Filtra a tabela baseada na escolha do mês real
if (
    competencia_selecionada != "Todos os Meses"
    and not df_lancamentos.empty
    and "competencia" in df_lancamentos.columns
):
  df_filtrado = df_lancamentos[
      df_lancamentos["competencia"] == competencia_selecionada
  ]
else:
  df_filtrado = df_lancamentos.copy()
# ==========================================================

if df_filtrado.empty:
  st.info(
      f"Nenhum lançamento encontrado para {competencia_selecionada}. Selecione"
      " 'Todos os Meses' no menu lateral."
  )
else:
  # Tratamento de dados usando o dataframe FILTRADO (df_filtrado)
  df_filtrado["valor"] = pd.to_numeric(
      df_filtrado["valor"], errors="coerce"
  ).fillna(0.0)

  receitas_total = df_filtrado[df_filtrado["tipo"].str.lower() == "receita"][
      "valor"
  ].sum()
  despesas_total = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"][
      "valor"
  ].sum()

  # Tratamento de aportes e resgates para a reserva de segurança atual
  total_aportes = 0.0
  if not df_aportes.empty and "valor" in df_aportes.columns:
    total_aportes = (
        pd.to_numeric(df_aportes["valor"], errors="coerce")
        .fillna(0.0)
        .sum()
    )

  total_resgates = 0.0
  if not df_resgates.empty and "valor" in df_resgates.columns:
    total_resgates = (
        pd.to_numeric(df_resgates["valor"], errors="coerce")
        .fillna(0.0)
        .sum()
    )

  # Reserva atual líquida descontando os resgates efetuados
  reserva_atual_liquida = total_aportes - total_resgates

  # Resultado líquido atual considerando receitas, despesas e aportes do mês
  saldo_atual = receitas_total - despesas_total

  # Métricas Gerais Atuais com 4 colunas
  st.subheader(f"📊 Panorama Atual ({competencia_selecionada})")
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Receita Atual", f"R$ {receitas_total:,.2f}")
  col2.metric("Despesa Atual", f"R$ {despesas_total:,.2f}")
  col3.metric(
      "Reserva Atual (Aportes)",
      f"R$ {reserva_atual_liquida:,.2f}",
      delta="Líquido Guardado 💙",
  )
  col4.metric(
      "Resultado Líquido Atual",
      f"R$ {saldo_atual:,.2f}",
      delta=(
          f"{(saldo_atual/receitas_total)*100:.1f}% da Receita"
          if receitas_total > 0
          else "0%"
      ),
      delta_color="normal" if saldo_atual >= 0 else "inverse",
  )

  st.divider()

  # ==========================================================
  # SIMULADOR DE TRANSIÇÃO (DEZEMBRO + PROEIS + CORTES)
  # ==========================================================
  st.subheader("🚀 Simulador Estratégico: Cenário Dezembro em Diante")
  st.markdown(
      "Simule o impacto da sua mudança para o apartamento próprio (eliminando"
      " o aluguel) e a injeção do extra do PROEIS na formação da sua reserva."
  )

  df_despesas = df_filtrado[df_filtrado["tipo"].str.lower() == "despesa"]
  aluguel_atual = 0.0
  if not df_despesas.empty:
    aluguel_match = df_despesas[
        df_despesas["categoria"].str.contains("Aluguel", case=False, na=False)
    ]
    if not aluguel_match.empty:
      aluguel_atual = aluguel_match["valor"].sum()

  col_tr1, col_tr2 = st.columns(2)

  with col_tr1:
    st.markdown("#### Premissas da Virada")
    entregar_aluguel = st.checkbox(
        "Entregar imóvel alugado em Dezembro (Zera o Aluguel de R$"
        f" {aluguel_atual:,.2f})",
        value=True,
    )
    incluir_proeis = st.checkbox(
        "Considerar valor extra do PROEIS (R$ 5.320,00)", value=True
    )

    valor_proeis = 5320.0 if incluir_proeis else 0.0
    economia_aluguel = aluguel_atual if entregar_aluguel else 0.0

    nova_despesa_total = despesas_total - economia_aluguel
    novo_saldo_mensal = receitas_total - nova_despesa_total
    meta_reserva_futura = (
        nova_despesa_total / 30
    ) * 180  # Meta de 6 meses das novas despesas

  with col_tr2:
    st.markdown("#### 🎯 Projeção de Caixa (A partir de Dezembro)")
    st.metric(
        "Nova Despesa Mensal",
        f"R$ {nova_despesa_total:,.2f}",
        delta=f"- R$ {economia_aluguel:,.2f} (Aluguel Eliminado)",
        delta_color="inverse",
    )
    st.metric(
        "Novo Saldo Líquido Mensal",
        f"R$ {novo_saldo_mensal:,.2f}",
        delta="Folga real garantida por mês!",
    )
    if incluir_proeis:
      st.success(
          f"💰 **Injeção PROEIS:** Os R$ {valor_proeis:,.2f} extras entram"
          " direto como o **pontapé inicial absoluto** da sua reserva de"
          " segurança!"
      )

  if novo_saldo_mensal > 1.0