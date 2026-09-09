import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Diagnóstico & Reserva", page_icon="🎯", layout="wide"
)

st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos, simula o impacto da transição de"
    " moradia em dezembro, a entrada do extra do PROEIS e traça a rota para"
    " construir sua reserva de segurança."
)


# Função flexível para buscar a URL do banco no secrets.toml
def carregar_dados():
  try:
    db_url = None
    if "DATABASE_URL" in st.secrets:
      db_url = st.secrets["DATABASE_URL"]
    elif "database_url" in st.secrets:
      db_url = st.secrets["database_url"]
    elif (
        "connections" in st.secrets
        and "postgresql" in st.secrets["connections"]
    ):
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
      return pd.DataFrame(), pd.DataFrame()

    conn = psycopg2.connect(db_url)
    df_lancamentos = pd.read_sql("SELECT * FROM lancamentos;", con=conn)
    df_dividas = pd.read_sql("SELECT * FROM dividas;", con=conn)
    conn.close()
    return df_lancamentos, df_dividas
  except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados na nuvem: {e}")
    return pd.DataFrame(), pd.DataFrame()


# Carregando os dados
df_lancamentos, df_dividas = carregar_dados()

if df_lancamentos.empty:
  st.info("Nenhum lançamento encontrado para gerar o diagnóstico no momento.")
else:
  # Tratamento de dados
  df_lancamentos["valor"] = pd.to_numeric(
      df_lancamentos["valor"], errors="coerce"
  ).fillna(0.0)

  receitas_total = df_lancamentos[
      df_lancamentos["tipo"].str.lower() == "receita"
  ]["valor"].sum()
  despesas_total = df_lancamentos[
      df_lancamentos["tipo"].str.lower() == "despesa"
  ]["valor"].sum()
  saldo_atual = receitas_total - despesas_total

  # Métricas Gerais Atuais
  st.subheader("📊 Panorama Atual (Com Aluguel)")
  col1, col2, col3 = st.columns(3)
  col1.metric("Receita Atual", f"R$ {receitas_total:,.2f}")
  col2.metric("Despesa Atual", f"R$ {despesas_total:,.2f}")
  col3.metric(
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

  # Identifica o valor exato do aluguel atual no banco para abater na simulação
  df_despesas = df_lancamentos[df_lancamentos["tipo"].str.lower() == "despesa"]
  aluguel_atual = 0.0
  if not df_despesas.empty:
    aluguel_match = df_despesas[
        df_despesas["categoria"].str.contains("Aluguel", case=False, na=False)
    ]
    if not aluguel_match.empty:
      aluguel_atual = aluguel_match["valor"].sum()

    condominio_match = df_despesas[
        df_despesas["categoria"].str.contains("Condomínio", case=False, na=False)
    ]
    condominio_atual = (
        condominio_match["valor"].sum() if not condominio_match.empty else 0.0
    )
  else:
    condominio_atual = 0.0

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
    meta_reserva_futura = (nova_despesa_total / 30) * 180  # 6 meses aproximados

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
        delta=f"Folga real garantida por mês!",
    )
    if incluir_proeis:
      st.success(
          f"💰 **Injeção PROEIS:** Os R$ {valor_proeis:,.2f} extras entram"
          f" direto como o **pontapé inicial absoluto** da sua reserva de"
          f" segurança!"
      )

  if novo_saldo_mensal > 0:
    meses_reserva = (
        (meta_reserva_futura - valor_proeis) / novo_saldo_mensal
        if (meta_reserva_futura - valor_proeis) > 0
        else 0
    )
    st.info(
        f"📈 **Previsão de Sucesso:** Com a economia do aluguel gerando R$"
        f" {novo_saldo_mensal:,.2f} livres por mês e aplicando o extra do"
        f" PROEIS logo no início, você atinge a sua meta completa de reserva de"
        f" segurança em cerca de **{max(1, meses_reserva):.1f} meses** após a"
        f" mudança!"
    )

  st.divider()

  # Mapeamento de Gargalos Clássico
  st.subheader("🔍 Mapeamento Detalhado de Saídas Atuais")
  if not df_despesas.empty:
    gargalos = (
        df_despesas.groupby("categoria")["valor"]
        .sum()
        .reset_index()
        .sort_values(by="valor", ascending=False)
    )
    gargalos["% do Total"] = (
        (gargalos["valor"] / despesas_total) * 100
        if despesas_total > 0
        else 0
    )

    st.dataframe(
        gargalos.style.format(
            {"valor": "R$ {:,.2f}", "% do Total": "{:.1f}%"}
        ),
        use_container_width=True,
    )

  st.divider()

  # Plano de Ação Estratégico
  st.subheader("🛡️ Plano Diretor de Transição Patrimonial")
  st.markdown(f"""
    1. **Foco na Data de Dezembro:** Mantenha a disciplina financeira atual até completar o prazo contratual do Quinto Andar. A própria inércia do contrato resolve o problema estrutural do aluguel sem multas rescisórias abusivas.
    2. **Blindagem do PROEIS (R$ {valor_proeis:,.2f}):** Quando esse valor for creditado, **não o misture com a conta corrente comum**. Destine-o imediatamente para uma aplicação de renda fixa com liquidez diária (criando a fundação da sua reserva).
    3. **Aproveitamento do Imóvel Próprio:** A mudança para o seu apartamento em dezembro converterá um custo perdido (aluguel a terceiros) em amortização ou permanência no seu próprio patrimônio, reduzindo drasticamente o escoamento de caixa.
    """)
