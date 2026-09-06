import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Desafio Reserva Financeira", page_icon="🎯", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.subheader("🎯 Desafio Personalizado de Reserva Financeira")
st.write("Defina sua meta financeira, ajuste o prazo ideal para o seu bolso e acompanhe o seu progresso mês a mês.")

def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CONFIGURAÇÃO DO DESAFIO PELO USUÁRIO ---
with st.expander("⚙️ Configurar / Ajustar Meu Desafio", expanded=True):
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        meta_total = st.number_input("Meta Desejada (R$)", min_value=100.0, value=10000.0, step=500.0, format="%.2f")
    with col_c2:
        meses_totais = st.number_input("Prazo (Meses)", min_value=1, max_value=60, value=12, step=1)
    with col_c3:
        valor_atual = st.number_input("Quanto já guardou até agora? (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")

# Cálculo automático da meta mensal com base na escolha
meta_mensal_base = meta_total / meses_totais if meses_totais > 0 else meta_total
progresso_perc = min(valor_atual / meta_total, 1.0) if meta_total > 0 else 0.0

st.divider()

# --- MÉTRICAS E BARRA DE PROGRESSO ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Meta Escolhida", fmt_moeda(meta_total))
with col2:
    st.metric("Meta Mensal Necessária", fmt_moeda(meta_mensal_base))
with col3:
    st.metric("Total Já Guardado", fmt_moeda(valor_atual))
with col4:
    st.metric("Prazo", f"{meses_totais} Meses")

st.write("")
st.progress(progresso_perc, text=f"Progresso Atual do Desafio: {progresso_perc * 100:.1f}% alcançado")

# Se atingir a meta, exibe parabéns e opção de recomeçar
if valor_atual >= meta_total and meta_total > 0:
    st.success("🎉 PARABÉNS! Você atingiu ou superou a meta estabelecida para este desafio!")
    if st.button("🚀 Iniciar Novo Desafio"):
        st.balloons()
        st.info("Para iniciar um novo ciclo, basta subir em 'Configurar / Ajustar Meu Desafio' e definir uma nova meta ou prazo superior!")

st.divider()

# --- TABELA DE EVOLUÇÃO PLANEJADA ---
st.markdown("### 📊 Tabela de Evolução Planejada (Mês a Mês)")

dados_desafio = []
acumulado = 0.0

for i in range(1, int(meses_totais) + 1):
    acumulado += meta_mensal_base
    dados_desafio.append({
        "Mês": f"Mês {i}",
        "Meta do Mês": meta_mensal_base,
        "Meta Acumulada": acumulado
    })

df_meta = pd.DataFrame(dados_desafio)

df_exibicao = df_meta.copy()
df_exibicao["Meta do Mês"] = df_exibicao["Meta do Mês"].apply(fmt_moeda)
df_exibicao["Meta Acumulada"] = df_exibicao["Meta Acumulada"].apply(fmt_moeda)

st.dataframe(df_exibicao, use_container_width=True, height=250)

st.divider()

st.markdown("### 💡 Dicas Estratégicas:")
st.markdown("""
* **Flexibilidade é a chave:** Se achar que a parcela mensal está alta, basta subir o prazo (ex: de 12 para 18 ou 24 meses) para o valor cair e caber perfeitamente no seu orçamento.
* **Comemore cada etapa:** Cada mês que você cumpre a meta estipulada é um passo firme rumo à sua tranquilidade financeira.
""")
