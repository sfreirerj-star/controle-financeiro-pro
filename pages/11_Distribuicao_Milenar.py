import streamlit as st
import pandas as pd
# Importa a função que criamos no passo anterior
from utils import calcular_distribuicao_milenar 

st.set_page_config(page_title="Alocação Milenar - Talmude", layout="wide")

st.title("📜 Estratégia de Alocação Milenar (Talmude)")
st.markdown("Aplicação dos conceitos de **Tsedacá** e da **Regra dos Três Terços** no seu saldo real.")

# --- INTEGRAÇÃO COM SEU BANCO DE DADOS ---
# Aqui simulamos a busca dos seus dados reais (Entradas: 11.636,70 | Gastos: 5.195,47)
# Se você tiver uma função no database.py ou utils.py que busca o saldo atualizado, 
# você pode substituir os valores abaixo por ela. Ex: saldo_atual = database.buscar_ultimo_saldo()
entradas_db = 11636.70
gastos_db = 5195.47
saldo_padrao = entradas_db - gastos_db

# Permitir que o usuário use o saldo do sistema ou digite um novo para simular
usar_saldo_sistema = st.checkbox("Usar saldo atual do sistema (Competência Ativa)", value=True)

if usar_saldo_sistema:
    saldo_disponivel = saldo_padrao
    st.info(f"💰 Utilizando o Saldo Remanescente do sistema: **R$ {saldo_disponivel:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
else:
    saldo_disponivel = st.number_input("Digite o saldo livre para simulação (R$)", value=float(saldo_padrao), step=100.0)

st.divider()

# --- EXECUÇÃO DA LÓGICA E EXIBIÇÃO ---
if saldo_disponivel > 0:
    # Executa a função concentrada no seu utils.py
    resultado = calcular_distribuicao_milenar(saldo_disponivel)
    
    # Bloco Informativo de Impacto (Tsedacá)
    st.warning(f"🕊️ **Tsedacá (Justiça Social - 10%): R$ {resultado['tsedaca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    st.caption("Destine este valor para doações, apoiar projetos comunitários ou capacitar alguém antes de investir no seu patrimônio.")
    
    st.write("")
    st.markdown("### 🎯 Divisão Estratégica dos Três Terços")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🛡️ **1/3 em Terras**")
        st.subheader(f"R$ {resultado['terras']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown("**Foco:** Segurança e Preservação\n\n*Sugestão:* FIIs de Tijolo, Imóveis ou Renda Fixa atrelada à inflação (IPCA+).")
        
    with col2:
        st.success("📈 **1/3 em Negócios**")
        st.subheader(f"R$ {resultado['negocios']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown("**Foco:** Multiplicação e Crescimento\n\n*Sugestão:* Ações, fundos de ações, investimento no próprio negócio ou educação de alto nível.")
        
    with col3:
        st.error("💰 **1/3 em Mãos**")
        st.subheader(f"R$ {resultado['em_maos']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown("**Foco:** Liquidez e Oportunidade\n\n*Sugestão:* Tesouro Selic, CDB 100% CDI com liquidez diária (Reserva de Oportunidade).")

    # Gráfico Visual para enriquecer a página
    st.write("")
    st.markdown("### 📊 Proporção Visual da Distribuição")
    df_grafico = pd.DataFrame({
        "Destino": ["Tsedacá", "Terras (Segurança)", "Negócios (Crescimento)", "Em Mãos (Liquidez)"],
        "Valores": [resultado['tsedaca'], resultado['terras'], resultado['negocios'], resultado['em_maos']]
    })
    st.bar_chart(data=df_grafico, x="Destino", y="Valores")

else:
    st.error("O saldo disponível precisa ser maior que zero para aplicar a distribuição.")
