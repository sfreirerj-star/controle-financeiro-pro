import os
import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DE CONEXÃO (SUPABASE / POSTGRESQL OU SQLITE) ---
DATABASE_URL = None
try:
    if "DATABASE_URL" in st.secrets:
        DATABASE_URL = st.secrets["DATABASE_URL"]
except Exception:
    pass

if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    def obter_conexao():
        return psycopg2.connect(DATABASE_URL)
    DB_TYPE = "postgres"
else:
    import sqlite3
    DB_NAME = "financas.db"
    def obter_conexao():
        return sqlite3.connect(DB_NAME)
    DB_TYPE = "sqlite"

def inicializar_banco():
    """Cria o banco de dados e as tabelas se elas não existirem."""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    if DB_TYPE == "postgres":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id SERIAL PRIMARY KEY,
                data TEXT,
                tipo TEXT,
                categoria TEXT,
                descricao TEXT,
                valor REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id SERIAL PRIMARY KEY,
                credor TEXT,
                valor_total REAL,
                juros_mensal REAL,
                status TEXT
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                tipo TEXT,
                categoria TEXT,
                descricao TEXT,
                valor REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dividas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credor TEXT,
                valor_total REAL,
                juros_mensal REAL,
                status TEXT
            )
        """)
        
    conexao.commit()
    conexao.close()

def adicionar_lancamento_db(data, tipo, categoria, descricao, valor):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    if DB_TYPE == "postgres":
        cursor.execute(
            "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
            (data, tipo, categoria, descricao, valor)
        )
    else:
        cursor.execute(
            "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
            (data, tipo, categoria, descricao, valor)
        )
        
    conexao.commit()
    conexao.close()

def adicionar_divida_db(credor, valor_total, juros_mensal, status):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    if DB_TYPE == "postgres":
        cursor.execute(
            "INSERT INTO dividas (credor, valor_total, juros_mensal, status) VALUES (%s, %s, %s, %s)",
            (credor, valor_total, juros_mensal, status)
        )
    else:
        cursor.execute(
            "INSERT INTO dividas (credor, valor_total, juros_mensal, status) VALUES (?, ?, ?, ?)",
            (credor, valor_total, juros_mensal, status)
        )
        
    conexao.commit()
    conexao.close()

def carregar_dados():
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
    conexao.close()
    return df_lancamentos, df_dividas

# Inicializa o banco ao iniciar o script
inicializar_banco()
# --- INTERFACE VISUAL DO STREAMLIT ---
st.set_page_config(page_title="Controle Financeiro Pro", page_icon="💰", layout="wide")

st.title("💰 Controle Financeiro - Sair do Vermelho")
st.markdown("Aplicativo de controle total de créditos, débitos e investimentos.")

menu = st.sidebar.selectbox("Menu Principal", ["Painel & Gráficos", "Novo Lançamento", "Raio-X de Dívidas"])

df_lancamentos, df_dividas = carregar_dados()

if menu == "Painel & Gráficos":
    st.subheader("Resumo do Mês e Visualização Gráfica")
    
    if not df_lancamentos.empty:
        total_receitas = df_lancamentos[df_lancamentos['tipo'] == 'Receita']['valor'].sum()
        total_despesas = df_lancamentos[df_lancamentos['tipo'] == 'Despesa']['valor'].sum()
        saldo = total_receitas - total_despesas
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Entradas", f"R$ {total_receitas:.2f}")
        col2.metric("Total de Saídas", f"R$ {total_despesas:.2f}")
        col3.metric("Saldo Atual", f"R$ {saldo:.2f}")
        
        st.markdown("---")
        st.dataframe(df_lancamentos, use_container_width=True)
    else:
        st.info("Nenhum lançamento registrado ainda. Utilize a aba 'Novo Lançamento' para começar.")
        
    st.subheader("Dívidas Mapeadas")
    if not df_dividas.empty:
        st.dataframe(df_dividas, use_container_width=True)
    else:
        st.info("Nenhuma dívida cadastrada.")

elif menu == "Novo Lançamento":
    st.subheader("Registrar Novo Lançamento")
    with st.form("form_lancamento"):
        data = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"))
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        categoria = st.text_input("Categoria (Ex: Alimentação, Moradia, Cartão)")
        descricao = st.text_input("Descrição / Estabelecimento")
        valor = st.number_input("Valor (R$)", min_format_spec="%.2f", format="%.2f")
        
        submitted = st.form_submit_button("Salvar Lançamento")
        if submitted:
            if categoria and descricao and valor > 0:
                adicionar_lancamento_db(data, tipo, categoria, descricao, valor)
                st.success("Lançamento registrado com sucesso no Supabase!")
            else:
                st.error("Preencha todos os campos corretamente.")

elif menu == "Raio-X de Dívidas":
    st.subheader("Cadastrar e Mapear Dívida")
    with st.form("form_divida"):
        credor = st.text_input("Credor / Nome da Dívida")
        valor_total = st.number_input("Valor Total Devido (R$)", format="%.2f")
        juros_mensal = st.number_input("Taxa de Juros Mensal (%)", format="%.2f")
        status = "Pendente"
        
        submitted_divida = st.form_submit_button("Cadastrar Dívida")
        if submitted_divida:
            if credor and valor_total > 0:
                adicionar_divida_db(credor, valor_total, juros_mensal, status)
                st.success("Dívida cadastrada com sucesso!")
            else:
                st.error("Preencha os campos corretamente.")