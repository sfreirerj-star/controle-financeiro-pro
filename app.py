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


# Inicializar as tabelas do banco de dados
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
    st.error(f"Erro ao conectar com o banco de dados no Supabase: {e}")
    st.stop()


inicializar_banco()

menu = st.sidebar.selectbox(
    "Menu Principal",
    [
        "📊 Painel & Gráficos",
        "➕ Novo Lançamento",
        "📋 Gerenciar Lançamentos",
        "🎯 Desafio Reserva / Aportes",
        "⚠️ Raio-X de Dívidas",
        "💡 Orientação & Investimentos",
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
  df_dividas = pd.DataFrame(
      columns=["id", "credor", "valor_total", "juros_mensal", "status"]
  )
  df_aportes = pd.DataFrame(
      columns=["id", "data", "valor", "local_aplicacao"]
  )


def fmt_moeda(valor):
  return (
      f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
  )


if menu == "📊 Painel & Gráficos":
  st.title("💰 Controle Financeiro - Sair do Vermelho")
  st.write("Aplicativo de controle total de créditos, débitos e investimentos.")

  if not df_lancamentos.empty or not df_aportes.empty:
    if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
      df_lancamentos["valor"] = pd.to_numeric(
          df_lancamentos["valor"], errors="coerce"
      ).fillna(0.0)
    else:
      df_lancamentos = pd.DataFrame(
          columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
      )

    if not df_aportes.empty and "valor" in df_aportes.columns:
      df_aportes["valor"] = pd.to_numeric(
          df_aportes["valor"], errors="coerce"
      ).fillna(0.0)
    else:
      df_aportes = pd.DataFrame(columns=["id", "data", "valor", "local_aplicacao"])

    total_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"][
        "valor"
    ].sum()
    total_despesas_comuns = df_lancamentos[
        df_lancamentos["tipo"] == "Despesa"
    ]["valor"].sum()
    total_aportes = df_aportes["valor"].sum()

    # Saídas totais incluem despesas comuns + investimentos/aportes feitos na conta
    total_saidas = total_despesas_comuns + total_aportes
    saldo = total_receitas - total_saidas

    st.subheader("Resumo do Mês e Visualização Gráfica")
    col1, col2, col3 = st.columns(3)
    col1.metric("Entradas", fmt_moeda(total_receitas))
    col2.metric("Saídas", fmt_moeda(total_saidas))

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

    st.subheader("Distribuição dos Gastos e Investimentos por Categoria")

    # Unificar despesas comuns e aportes para visualização completa nos gráficos
    df_despesas_comuns = df_lancamentos[
        df_lancamentos["tipo"] == "Despesa"
    ].copy()
    if not df_aportes.empty:
      df_aportes_virtual = pd.DataFrame({
          "categoria": ["Investimento / Reserva"] * len(df_aportes),
          "valor": df_aportes["valor"],
      })
      df_grafico = pd.concat(
          [df_despesas_comuns[["categoria", "valor"]], df_aportes_virtual],
          ignore_index=True,
      )
    else:
      df_grafico = df_despesas_comuns[["categoria", "valor"]]

    if not df_grafico.empty:
      df_cat = df_grafico.groupby("categoria")["valor"].sum().reset_index()

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
        fig_pizza.update_traces(
            textposition="inside", textinfo="percent+label"
        )
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
        fig_barras.update_traces(
            texttemplate="R$ %{text:.2f}", textposition="outside"
        )
        fig_barras.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_barras, use_container_width=True)
    else:
      st.info("Nenhuma despesa ou aporte registrado para gerar gráficos.")

    st.divider()
    st.subheader("Histórico de Lançamentos Comuns")
    if not df_lancamentos.empty:
      df_exibicao = df_lancamentos.tail(10).copy()
      df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
      st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
    else:
      st.info("Nenhum lançamento comum registrado.")
  else:
    st.info("Nenhum registro encontrado.")

elif menu == "➕ Novo Lançamento":
  st.title("➕ Central de Lançamentos e Aportes")

  tipo_registro = st.radio(
      "O que deseja registrar?",
      ["Gasto ou Receita Comum", "Aporte / Investimento na Reserva"],
  )

  if tipo_registro == "Gasto ou Receita Comum":
    st.subheader("Registrar Nova Receita ou Despesa")
    with st.form("form_comum"):
      data_l = st.text_input(
          "Data (DD/MM/AAAA)", value=datetime.now().strftime("%d/%m/%Y")
      )
      tipo_l = st.selectbox("Tipo", ["Despesa", "Receita"])
      categoria_l = st.text_input("Categoria (Ex: Aluguel, Alimentação)")
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
        "Ao salvar por aqui, o valor será somado ao seu Desafio e abatido"
        " automaticamente do seu saldo em conta corrente."
    )

    with st.form("form_aporte_integrado"):
      col_i1, col_i2 = st.columns(2)
      with col_i1:
        data_aporte = st.text_input(
            "Data do Depósito (DD/MM/AAAA)",
            value=datetime.now().strftime("%d/%m/%Y"),
        )
      with col_i2:
        valor_aporte = st.number_input(
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
      local_sel = st.selectbox("Local da Aplicação", locais_geral)
      local_outro = st.text_input(
          "Especifique o Banco / Corretora (Preencha caso tenha selecionado"
          " 'Outro')"
      )

      if st.form_submit_button("💾 Salvar Aporte no Desafio"):
        if local_sel == "Outro (Personalizado)":
          local_final = local_outro.strip() if local_outro.strip() else "Outro"
        else:
          local_final = local_sel

        try:
          datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
          conexao = obter_conexao()
          cursor = conexao.cursor()

          cursor.execute(
              "INSERT INTO desafio_aportes (data, valor, local_aplicacao)"
              " VALUES (%s, %s, %s)",
              (
                  data_aporte.strip(),
                  float(valor_aporte),
                  local_final,
              ),
          )

          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Aporte registrado com sucesso e saldo atualizado!")
          st.rerun()
        except ValueError:
          st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
        except Exception as e:
          st.error(f"Erro ao salvar: {e}")

elif menu == "📋 Gerenciar Lançamentos":
  st.title("📋 Gerenciamento de Lançamentos Comuns")
  if not df_lancamentos.empty:
    ids_lanc = df_lancamentos["id"].tolist()
    id_sel = st.selectbox("Selecione o Lançamento para Editar ou Excluir", ids_lanc)

    if id_sel:
      lan_sel = df_lancamentos[df_lancamentos["id"] == id_sel].iloc[0]
      with st.form("form_gerenciar_lancamento"):
        st.write(f"Editando Lançamento ID: {id_sel}")
        cat_g = st.text_input("Categoria", value=str(lan_sel["categoria"]))
        desc_g = st.text_input("Descrição", value=str(lan_sel["descricao"]))
        val_g = st.number_input("Valor (R$)", value=float(lan_sel["valor"]))
        data_g = st.text_input("Data", value=str(lan_sel["data"]))

        col_g1, col_g2 = st.columns(2)
        with col_g1:
          btn_salvar_g = st.form_submit_button("Salvar Alterações")
        with col_g2:
          btn_excluir_g = st.form_submit_button("🗑️ Excluir Lançamento")

        if btn_excluir_g:
          try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "DELETE FROM lancamentos WHERE id = %s", (int(id_sel),)
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Lançamento excluído com sucesso!")
            st.rerun()
          except Exception as e:
            st.error(f"Erro ao excluir: {e}")
  else:
    st.info("Nenhum lançamento comum para gerenciar.")

elif menu == "🎯 Desafio Reserva / Aportes":
  st.title("🎯 Gerenciamento do Desafio de Reserva")

  if not df_aportes.empty:
    df_aportes["valor_num"] = (
        pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    )
    total_guardado = df_aportes["valor_num"].sum()

    st.metric("Total Geral Guardado em Reservas", fmt_moeda(total_guardado))

    st.subheader("📊 Distribuição por Banco / Corretora")
    df_resumo = (
        df_aportes.groupby("local_aplicacao")["valor_num"].sum().reset_index()
    )
    df_resumo["% do Total"] = (
        (df_resumo["valor_num"] / total_guardado) * 100
    ).apply(lambda x: f"{x:.1f}%")
    df_resumo["Valor Acumulado"] = df_resumo["valor_num"].apply(fmt_moeda)
    df_tabela = df_resumo[
        ["local_aplicacao", "Valor Acumulado", "% do Total"]
    ].rename(columns={"local_aplicacao": "Instituição / Local"})
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🛠️ Editar ou Excluir Aportes Registrados")
    ids_aportes = df_aportes["id"].tolist()
    aporte_id_sel = st.selectbox(
        "Selecione o ID do Aporte para Corrigir ou Excluir", ids_aportes
    )

    if aporte_id_sel:
      ap_sel = df_aportes[df_aportes["id"] == aporte_id_sel].iloc[0]
      with st.form("form_editar_aporte"):
        st.write(f"Editando Aporte ID: {aporte_id_sel}")
        novo_local = st.text_input(
            "Nome do Banco / Corretora", value=str(ap_sel["local_aplicacao"])
        )
        novo_valor = st.number_input(
            "Valor (R$)", value=float(ap_sel["valor_num"])
        )
        nova_data = st.text_input("Data", value=str(ap_sel["data"]))

        col_a1, col_a2 = st.columns(2)
        with col_a1:
          btn_salvar_ap = st.form_submit_button("Salvar Alterações do Aporte")
        with col_a2:
          btn_excluir_ap = st.form_submit_button("🗑️ Excluir Aporte")

        if btn_salvar_ap:
          try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE desafio_aportes SET local_aplicacao = %s, valor = %s,"
                " data = %s WHERE id = %s",
                (
                    novo_local.strip(),
                    float(novo_valor),
                    nova_data.strip(),
                    int(aporte_id_sel),
                ),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Aporte atualizado com sucesso!")
            st.rerun()
          except Exception as e:
            st.error(f"Erro ao atualizar aporte: {e}")

        if btn_excluir_ap:
          try:
            conexao = obter_conexao()
            cursor = conexao.cursor()
            cursor.execute(
                "DELETE FROM desafio_aportes WHERE id = %s",
                (int(aporte_id_sel),),
            )
            conexao.commit()
            cursor.close()
            conexao.close()
            st.success("Aporte excluído com sucesso e saldo restituído!")
            st.rerun()
          except Exception as e:
            st.error(f"Erro ao excluir aporte: {e}")
  else:
    st.info("Nenhum aporte registrado ainda.")

elif menu == "⚠️ Raio-X de Dívidas":
  st.title("⚠️ Raio-X de Dívidas Ativas")
  if not df_dividas.empty:
    st.dataframe(df_dividas.set_index("id"), use_container_width=True)
  else:
    st.info("Nenhuma dívida cadastrada no momento.")

elif menu == "💡 Orientação & Investimentos":
  st.title("💡 Orientação e Estratégias de Investimento")
  st.write(
      "Aqui você encontra orientações para organizar suas finanças e fazer sua"
      " reserva de emergência render com segurança."
  )
