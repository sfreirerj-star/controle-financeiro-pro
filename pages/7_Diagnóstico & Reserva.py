import pandas as pd
import streamlit as st


def render_aba_diagnostico(conn):
  st.header("🎯 Diagnóstico de Gargalos & Estratégia de Reserva")
  st.markdown(
      "Esta aba analisa os seus lançamentos e dívidas para identificar onde"
      " sua renda está escoando e traça a rota ideal para construir sua"
      " reserva de segurança com base em metodologias globais de gestão"
      " financeira."
  )

  try:
    # Carregando dados reais do banco PostgreSQL (Supabase)
    df_lancamentos = pd.read_sql(
        "SELECT * FROM lancamentos", con=conn
    )  # Colunas esperadas: tipo, categoria, valor, data
    df_dividas = pd.read_sql("SELECT * FROM dividas", con=conn)
  except Exception as e:
    st.error(
        f"Erro ao carregar dados do banco para o diagnóstico: {e}"
    )
    return

  if df_lancamentos.empty:
    st.info(
        "Nenhum lançamento encontrado para gerar o diagnóstico no momento."
    )
    return

  # Tratamento de dados
  df_lancamentos["valor"] = pd.to_numeric(
      df_lancamentos["valor"], errors="coerce"
  ).fillna(0.0)

  receitas_total = df_lancamentos[df_lancamentos["tipo"].str.lower() == "receita"][
      "valor"
  ].sum()
  despesas_total = df_lancamentos[df_lancamentos["tipo"].str.lower() == "despesa"][
      "valor"
  ].sum()
  saldo_atual = receitas_total - despesas_total

  # Métricas Gerais
  col1, col2, col3 = st.columns(3)
  col1.metric("Receita Acumulada", f"R$ {receitas_total:,.2f}")
  col2.metric("Despesa Acumulada", f"R$ {despesas_total:,.2f}")
  col3.metric(
      "Resultado Líquido",
      f"R$ {saldo_atual:,.2f}",
      delta=f"{(saldo_atual/receitas_total)*100:.1f}% da Receita"
      if receitas_total > 0
      else "0%",
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

  # Plano de Ação para a Reserva de Segurança
  st.subheader("🛡️ Estratégia Global para a Reserva de Segurança")

  custo_mensal_estimado = (
      despesas_total / max(1, len(df_lancamentos["data"].unique()) // 30)
  )  # Estimativa base
  meta_reserva = custo_mensal_estimado * 6

  st.markdown(f"""
    Para atingir a tranquilidade financeira e blindar o seu patrimônio contra imprevistos, siga rigorosamente o plano de 4 etapas fundamentais:
    
    1. **Inverta a Lógica de Poupança (Pay Yourself First):** O erro fatal é investir o que sobra. Defina que **20%** de toda receita líquida vai direto para a reserva no **mesmo dia** em que o dinheiro entra.
    2. **Ataque Cirúrgico no Gargalo:** Reduza em pelo menos 15% os gastos na categoria **{maior_gargalo['categoria'] if 'maior_gargalo' in locals() and maior_gargalo is not None else 'principal'}** identificada acima.
    3. **Alocação de Longo Prazo da Reserva:** O montante da reserva deve ser guardado em aplicações de **Renda Fixa com Liquidez Diária** (Tesouro Selic ou CDBs 100% do CDI com liquidez imediata), garantindo que o dinheiro renda acima da inflação sem risco de perda de capital.
    4. **Meta de Alvo (6 Meses):** Com base no seu volume de despesas, sua meta ideal de reserva de segurança é de aproximadamente **R$ {meta_reserva:,.2f}**.
    """)
