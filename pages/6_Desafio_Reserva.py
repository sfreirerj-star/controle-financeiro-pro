from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Desafio Reserva Financeira", page_icon="🎯", layout="wide"
)


def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


# Criar tabela de aportes do desafio se não existir
def garantir_tabela():
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS desafio_aportes (
                id SERIAL PRIMARY KEY,
                data TEXT NOT NULL,
                valor NUMERIC(10,2) NOT NULL,
                local_aplicacao TEXT NOT NULL
            )
        """
        )
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception:
        pass


garantir_tabela()

st.subheader("🎯 Desafio Personalizado de Reserva Financeira")
st.write(
    "Defina sua meta mensal, registre seus aportes informando a data e o local, e acompanhe o crescimento do seu patrimônio."
)


def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


# --- CONFIGURAÇÃO DO DESAFIO (OPÇÕES DE META MENSAL) ---
with st.expander(
    "⚙️ Configurar / Selecionar Meta Mensal (Inclui CPROEIS)", expanded=True
):
    opcoes_meta_mensal = {
        "Personalizado (Definir manual)": 0.0,
        "1 Plantão CPROEIS (R$ 532,00 / mês)": 532.00,
        "Conservador (R$ 300,00 / mês)": 300.00,
        "Intermediário (R$ 800,00 / mês)": 800.00,
        "Agressivo (R$ 1.000,00 / mês)": 1000.00,
    }

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        escolha_perfil = st.selectbox(
            "Escolha o Perfil / Valor Mensal", list(opcoes_meta_mensal.keys())
        )
    with col_m2:
        meses_totais = st.number_input(
            "Prazo do Desafio (Meses)",
            min_value=1,
            max_value=60,
            value=12,
            step=1,
        )

    # Definir valor mensal com base na escolha
    if escolha_perfil != "Personalizado (Definir manual)":
        meta_mensal_base = opcoes_meta_mensal[escolha_perfil]
    else:
        meta_mensal_base = st.number_input(
            "Valor Desejado por Mês (R$)",
            min_value=50.0,
            value=532.00,
            step=50.0,
            format="%.2f",
        )

    meta_total = meta_mensal_base * meses_totais

# --- BUSCAR APORTES REAIS DO BANCO ---
try:
    conexao = obter_conexao()
    df_aportes = pd.read_sql_query(
        "SELECT id, data, valor, local_aplicacao FROM desafio_aportes ORDER BY id DESC",
        conexao,
    )
    conexao.close()
except Exception:
    df_aportes = pd.DataFrame(
        columns=["id", "data", "valor", "local_aplicacao"]
    )

if not df_aportes.empty:
    df_aportes["valor_num"] = pd.to_numeric(
        df_aportes["valor"], errors="coerce"
    ).fillna(0.0)
    total_guardado = df_aportes["valor_num"].sum()
else:
    total_guardado = 0.0

progresso_perc = (
    min(total_guardado / meta_total, 1.0) if meta_total > 0 else 0.0
)

st.divider()

# --- MÉTRICAS E BARRA DE PROGRESSO ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Meta Total Calculada", fmt_moeda(meta_total))
with col2:
    st.metric("Meta Mensal Escolhida", fmt_moeda(meta_mensal_base))
with col3:
    st.metric("Total Acumulado Real", fmt_moeda(total_guardado))
with col4:
    st.metric("Prazo", f"{meses_totais} Meses")

st.write("")
st.progress(
    progresso_perc,
    text=f"Progresso Atual do Desafio: {progresso_perc * 100:.1f}% alcançado",
)

if total_guardado >= meta_total and meta_total > 0:
    st.success(
        "🎉 PARABÉNS! Você atingiu ou superou a meta estabelecida para este desafio!"
    )
    if st.button("🔄 Iniciar Novo Ciclo"):
        st.balloons()

st.divider()

# --- ABA DE REGISTRO E TABELA DE APORTES ---
st.markdown("### 📥 Registrar Novo Depósito / Aporte")
with st.form("form_novo_aporte"):
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        data_aporte = st.text_input(
            "Data do Depósito (DD/MM/AAAA)",
            value=datetime.now().strftime("%d/%m/%Y"),
        )
    with col_a2:
        valor_aporte = st.number_input(
            "Valor Depositado (R$)",
            min_value=1.0,
            value=meta_mensal_base,
            step=10.0,
            format="%.2f",
        )
    with col_a3:
        local_aporte = st.text_input(
            "Local da Aplicação",
            value="Nubank (Caixinha / RDB 100% CDI)",
            placeholder="Ex: Banco Inter, Tesouro Direto...",
        )

    if st.form_submit_button("💾 Salvar Aporte no Desafio"):
        try:
            datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "INSERT INTO desafio_aportes (data, valor, local_aplicacao) VALUES (%s, %s, %s)",
                (data_aporte.strip(), valor_aporte, local_aporte.strip()),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Aporte registrado e acumulado com sucesso!")
            st.rerun()
        except ValueError:
            st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

st.divider()

st.markdown("### 📊 Extrato de Aportes Realizados")
if not df_aportes.empty:
    df_exib_aportes = df_aportes.copy()
    df_exib_aportes["Valor"] = df_exib_aportes["valor_num"].apply(fmt_moeda)
    df_tabela_final = df_exib_aportes[
        ["id", "data", "Local da Aplicação", "Valor"]
    ].rename(columns={"local_aplicacao": "Local da Aplicação"})
    # Ajustando nome da coluna corretamente
    df_tabela_final = df_aportes[["id", "data", "local_aplicacao", "Valor"]].rename(
        columns={"local_aplicacao": "Local da Aplicação"}
    )
    st.dataframe(
        df_tabela_final.set_index("id"), use_container_width=True, height=200
    )

    if st.button("🗑️ Excluir Último Aporte Registrado"):
        try:
            ultimo_id = df_aportes["id"].max()
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "DELETE FROM desafio_aportes WHERE id = %s", (int(ultimo_id),)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.warning("Último aporte removido com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir: {e}")
else:
    st.info("Nenhum aporte registrado ainda. Utilize o formulário acima para registrar o seu primeiro depósito!")

st.divider()

# --- ORIENTAÇÃO DE MERCADO FINANCEIRO ---
st.markdown("### 💡 Orientação do Mercado Financeiro: Onde Aplicar?")
st.markdown("""
Para uma **reserva financeira de curto/médio prazo** (como este desafio de 1 ano), a melhor diretriz do mercado financeiro é priorizar **Renda Fixa com Liquidez Diária e Baixo Risco**:

1. **Contas Digitais com Rendimento Automático (100% do CDI):** Opções como *Nubank*, *Banco Inter* ou *99Pay* que rendem todos os dias úteis e permitem resgate imediato caso precise do dinheiro.
2. **Tesouro Selic:** Título público federal extremamente seguro, ideal para guardar o dinheiro com rentabilidade atrelada à taxa básica de juros da economia (Selic).
3. **CDBs de Bancos Médios com Liquidez Diária:** Certificados de Depósito Bancário emitidos por instituições sólidas que pagem 100% ou mais do CDI e contem com a garantia do **FGC (Fundo Garantidor de Crédito)** até R$ 250 mil por CPF.

*Evite a Poupança tradicional:* Atualmente, em períodos de juros mais altos, a poupança rende menos do que o CDI e perde o rendimento nos aniversários mensais. Prefira sempre uma aplicação que rende diariamente em 100% do CDI.
""")
