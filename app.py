import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro Pro", page_icon="💰", layout="centered"
)

# Conexão com o Banco de Dados PostgreSQL no Supabase via Secrets
def obter_conexao():
    url_conexao = st.secrets["DATABASE_URL"]
    return psycopg2.connect(url_conexao)

# Inicializar as tabelas no Supabase caso não existam
def inicializar_banco():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
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
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados no Supabase: {e}.")
        st.stop()

inicializar_banco()

st.title("💰 Controle Financeiro - Sair do Vermelho")
st.write("Aplicativo de controle total de créditos, débitos e investimentos.")

# Carregar dados do Supabase para DataFrames do Pandas
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
    conexao.close()
except Exception:
    df_lancamentos = pd.DataFrame(
        columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
    )
    df_dividas = pd.DataFrame(
        columns=["id", "credor", "valor_total", "juros_mensal", "status"]
    )

st.subheader("Resumo do Mês e Visualização Gráfica")

if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor"] = pd.to_numeric(
        df_lancamentos["valor"], errors="coerce"
    ).fillna(0.0)
    
    total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"]["valor"].sum()
    total_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"]["valor"].sum()
    saldo = total_receitas - total_despesas

    # Função auxiliar para formatar moeda no padrão brasileiro (R$ X.XXX,XX)
    def fmt_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", fmt_moeda(total_receitas))
    col2.metric("Saídas", fmt_moeda(total_despesas))

    if saldo >= 0:
        col3.metric("Saldo Atual", fmt_moeda(saldo), delta="No Azul 💙")
    else:
        col3.metric(
            "Saldo Atual",
            fmt_moeda(saldo),
            delta="No Vermelho 🔴",
            delta_color="inverse",
        )

    st.divider()

    # Gráficos se houver despesas
    df_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"]
    if not df_despesas.empty:
        st.write("### Distribuição dos Gastos por Categoria")
        gasto_por_cat = df_despesas.groupby("categoria")["valor"].sum()

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.write("**Gráfico de Pizza**")
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.pie(
                gasto_por_cat, labels=gasto_por_cat.index, autopct="%1.1f%%", startangle=90
            )
            ax1.axis("equal")
            st.pyplot(fig1)

        with col_g2:
            st.write("**Gráfico de Barras**")
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            gasto_por_cat.plot(kind="bar", ax=ax2, color="#1a73e8")
            ax2.set_ylabel("Valor (R$)")
            plt.xticks(rotation=45)
            st.pyplot(fig2)
    else:
        st.info("Cadastre algumas despesas para visualizar os gráficos.")

    st.subheader("Histórico de Lançamentos")
    
    # Formatar coluna valor para exibição e remover índice lateral
    df_exibicao = df_lancamentos.tail(10).copy()
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
else:
    st.info(
        "Nenhum lançamento registrado ainda. Utilize a aba '1_Novo_Lancamento' no"
        " menu lateral."
    )

st.divider()
st.subheader("⚠️ Mapeamento de Dívidas Ativas")

if not df_dividas.empty:
    df_dividas_exibicao = df_dividas.copy()
    if "valor_total" in df_dividas_exibicao.columns:
        df_dividas_exibicao["valor_total"] = pd.to_numeric(df_dividas_exibicao["valor_total"], errors="coerce").fillna(0.0).apply(fmt_moeda)
    if "juros_mensal" in df_dividas_exibicao.columns:
        df_dividas_exibicao["juros_mensal"] = pd.to_numeric(df_dividas_exibicao["juros_mensal"], errors="coerce").fillna(0.0).apply(lambda x: f"{x:.2f}%")
        
    st.dataframe(df_dividas_exibicao.set_index("id"), use_container_width=True)
else:
    st.info("Nenhuma dívida cadastrada no momento.")