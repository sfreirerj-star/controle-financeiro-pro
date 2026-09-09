import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Diagnóstico & Reserva", page_icon="🎯", layout="wide"
)

st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
st.markdown(
    "Esta aba analisa os seus lançamentos e dívidas para identificar onde sua"
    " renda está escoando, simular cortes estratégicos e traçar a rota ideal"
    " para construir sua reserva de segurança."
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

  # Métricas Gerais
  col1, col2, col3 = st.columns(3)
  col1.metric("Receita Acumulada", f"R$ {receitas_total:,.2f}")
  col2.metric("Despesa Acumulada", f"R$ {despesas_total:,.2f}")
  col3.metric(
      "Resultado Líquido",
      f"R$ {saldo_atual:,.2f}",
      delta=(
          f"{(saldo_atual/receitas_total)*100:.1f}% da Receita"
          if receitas_total > 0
          else "0%"
      ),
      delta_color="normal" if saldo_atual >= 0 else "inverse",
  )

  st.divider()

  # Análise de Gargalos por Categoria de Despesa
  st.subheader("🔍 Mapeamento de Gargalos (Maiores Saídas)")
  df_despesas = df_lancamentos[df_lancamentos["tipo"].str.lower() == "despesa"]

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

    maior_gargalo = gargalos.iloc[0] if not gargalos.empty else None
    if maior_gargalo is not None:
      st.warning(
          f"⚠️ **Principal Gargalo Identificado:** A categoria"
          f" **'{maior_gargalo['categoria']}'** consome"
          f" **R$ {maior_gargalo['valor']:,.2f}**"
          f" ({maior_gargalo['% do Total']:.1f}% de todas as suas despesas)."
          " É aqui que a intervenção cirúrgica do orçamento deve ser aplicada"
          " primeiro."
      )

  st.divider()

  # ==========================================
  # SIMULADOR DE CORTE DE CUSTOS E IMPACTO
  # ==========================================
  st.subheader("🧪 Simulador de Impacto e Cortes Estratégicos")
  st.markdown(
      "Ajuste os percentuais de redução abaixo nas principais categorias de"
      " saída para projetar o novo saldo mensal livre e a velocidade de"
      " construção da sua reserva."
  )

  if not df_despesas.empty:
    # Seleciona as top 5 maiores categorias para o simulador ficar limpo e direto
    top_categorias = gargalos.head(5)["categoria"].tolist()

    col_sim1, col_sim2 = st.columns([1, 1])

    cortes_por_categoria = {}
    with col_sim1:
      st.markdown("#### Redução Desejada por Categoria (%)")
      for cat in top_categorias:
        val_atual = gargalos.loc[gargalos["categoria"] == cat, "valor"].values[0]
        # Cria um slider de 0% a 50% de corte para cada categoria principal
        corte = st.slider(
            f"{cat} (Atual: R$ {val_atual:,.2f})", 0, 50, 0, step=5, key=f"slider_{cat}"
        )
        cortes_por_categoria[cat] = corte

    # Cálculo do impacto financeiro do simulador
    economia_total_mensal = 0
    for cat, perc in cortes_por_categoria.items():
      val_atual = gargalos.loc[gargalos["categoria"] == cat, "valor"].values[0]
      economia_total_mensal += val_atual * (perc / 100.0)

    novo_gasto_total = despesas_total - economia_total_mensal
    novo_saldo_liquido = receitas_total - novo_gasto_total
    custo_mensal_estimado = (
        novo_gasto_total / max(1, len(df_lancamentos["data"].unique()) // 30)
    )
    meta_reserva = custo_mensal_estimado * 6

    with col_sim2:
      st.markdown("#### 📊 Resultado da Simulação")
      st.metric(
          "Nova Economia Mensal",
          f"R$ {economia_total_mensal:,.2f}",
          delta=f"Dinheiro livre p/ Reserva",
      )
      st.metric(
          "Novo Saldo Líquido Mensal",
          f"R$ {novo_saldo_liquido:,.2f}",
          delta=(
              f"{(novo_saldo_liquido/receitas_total)*100:.1f}% da Receita"
              if receitas_total > 0
              else "0%"
          ),
      )
      st.metric(
          "Nova Meta de Reserva (6 Meses)", f"R$ {meta_reserva:,.2f}"
      )

      if economia_total_mensal > 0:
        meses_para_meta = (
            meta_reserva / economia_total_mensal
            if economia_total_mensal > 0
            else 0
        )
        st.success(
            f"💡 **Ritmo de Conquista:** Guardando integralmente a economia gerada"
            f" (R$ {economia_total_mensal:,.2f}/mês), você atinge a sua meta"
            f" completa de reserva de segurança em aproximadamente"
            f" **{meses_para_meta:.1f} meses**!"
        )
      else:
        st.info(
            "Arraste os controles ao lado para simular reduções de despesas e"
            " calcular o impacto no seu fluxo de caixa."
        )

  st.divider()

  # Plano de Ação para a Reserva de Segurança
  st.subheader("🛡️ Estratégia Global para a Reserva de Segurança")
  gargalo_nome = (
      maior_gargalo["categoria"]
      if "maior_gargalo" in locals() and maior_gargalo is not None
      else "principal"
  )

  st.markdown(f"""
    Para atingir a tranquilidade financeira e blindar o seu patrimônio contra imprevistos, siga rigorosamente o plano de 4 etapas fundamentais:
    
    1. **Inverta a Lógica de Poupança (Pay Yourself First):** O erro fatal é investir o que sobra. Defina que **20%** de toda receita líquida vai direto para a reserva no **mesmo dia** em que o dinheiro entra.
    2. **Ataque Cirúrgico no Gargalo:** Reduza em pelo menos 15% os gastos na categoria **{gargalo_nome}** identificada acima.
    3. **Alocação de Longo Prazo da Reserva:** O montante da reserva deve ser guardado em aplicações de **Renda Fixa com Liquidez Diária** (Tesouro Selic ou CDBs 100% do CDI com liquidez imediata), garantindo que o dinheiro renda acima da inflação sem perda de capital.
    4. **Meta de Alvo (6 Meses):** Com base no seu novo volume projetado de despesas, sua meta ideal de reserva de segurança ajustada é de aproximadamente **R$ {meta_reserva:,.2f}**.
    """)
