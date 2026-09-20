from datetime import datetime
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro - Sair do Vermelho", page_icon="💰", layout="wide"
)

def obter_conexao():
    """Retorna a conexão com a base de dados PostgreSQL centralizada nos secrets."""
    return psycopg2.connect(st.secrets["DATABASE_URL"])

# Inicialização segura dos DataFrames
df_lancamentos = pd.DataFrame(columns=["id", "data", "tipo", "categoria", "descricao", "valor"])
df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])
df_dividas = pd.DataFrame(columns=["id", "credor", "valor_total", "juros_mensal", "status"])

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
        df_aportes = pd.read_sql_query("SELECT id, data, valor, local_aplicacao FROM desafio_aportes", conexao)
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
    df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    total_aportes = df_aportes["valor_num"].sum()
else:
    total_aportes = 0.0

def fmt_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CORPO DA PÁGINA PRINCIPAL (PAINEL & GRÁFICOS) ---
st.title("💰 Controle Financeiro - Sair do Vermelho")
st.write("Aplicativo unificado de controle de créditos, débitos e investimentos.")

# Tratamento flexível para capturar receitas e despesas de lançamentos
if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor"] = pd.to_numeric(df_lancamentos["valor"], errors="coerce").fillna(0.0)
    df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()
else:
    df_lancamentos["tipo_clean"] = ""

total_receitas = (
    df_lancamentos[df_lancamentos["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])]["valor"].sum()
    if not df_lancamentos.empty else 0.0
)

total_gastos = (
    df_lancamentos[df_lancamentos["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]["valor"].sum()
    if not df_lancamentos.empty else 0.0
)

# Saldo Atual da Conta Corrente: Entradas menos Gastos Comuns menos o dinheiro enviado para os Aportes
saldo = total_receitas - total_gastos - total_aportes

st.subheader("Resumo do Mês e Visualização Gráfica")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Entradas", fmt_moeda(total_receitas))
col2.metric("Gastos Comuns", fmt_moeda(total_gastos))
col3.metric("Total em Aportes", fmt_moeda(total_aportes))

if saldo >= 0:
    col4.metric("Saldo Atual", fmt_moeda(saldo), delta="No Azul 💙")
else:
    col4.metric("Saldo Atual", fmt_moeda(saldo), delta="No Vermelho 🔴", delta_color="inverse")

st.divider()

st.subheader("Distribuição de Gastos e Investimentos (Visão Consolidada)")

df_gastos_grafico = (
    df_lancamentos[df_lancamentos["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])].copy()
    if not df_lancamentos.empty else pd.DataFrame()
)

# Integrando os aportes como fatias de investimento nos gráficos globais
if not df_aportes.empty:
    df_ap_graf = pd.DataFrame()
    df_ap_graf["categoria"] = ["Investimento / Aporte"] * len(df_aportes)
    df_ap_graf["valor"] = df_aportes["valor_num"]
    df_gastos_grafico = pd.concat([df_gastos_grafico, df_ap_graf], ignore_index=True)

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
        fig_barras.update_traces(texttemplate="R$ %{text:.2f}", textposition="outside")
        fig_barras.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_barras, use_container_width=True)
else:
    st.info("Nenhum registro encontrado para gerar gráficos.")

st.divider()
st.subheader("Histórico Geral de Lançamentos")
if not df_lancamentos.empty and "id" in df_lancamentos.columns:
    df_exibicao = df_lancamentos.tail(10).copy()
    if "tipo_clean" in df_exibicao.columns:
        df_exibicao = df_exibicao.drop(columns=["tipo_clean"])
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
    st.info("Nenhum lançamento encontrado.")