from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Relatórios e Consultas", page_icon="📈", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.subheader("📈 Relatórios, Consultas e Fechamento de Mês")
st.write("Filtre seus lançamentos detalhadamente ou acompanhe o fechamento mês a mês com o saldo remanescente.")

# Carregar todos os lançamentos do banco
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar lançamentos: {e}")
    df_lancamentos = pd.DataFrame()

if not df_lancamentos.empty:
    # Tratamento da data para ordenações e filtros
    df_lancamentos["data_dt"] = pd.to_datetime(df_lancamentos["data"], format="%d/%m/%Y", errors="coerce")
    
    # Criamos abas para organizar a tela de forma limpa
    aba1, aba2 = st.tabs(["🔍 Consulta e Filtros Avançados", "📅 Fechamento de Mês (Saldo Remanescente)"])

    # --- ABA 1: CONSULTA E FILTROS AVANÇADOS ---
    with aba1:
        st.markdown("### 🔎 Filtrar Lançamentos")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            # Filtro por Tipo (Todos, Despesa, Receita)
            tipos_disponiveis = ["Todos"] + list(df_lancamentos["tipo"].dropna().unique())
            filtro_tipo = st.selectbox("Filtrar por Tipo", tipos_disponiveis)
            
        with col_f2:
            # Filtro por Categoria
            categorias_disponiveis = ["Todas"] + sorted(list(df_lancamentos["categoria"].dropna().unique()))
            filtro_categoria = st.selectbox("Filtrar por Categoria", categorias_disponiveis)
            
        with col_f3:
            # Filtro por termo na descrição
            filtro_texto = st.text_input("Buscar na Descrição (Palavra-chave)")

        # Aplicação dos filtros
        df_filtrado = df_lancamentos.copy()
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]
            
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_categoria]
            
        if filtro_texto:
            df_filtrado = df_filtrado[df_filtrado["descricao"].str.contains(filtro_texto, case=False, na=False)]

        # Formatação de valores para exibição
        def fmt_moeda(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        df_exibicao = df_filtrado.copy()
        df_exibicao["valor"] = pd.to_numeric(df_exibicao["valor"], errors="coerce").fillna(0.0).apply(fmt_moeda)
        
        colunas_mostrar = ["id", "data", "tipo", "categoria", "descricao", "valor"]
        st.dataframe(df_exibicao[colunas_mostrar].set_index("id"), use_container_width=True)
        
        # Métrica do total filtrado
        total_filtrado = pd.to_numeric(df_filtrado["valor"], errors="coerce").sum()
        st.info(f"📊 **Total dos lançamentos filtrados:** {fmt_moeda(total_filtrado)}")

    # --- ABA 2: FECHAMENTO DE MÊS (FLUXO E SALDO REMANESCENTE) ---
    with aba2:
        st.markdown("### 📅 Fechamento Mensal e Evolução de Saldo")
        st.write("Visão consolidada de entradas, saídas, resultado líquido do mês e o saldo remanescente acumulado.")

        # Extração de Mês e Ano para agrupamento
        df_lancamentos["ano_mes"] = df_lancamentos["data_dt"].dt.to_period("M")
        
        if df_lancamentos["ano_mes"].notna().any():
            # Separa receitas e despesas por mês
            df_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"].groupby("ano_mes")["valor"].sum().reset_index(name="entradas")
            df_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"].groupby("ano_mes")["valor"].sum().reset_index(name="saidas")
            
            # Une os dados mensais
            df_fechamento = pd.merge(df_receitas, df_despesas, on="ano_mes", how="outer").fillna(0.0)
            df_fechamento = df_fechamento.sort_values(by="ano_mes", ascending=True).reset_index(drop=True)
            
            # Cálculos de Resultado e Saldo Remanescente Acumulado
            df_fechamento["resultado_mes"] = df_fechamento["entradas"] - df_fechamento["saidas"]
            df_fechamento["saldo_remanescente"] = df_fechamento["resultado_mes"].cumsum()
            
            # Formatação bonita para exibição do mês (ex: Setembro/2026)
            df_fechamento["mes_ano_str"] = df_fechamento["ano_mes"].dt.strftime("%m/%Y")
            
            # Tabela final para o usuário
            df_tabela_mensal = pd.DataFrame({
                "Mês/Ano": df_fechamento["mes_ano_str"],
                "Total Entradas": df_fechamento["entradas"].apply(fmt_moeda),
                "Total Saídas": df_fechamento["saidas"].apply(fmt_moeda),
                "Resultado do Mês": df_fechamento["resultado_mes"].apply(fmt_moeda),
                "Saldo Remanescente (Acumulado)": df_fechamento["saldo_remanescente"].apply(fmt_moeda)
            })
            
            st.dataframe(df_tabela_mensal, use_container_width=True)
        else:
            st.warning("Não há datas válidas o suficiente para gerar o fechamento mensal.")
else:
    st.info("Nenhum lançamento cadastrado no sistema para gerar relatórios.")
