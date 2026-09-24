import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador & Inteligência de Mercado - Painel do Marcelo",
    page_icon="📈",
    layout="wide",
)

st.title("💰 Controle Financeiro — Painel do Marcelo")
st.header("📈 Simulador Inteligente & Inteligência do Mercado Global")
st.markdown(
    "Esta ferramenta combina projeções de aportes mensais (DCA) com o"
    " monitoramento das fontes de dados utilizadas pelos maiores investidores"
    " do mundo para operar com segurança no mercado internacional."
)

st.divider()

# ==========================================================
# 1. ONDE OS GRANDES INVESTIDORES BUSCAM INFORMAÇÕES
# ==========================================================
st.subheader(
    "🌍 1. Fontes Oficiais e Termômetros do Mercado Global (Smart Money)"
)
st.markdown(
    "Para investir com segurança e sem especulação, os grandes gestores"
    " acompanham indicadores macroeconômicos e relatórios em plataformas"
    " consolidadas:"
)

col_f1, col_f2 = st.columns(2)

with col_f1:
  st.markdown("""
    #### 📊 Portais de Dados e Cotações Globais
    * **[TradingView](https://br.tradingview.com/):** A principal ferramenta gráfica do mundo para monitorar o comportamento de ativos, índices (S&P 500, NASDAQ) e cotações em tempo real.
    * **[Yahoo Finance](https://finance.yahoo.com/):** Essencial para verificar balanços trimestrais, lucros por ação (EPS) e o *Dividend Yield* histórico de empresas e ETFs.
    * **[Seeking Alpha](https://seekingalpha.com/):** Plataforma global onde analistas e investidores publicam teses detalhadas sobre ações pagadoras de dividendos e REITs.
    """)

with col_f2:
  st.markdown("""
    #### 🏛️ Indicadores Macroeconômicos (O que move a Bolsa)
    * **Taxa de Juros do FED (FOMC):** O custo do dinheiro nos EUA dita o fluxo de capital. Juros em queda costumam impulsionar ações e REITs de dividendos.
    * **Índice de Inflação (CPI e PCE):** Medem o ritmo do custo de vida americano, influenciando diretamente as decisões do Banco Central dos EUA.
    * **Relatórios 10-K e 13-F:** Documentos oficiais na SEC (CVM americana) onde grandes investidores (como o fundo de Warren Buffett) revelam o que estão comprando ou vendendo.
    """)

st.divider()

# ==========================================================
# 2. SELEÇÃO DE ATIVOS E SIMULAÇÃO DE APORTES (DCA)
# ==========================================================
st.subheader("🎯 2. Simulador de Projeção de Renda (Estratégia DCA)")

ativo_escolhido = st.selectbox(
    "Selecione o Ativo de Estudo:",
    [
        "O (Realty Income - Mensal)",
        "SCHD (ETF de Dividendos - Trimestral)",
        "VYM (ETF High Yield - Trimestral)",
        "KO (Coca-Cola - Trimestral)",
    ],
)

# Dados de referência de mercado atualizados para simulação segura
dados_ativos = {
    "O (Realty Income - Mensal)": {"preco": 55.00, "dy": 0.053},
    "SCHD (ETF de Dividendos - Trimestral)": {"preco": 28.50, "dy": 0.035},
    "VYM (ETF High Yield - Trimestral)": {"preco": 125.00, "dy": 0.030},
    "KO (Coca-Cola - Trimestral)": {"preco": 68.00, "dy": 0.031},
}

preco_atual = dados_ativos[ativo_escolhido]["preco"]
dividend_yield = dados_ativos[ativo_escolhido]["dy"]

st.success(
    f"🌐 Parâmetros de referência para **{ativo_escolhido}** | Cotação Média"
    f" Base: **US$ {preco_atual:,.2f}** | Dividend Yield Anual Estimado:"
    f" **{dividend_yield * 100:.1f}%**"
)

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
    * **Estratégia DCA:** Aportes regulares reduzem o impacto da volatilidade cambial e dos ciclos de alta e baixa da bolsa[cite: 6].
    * **Foco:** Acumulação segura de ativos geradores de fluxo de caixa passivo[cite: 6].
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
# 3. GUIA PRÁTICO: COMO EXECUTAR A OPERAÇÃO NA CORRETORA
# ==========================================================
st.subheader(
    "🛠️ 3. Guia Prático: Como Executar a Operação na Prática (Avenue ou Nomad)"
)
st.markdown(
    "Com base nas informações globais e no seu planejamento, execute suas"
    " ordens de forma segura seguindo o fluxo nas corretoras internacionais:"
)

with st.expander(
    "📘 Passo 1: Transferência de Recursos e Câmbio", expanded=True
):
  st.markdown("""
    1. **Envio de Reais:** Acesse o aplicativo da sua corretora (Avenue ou Nomad)[cite: 6].
    2. **Conversão Cambial:** Faça uma TED/PIX para a conta da corretora e converta para Dólares aplicando a cotação comercial e o IOF[cite: 6].
    3. **Saldo Disponível:** Confirme que o poder de compra em dólares já está liberado em sua conta internacional.
    """)

with st.expander("📘 Passo 2: Localização do Ativo no Home Broker"):
  st.markdown("""
    1. **Horário de Negociação:** Abra a aba de investimentos durante o horário de funcionamento da Bolsa de Nova York (NYSE / NASDAQ).
    2. **Busca pelo Ticker:** Digite o código oficial do ativo na barra de pesquisa (ex: **`O`** para a *Realty Income* ou **`SCHD`** para o ETF)[cite: 6].
    3. **Análise de Conjuntura:** Confira o comportamento recente do preço antes de prosseguir.
    """)

with st.expander("📘 Passo 3: Envio da Ordem de Compra (Execução Segura)"):
  st.markdown("""
    1. **Tipo de Ordem:** 
       * *Ordem a Mercado:* Executa imediatamente pelo preço atual.
       * *Ordem Limitada (Recomendada):* Define o teto de preço máximo que você aceita pagar por cota, evitando oscilações bruscas do momento.
    2. **Fracionamento:** Utilize o recurso de compra fracionada caso o valor do aporte não atinja o preço integral de uma cota inteira.
    3. **Confirmação:** Revise os parâmetros e finalize a ordem.
    """)

with st.expander(
    "📘 Passo 4: Custódia, Dividendos e Retenção de Impostos"
):
  st.markdown("""
    * **Custódia Vitalícia:** As cotas adquiridas ficam armazenadas de forma segura na sua conta internacional.
    * **Tributação Automática:** Os dividendos entram líquidos na sua conta após a retenção automática de 30% de imposto na fonte pelo governo americano[cite: 6].
    * **Utilização do Caixa:** Acumule para gerar efeito bola de neve ou solicite remessas futuras para o Brasil conforme sua necessidade[cite: 6].
    """)

st.markdown(
    "<br><hr><p style='text-align: center; color: gray; font-size: 0.85em;'>"
    "<i>Módulo integrado de inteligência global, simulação de aportes e orientação"
    " operacional. Conteúdo de caráter educacional.</i></p>",
    unsafe_allow_html=True,
)
