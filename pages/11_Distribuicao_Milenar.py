from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(
    page_title="Alocação Milenar - Talmude", page_icon="📜", layout="wide"
)
aplicar_estilo_moderno()  # <-- Mantém o menu opaco e padronizado


def obter_conexao():
  """Abre e retorna a conexão com o banco de dados PostgreSQL na nuvem."""
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def extrair_competencia(data_val):
  if pd.isna(data_val) or data_val is None:
    return "Indefinido", "9999-99"
  try:
    if isinstance(data_val, (pd.Timestamp, datetime)):
      return data_val.strftime("%m/%Y"), data_val.strftime("%Y-%m")
    data_str = str(data_val).strip()
    dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
      dt = pd.to_datetime(data_str, errors="coerce")
    if pd.notna(dt):
      return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
  except Exception:
    pass
  return "Indefinido", "9999-99"


def configurar_sidebar_competencia(conexao, prefixo_key="milenar"):
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
      if not mapeamento_comps.empty
      and competencia_selecionada in mapeamento_comps["competencia"].values
      else datetime.now().strftime("%Y-%m")
  )

  return competencia_selecionada, ordem_sel


# Carregando a competência selecionada na sidebar
try:
  conn_temp = obter_conexao()
  competencia_alvo, ordem_alvo = configurar_sidebar_competencia(
      conn_temp, prefixo_key="milenar"
  )
  conn_temp.close()
except Exception:
  competencia_alvo = datetime.now().strftime("%m/%Y")


st.title("📜 Estratégia de Alocação Milenar (Talmude)")
st.markdown(
    "Aplicação prática dos conceitos de **Tsedacá** e da **Regra dos Três"
    f" Terços** usando seus dados reais na nuvem (Competência: **{competencia_alvo}**)."
)

# --- SEÇÃO EDUCATIVA E CONCEITUAL ---
with st.expander(
    "📖 Clique aqui para entender a Origem e a Filosofia da Riqueza Milenar",
    expanded=False,
):
  st.markdown("""
        ### A Regra dos Três Terços do Talmude
        Para aprofundar seus conhecimentos, o ponto de partida ideal é a **Regra dos Três Terços do Talmude**, uma das diretrizes financeiras mais antigas e eficazes do mundo sobre gestão e diversificação de patrimônio.
        Há mais de 1.500 anos, o tratado **Baba Metzia (42a)** determinou a seguinte estratégia de alocação de recursos:
        > *"Uma pessoa deve sempre dividir seu dinheiro em três partes: um terço em terras, um terço em negócios e um terço mantido em mãos."*

        ---

        ### A Estrutura Prática dos Três Terços
        Traduzindo esse ensinamento milenar para o cenário financeiro e econômico moderno, a divisão funciona da seguinte forma:

        * **1/3 em Terras (Segurança)**
          * *Conceito antigo:* Propriedades rurais e imóveis.
          * *Aplicação moderna:* Investimentos de base sólida, real e menos voláteis. Inclui bens imobiliários (físicos ou Fundos Imobiliários - FIIs), terras agrícolas e ativos de infraestrutura. O objetivo é a preservação de capital e proteção contra a inflação.
        * **1/3 em Negócios (Crescimento)**
          * *Conceito antigo:* Mercadorias, comércio e frotas de transporte.
          * *Aplicação moderna:* Investimentos de risco e potencial de multiplicação. Inclui empreendedorismo (negócio próprio), ações de empresas na bolsa de valores e investimentos em inovação. O objetivo é gerar verdadeira riqueza através do crescimento e dos lucros.
        * **1/3 em Mãos (Liquidez e Oportunidade)**
          * *Conceito antigo:* Moedas de ouro ou prata guardadas em casa.
          * *Aplicação moderna:* Dinheiro de fácil acesso, reservas de emergência e ativos de altíssima liquidez (como Tesouro Selic ou CDBs com liquidez diária). O objetivo é garantir a sobrevivência em crises e ter poder de compra imediato quando ótimas oportunidades de negócio surgirem com preços descontados.

        ---

        ### O Conceito de Tsedacá (Justiça Social)
        Ao contrário da palavra "caridade" (que remete ao sentimento de pena), **Tsedacá** tem origem na raiz hebraica *Tsedek*, que significa **justiça ou retidão**.
        * **A Mentalidade de Canal:** O dinheiro não pertence totalmente a quem o ganha; o indivíduo é um "administrador" ou canal de recursos. Se você retém tudo, o fluxo bloqueia. Se faz o dinheiro circular ajudando a comunidade e apoiando projetos, mais recursos são direcionados a você.
        * **A Regra dos 10% a 20%:** Destinar uma parte dos ganhos para apoiar o próximo ou capacitar profissionais não é um ato opcional, mas uma obrigação de fazer o que é justo.
    """)

st.divider()


# --- CONSULTA AO POSTGRESQL PARA A COMPETÊNCIA SELECIONADA ---
def buscar_dados_competencia(competencia):
  entradas = 0.0
  gastos_comuns = 0.0

  try:
    conn = obter_conexao()
    df_l = pd.read_sql_query("SELECT * FROM lancamentos", conn)
    conn.close()

    if not df_l.empty and "data" in df_l.columns:
      res_comp = df_l["data"].apply(extrair_competencia)
      df_l["competencia"] = [x[0] for x in res_comp]
      df_l["valor_num"] = pd.to_numeric(
          df_l["valor"], errors="coerce"
      ).fillna(0.0)
      df_l["tipo_clean"] = df_l["tipo"].str.strip().str.lower()

      df_mes = df_l[df_l["competencia"] == competencia]

      if not df_mes.empty:
        entradas = df_mes[
            df_mes["tipo_clean"].isin(
                ["receita", "crédito", "credito", "entrada"]
            )
        ]["valor_num"].sum()
        gastos_comuns = df_mes[
            df_mes["tipo_clean"].isin(
                ["despesa", "débito", "debito", "saida"]
            )
        ]["valor_num"].sum()

  except Exception as e:
    st.sidebar.error(f"Erro ao carregar dados do banco: {e}")

  return entradas, gastos_comuns


entradas, gastos_comuns = buscar_dados_competencia(competencia_alvo)
saldo_remanescente = entradas - gastos_comuns

# Painel de métricas do sistema
st.markdown(f"### 📱 Resumo da Competência: {competencia_alvo}")
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric(
    "Entradas",
    f"R$ {entradas:,.2f}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
)
col_m2.metric(
    "Gastos Comuns",
    f"R$ {gastos_comuns:,.2f}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
)
col_m3.metric(
    "Saldo Livre",
    f"R$ {saldo_remanescente:,.2f}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
    delta="No Azul 💙" if saldo_remanescente >= 0 else "No Vermelho 🔴",
)

st.divider()

if saldo_remanescente > 0:
  # --- MATEMÁTICA MILENAR APLICADA AOS SEUS DADOS ---
  tsedaca = saldo_remanescente * 0.10
  saldo_investivel = saldo_remanescente - tsedaca
  um_terco = saldo_investivel / 3

  # --- RENDERIZAÇÃO DA INTERFACE ---
  st.warning(
      "🕊️ **Tsedacá (Justiça Social - 10%): R$"
      f" {tsedaca:,.2f}**".replace(",", "X")
      .replace(".", ",")
      .replace("X", ".")
  )
  st.caption(
      "Destine este valor para fazer o bem, apoiar projetos sociais ou ajudar"
      " na capacitação profissional de terceiros."
  )

  st.write("")
  st.markdown("### 🎯 Divisão Estratégica dos Três Terços (Talmude)")

  col1, col2, col3 = st.columns(3)

  with col1:
    st.info("🛡️ **1/3 em Terras**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Segurança e Preservação\n\n*Sugestão:* Fundos Imobiliários"
        " de Tijolo, Imóveis ou Renda Fixa IPCA+."
    )

  with col2:
    st.success("📈 **1/3 em Negócios**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Multiplicação e Crescimento\n\n*Sugestão:* Ações, novos"
        " projetos geradores de receita ou capacitação pessoal."
    )

  with col3:
    st.error("💰 **1/3 em Mãos**")
    st.subheader(
        f"R$ {um_terco:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    st.markdown(
        "**Foco:** Liquidez e Oportunidade\n\n*Sugestão:* Tesouro Selic ou CDB"
        " 100% CDI com liquidez diária."
    )

  # Elemento Gráfico Complementar
  st.write("")
  st.markdown("### 📊 Visão Geral do Repasse")
  df_grafico = pd.DataFrame({
      "Destino": [
          "Tsedacá",
          "Terras (Segurança)",
          "Negócios (Crescimento)",
          "Em Mãos (Liquidez)",
      ],
      "Valores": [tsedaca, um_terco, um_terco, um_terco],
  })
  st.bar_chart(data=df_grafico, x="Destino", y="Valores")

else:
  st.error(
      "O saldo remanescente em conta precisa ser positivo para aplicar o"
      " modelo milenar de investimentos."
  )