import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Simulador & Guia de Dividendos em Dólar - Painel do Marcelo",
    page_icon="📈",
    layout="wide",
)

st.title("💰 Controle Financeiro — Painel do Marcelo")
st.header("📈 Simulador Inteligente & Guia Prático de Aportes em Dólar")
st.markdown(
    "Esta ferramenta utiliza dados de mercado para projetar o impacto de"
    " aportes mensais recorrentes (DCA) em ativos focados em dividendos e"
    " orienta sobre o passo a passo operacional nas corretoras globais."
)

st.divider()

# ==========================================================
# 1. SELEÇÃO DE ATIVOS E SIMULAÇÃO DE APORTES (DCA)
# ==========================================================
st.subheader("🎯 1. Simulador de Projeção de Renda (Estratégia DCA)")

ativo_escolhido = st.selectbox(
    "Selecione o Ativo de Estudo:",
    [
        "O (Realty Income - Mensal)",
        "SCHD (ETF de Dividendos - Trimestral)",
        "VYM (ETF High Yield - Trimestral)",
        "KO (Coca-Cola - Trimestral)",
    ],
)

ticker_map = {
    "O (Realty Income - Mensal)": "O",
    "SCHD (ETF de Dividendos - Trimestral)": "SCHD",
    "VYM (ETF High Yield - Trimestral)": "VYM",
    "KO (Coca-Cola - Trimestral)": "KO",
}

ticker_selecionado = ticker_map[ativo_escolhido]

# Buscando dados reais de mercado de forma automatizada
try:
  dados_ticker = yf.Ticker(ticker_selecionado)
  info = dados_ticker.info
  preco_atual = info.get("currentPrice", info.get("regularMarketPrice", 0.0))
  dividend_yield = info.get("dividendYield", 0.0)
  if dividend_yield is None:
    dividend_yield = 0.0

  st.success(
      f"🌐 Dados obtidos com sucesso para **{ticker_selecionado}** | Cotação"
      f" Atual: **US$ {preco_atual:,.2f}** | Dividend Yield Anual Estimado:"
      f" **{dividend_yield * 100:.2f}%**"
  )
except Exception as e:
  st.warning(
      "Não foi possível conectar à API de mercado no momento. Utilizando"
      " valores de simulação padrão."
  )
  preco_atual = 55.00
  dividend_yield = 0.045

col_s1, col_s2 = st.columns(2)

with col_s1:
  aporte_mensal_usd = st.number_input(
      "Aporte Mensal Planejado (US$)",
      min_value=10.0,
      max_value=5000.0,
      value=100.0,
      step=10.0,
  )
  meses_projecao = st.slider(
      "Horizonte de Projeção (Meses)", min_value=12, max_value=120, value=36, step=12
  )

with col_s2:
  st.markdown(f"""
    * **Valor do Aporte:** US$ {aporte_mensal_usd:,.2f} por mês[cite: 6].
    * **Frequência:** Disciplina constante (DCA) para suavizar a volatilidade do câmbio e do preço das cotas[cite: 6].
    * **Objetivo:** Construir posições consistentes focadas em fluxo de caixa passivo[cite: 6].
    """)

if preco_atual > 0:
  cotas_por_mes = aporte_mensal_usd / preco_atual
  total_cotas_acumuladas = cotas_por_mes * meses_projecao
  renda_anual_projetada = total_cotas_acumuladas * preco_atual * dividend_yield
  renda_mensal_projetada = renda_anual_projetada / 12

  st.subheader("📊 Resultados Projetados para o seu Perfil")

  res1, res2, res3 = st.columns(3)
  res1.metric("Cotas Acumuladas Estimadas", f"{total_cotas_acumuladas:.1f} cotas")
  res2.metric(
      "Renda Passiva Anual", f"US$ {renda_anual_projetada:,.2f} por ano"
  )
  res3.metric(
      "Complemento de Renda Mensal",
      f"US$ {renda_mensal_projetada:,.2f} / mês",
      delta="Renda Passiva Gerada 💵",
  )

st.divider()

# ==========================================================
# 2. GUIA PRÁTICO: COMO EXECUTAR A OPERAÇÃO NA CORRETORA
# ==========================================================
st.subheader(
    "🛠️ 2. Guia Prático: Como Executar a Operação na Prática (Avenue ou Nomad)"
)
st.markdown(
    "Depois de definir sua estratégia de aportes e verificar a reserva no"
    " Brasil, siga este passo a passo operacional diretamente no aplicativo"
    " da sua corretora internacional:"
)

with st.expander(
    "📘 Passo 1: Transferência de Recursos e Câmbio", expanded=True
):
  st.markdown("""
    1. **Envio de Reais:** Abra o aplicativo da sua corretora (Avenue ou Nomad)[cite: 6].
    2. **Conversão Cambial:** Faça uma TED/PIX da sua conta bancária brasileira para a conta da corretora e realize a conversão para Dólares (o sistema aplicará o câmbio comercial do dia mais o IOF correspondente).
    3. **Saldo Disponível:** Certifique-se de que o saldo em dólares já consta disponível no seu poder de compra internacional.
    """)

with st.expander("📘 Passo 2: Localização do Ativo no Home Broker"):
  st.markdown("""
    1. **Horário de Funcionamento:** Acesse a aba de investimentos/ações no horário de funcionamento da Bolsa de Nova York (NYSE / NASDAQ).
    2. **Busca pelo Ticker:** Na barra de pesquisa, digite o código exato do ativo escolhido (por exemplo: digite **`O`** para a *Realty Income* ou **`SCHD`** para o ETF)[cite: 6].
    3. **Análise Rápida:** Confira se o preço da cota exibido no aplicativo está alinhado com o seu planejamento.
    """)

with st.expander("📘 Passo 3: Envio da Ordem de Compra (Execução Segura)"):
  st.markdown("""
    1. **Tipo de Ordem:** 
       * *Ordem a Mercado (Market Order):* Compra instantaneamente pelo preço atual de cotação.
       * *Ordem Limitada (Limit Order) — **Recomendada** para maior controle:* Você define o preço máximo em dólares que aceita pagar por cota. A compra só é efetivada se o ativo atingir esse valor.
    2. **Frascos / Quantidade:** As corretoras modernas permitem a compra de ações fracionadas. Se o ativo custar US$ 55 e você quiser investir US$ 50, você conseguirá comprar uma fração exata (ex: 0.90 cotas).
    3. **Confirmação:** Revise os dados e clique em **Confirmar Compra**.
    """)

with st.expander(
    "📘 Passo 4: Custódia, Dividendos e Retenção de Impostos"
):
  st.markdown("""
    * **Custódia Automática:** As cotas compradas passam a integrar o seu patrimônio internacional de forma vitalícia na corretora.
    * **Tributação na Fonte:** Os dividendos distribuídos pelas empresas americanas já entram na sua conta da corretora com os 30% de imposto retidos automaticamente na fonte pelo governo dos EUA[cite: 6]. O valor restante é **100% líquido**.
    * **Destino do Dinheiro:** Você poderá acumular esses dólares na corretora para novas compras (efeito bola de neve) ou solicitar a remessa de volta para o Brasil quando desejar utilizar[cite: 6].
    """)

st.markdown(
    "<br><hr><p style='text-align: center; color: gray; font-size: 0.85em;'>"
    "<i>Módulo integrado de simulação e orientação operacional para o mercado"
    " internacional. Conteúdo de caráter educacional.</i></p>",
    unsafe_allow_html=True,
)
