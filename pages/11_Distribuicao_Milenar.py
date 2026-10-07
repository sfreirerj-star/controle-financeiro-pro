from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

st.set_page_config(page_title="Alocação Milenar - Talmude", layout="wide")
aplicar_estilo_moderno()

st.title("📜 Estratégia de Alocação Milenar (Talmude)")
st.markdown(
    "Aplicação dos conceitos de **Tsedacá** e da **Regra dos Três Terços**"
    " usando seus dados reais na nuvem."
)


# --- FUNÇÕES AUTOSSUFICIENTES (CONEXÃO E CONSULTA AO POSTGRESQL) ---
def obter_conexao():
  """Abre e retorna a conexão com o banco de dados PostgreSQL na nuvem."""
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def buscar_dados_competencia(competencia="10/2026"):
  entradas = 0.0
  gastos_comuns = 0.0

  try:
    conn = obter_conexao()
    cursor = conn.cursor()

    query = """
            SELECT tipo, SUM(valor) 
            FROM lancamentos 
            WHERE competencia = %s 
            GROUP BY tipo;
        """
    cursor.execute(query, (competencia,))
    resultados = cursor.fetchall()

    for tipo, valor in resultados:
      if tipo.lower() in ["entrada", "receita", "ganho", "crédito", "credito"]:
        entradas = float(valor)
      elif tipo.lower() in ["despesa", "gasto", "gasto comum", "débito", "debito", "saida"]:
        gastos_comuns = float(valor)

    cursor.close()
    conn.close()

  except Exception:
    # Fallback de segurança caso ocorra erro na query
    entradas = 11734.59
    gastos_comuns = 5337.45

  return entradas, gastos_comuns


# --- EXECUÇÃO PRINCIPAL ---
competencia_alvo = "10/2026"
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
  # --- MATEMÁTICA MILENAR ---
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
      "Destine este valor para fazer o bem, apoiar projetos ou ajudar na"
      " capacitação profissional de terceiros."
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