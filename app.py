from datetime import datetime
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro Pro", page_icon="💰", layout="wide"
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
                status TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS desafio_aportes (
                id SERIAL PRIMARY KEY,
                data TEXT,
                valor REAL,
                local_aplicacao TEXT
            )
        """)
    conexao.commit()
    cursor.close()
    conexao.close()
  except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados no Supabase: {e}.")
    st.stop()


inicializar_banco()

# Menu lateral de navegação simulada / abas
menu = st.sidebar.selectbox(
    "Navegação",
    [
        "Visão Geral / Painel",
        "Novo Lançamento / Aporte",
        "Gerenciar Lançamentos",
    ],
)

# Carregar dados do Supabase para DataFrames do Pandas
try:
  conexao = obter_conexao()
  df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
  df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
  df_aportes = pd.read_sql_query("SELECT * FROM desafio_aportes", conexao)
  conexao.close()
except Exception:
  df_lancamentos = pd.DataFrame(
      columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
  )
  df_dividas = pd.DataFrame(columns=["id", "credor", "valor_total", "status"])
  df_aportes = pd.DataFrame(
      columns=["id", "data", "valor", "local_aplicacao"]
  )


def fmt_moeda(valor):
  return (
      f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  )


if menu == "Visão Geral / Painel":
  st.title("💰 Controle Financeiro - Sair do Vermelho")
  st.write("Aplicativo de controle total de créditos, débitos e investimentos.")

  st.subheader("Resumo do Mês e Visualização Gráfica")
  if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
    df_lancamentos["valor"] = pd.to_numeric(
        df_lancamentos["valor"], errors="coerce"
    ).fillna(0.0)

    total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"][
        "valor"
    ].sum()
    total_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"][
        "valor"
    ].sum()
    saldo = total_receitas - total_despesas

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

    # Gráficos interativos usando Plotly
    df_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"]
    if not df_despesas.empty:
      st.write("### Distribuição dos Gastos por Categoria")
      gasto_por_cat = (
          df_despesas.groupby("categoria")["valor"].sum().reset_index()
      )

      col_g1, col_g2 = st.columns(2)

      with col_g1:
        st.write("**Gráfico de Pizza**")
        fig1 = px.pie(
            gasto_por_cat,
            names="categoria",
            values="valor",
            hole=0.3,
            height=400,
        )
        fig1.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig1, use_container_width=True)

      with col_g2:
        st.write("**Gráfico de Barras**")
        fig2 = px.bar(
            gasto_por_cat,
            x="categoria",
            y="valor",
            text_auto=".2s",
            height=400,
            color="categoria",
        )
        fig2.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    else:
      st.info("Cadastre algumas despesas para visualizar os gráficos.")

    st.subheader("Histórico de Lançamentos")
    df_exibicao = df_lancamentos.tail(10).copy()
    df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
    st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
  else:
    st.info(
        "Nenhum lançamento registrado ainda. Utilize o menu lateral para"
        " cadastrar."
    )

  st.divider()
  st.subheader("⚠️ Mapeamento de Dívidas Ativas")
  if not df_dividas.empty:
    df_dividas_exibicao = df_dividas.copy()
    if "valor_total" in df_dividas_exibicao.columns:
      df_dividas_exibicao["valor_total"] = (
          pd.to_numeric(df_dividas_exibicao["valor_total"], errors="coerce")
          .fillna(0.0)
          .apply(fmt_moeda)
      )
    st.dataframe(df_dividas_exibicao.set_index("id"), use_container_width=True)
  else:
    st.info("Nenhuma dívida cadastrada no momento.")

elif menu == "Novo Lançamento / Aporte":
  st.title("➕ Central de Lançamentos e Aportes")

  aba_tipo = st.radio(
      "Escolha o tipo de registro:",
      ["Gasto ou Receita", "Registrar Aporte na Reserva"],
  )

  if aba_tipo == "Gasto ou Receita":
    st.subheader("Registrar Nova Receita ou Despesa")
    with st.form("form_lancamento"):
      data_l = st.text_input(
          "Data (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y")
      )
      tipo_l = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria_l = st.text_input(
          "Categoria (Ex: Aluguel, Alimentação, Salário)"
      )
      descricao_l = st.text_input("Descrição")
      valor_l = st.number_input(
          "Valor (R$)", min_value=0.01, step=10.0, format="%.2f"
      )

      if st.form_submit_button("Salvar Lançamento"):
        try:
          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              "INSERT INTO lancamentos (data, tipo, categoria, descricao,"
              " valor) VALUES (%s, %s, %s, %s, %s)",
              (
                  data_l,
                  tipo_l,
                  categoria_l,
                  descricao_l,
                  float(valor_l),
              ),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento salvo com sucesso!")
          st.rerun()
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")

  else:
    st.subheader("📥 Registrar Novo Depósito / Aporte na Reserva")
    st.write(
        "Ao registrar o aporte por aqui, o valor será somado ao seu Desafio de"
        " Reserva e lançado automaticamente como uma **Despesa/Saída** no"
        " seu fluxo de caixa, abatendo do seu saldo atual."
    )

    with st.form("form_aporte_integrado"):
      col_i1, col_i2 = st.columns(2)
      with col_i1:
        data_aporte_geral = st.text_input(
            "Data do Depósito (DD/MM/AAAA)",
            value=datetime.now().strftime("%d/%m/%Y"),
        )
      with col_i2:
        valor_aporte_geral = st.number_input(
            "Valor Depositado (R$)",
            min_value=1.0,
            value=100.00,
            step=10.0,
            format="%.2f",
        )

      locais_geral = [
          "Banco Itaú",
          "Nomad (Investimentos em Dólar)",
          "Sofisa Direto (CDB 105% CDI)",
          "Banco Inter (CDB Liquidez Diária)",
          "Nubank (Caixinha / RDB 100% CDI)",
          "Tesouro Selic (Tesouro Direto)",
          "Outro (Personalizado)",
      ]
      local_sel_geral = st.selectbox("Local da Aplicação", locais_geral)
      local_outro_geral = st.text_input(
          "Se selecionou 'Outro (Personalizado)' acima, digite o nome do Banco"
          " ou Corretora:"
      )

      if st.form_submit_button(
          "💾 Salvar Aporte (Atualiza Desafio e Abate do Saldo)"
      ):
        if local_sel_geral == "Outro (Personalizado)":
          local_final_geral = (
              local_outro_geral.strip() if local_outro_geral.strip() else "Outro"
          )
        else:
          local_final_geral = local_sel_geral

        try:
          datetime.strptime(data_aporte_geral.strip(), "%d/%m/%Y")
          conexao = obter_conexao()
          cursor = conexao.cursor()

          # 1. Salva na tabela do Desafio de Aportes
          cursor.execute(
              "INSERT INTO desafio_aportes (data, valor, local_aplicacao)"
              " VALUES (%s, %s, %s)",
              (
                  data_aporte_geral.strip(),
                  float(valor_aporte_geral),
                  local_final_geral,
              ),
          )

          # 2. Insere automaticamente como uma Despesa/Saída para abater do saldo principal
          cursor.execute(
              "INSERT INTO lancamentos (data, tipo, categoria, descricao,"
              " valor) VALUES (%s, %s, %s, %s, %s)",
              (
                  data_aporte_geral.strip(),
                  "Despesa",
                  "Investimento / Reserva",
                  f"Aporte: {local_final_geral}",
                  float(valor_aporte_geral),
              ),
          )

          conexao.commit()
          cursor.close()
          conexao.close()

          st.success(
              "Aporte registrado com sucesso! Adicionado ao desafio e abatido"
              " do saldo."
          )
          st.rerun()
        except ValueError:
          st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
          st.error(f"Erro ao salvar o aporte: {e}")

    # Exibir resumo dos aportes realizados
    if not df_aportes.empty:
      st.divider()
      st.subheader("📊 Saldos e Distribuição por Banco / Corretora")
      total_geral_aportes = df_aportes["valor"].sum()
      st.markdown(
          f"**Total Geral Guardado em Reservas:** {fmt_moeda(total_geral_aportes)}"
      )

      df_agrupado = (
          df_aportes.groupby("local_aplicacao")["valor"]
          .sum()
          .reset_index()
      )
      df_agrupado["% do Total"] = (
          (df_agrupado["valor"] / total_geral_aportes) * 100
      ).apply(lambda x: f"{x:.1f}%")
      df_agrupado["valor"] = df_agrupado["valor"].apply(fmt_moeda)
      df_agrupado.columns = [
          "Instituição / Local",
          "Valor Acumulado",
          "% do Total",
      ]
      st.dataframe(df_agrupado, use_container_width=True)

elif menu == "Gerenciar Lançamentos":
  st.title("🛠️ Gerenciar Lançamentos Existentes")
  if not df_lancamentos.empty:
    st.write(
        "Selecione um lançamento abaixo para excluir caso tenha cadastrado"
        " errado:"
    )
    id_para_excluir = st.selectbox(
        "ID do Lançamento", df_lancamentos["id"].tolist()
    )

    if st.button("Excluir Lançamento Selecionado"):
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM lancamentos WHERE id = %s", (int(id_para_excluir),)
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success(
            f"Lançamento de ID {id_para_excluir} excluído com sucesso!"
        )
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao excluir: {e}")

    st.dataframe(
        df_lancamentos.set_index("id").applymap(
            lambda x: fmt_moeda(x) if isinstance(x, (int, float)) else x
        ),
        use_container_width=True,
    )
  else:
    st.info("Nenhum lançamento para gerenciar.")