from datetime import datetime
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Controle Financeiro Pro", page_icon="💰", layout="wide"
)

def obter_conexao():
    """Retorna a conexão com a base de dados PostgreSQL centralizada nos secrets."""
    return psycopg2.connect(st.secrets["DATABASE_URL"])

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

# Carregar dados do PostgreSQL para DataFrames do Pandas de forma robusta
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
    
    # Tenta carregar aportes com fallback para nomes alternativos
    try:
        df_aportes = pd.read_sql_query("SELECT * FROM aportes", conexao)
    except Exception:
        try:
            df_aportes = pd.read_sql_query("SELECT * FROM investimentos", conexao)
        except Exception:
            df_aportes = pd.DataFrame(columns=["id", "data", "local_aplicacao", "descricao", "valor"])

    df_dividas = pd.read_sql_query("SELECT * FROM dividas", conexao)
    conexao.close()
except Exception:
    df_lancamentos = pd.DataFrame(
        columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
    )
    df_aportes = pd.DataFrame(
        columns=["id", "data", "local_aplicacao", "descricao", "valor"]
    )
    df_dividas = pd.DataFrame(
        columns=["id", "credor", "valor_total", "juros_mensal", "status"]
    )

# Tratamento numérico rigoroso para aportes globalmente
if not df_aportes.empty and "valor" in df_aportes.columns:
    df_aportes["valor"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    total_aportes = df_aportes["valor"].sum()
else:
    total_aportes = 0.0

def fmt_moeda(valor):
    return (
        f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


if menu == "📊 Painel & Gráficos":
    st.title("💰 Controle Financeiro - Sair do Vermelho")
    st.write(
        "Aplicativo unificado de controle de créditos, débitos e investimentos."
    )

    # Tratamento flexível para capturar receitas e despesas independentemente de maiúsculas/minúsculas
    if not df_lancamentos.empty and "valor" in df_lancamentos.columns:
        df_lancamentos["valor"] = pd.to_numeric(
            df_lancamentos["valor"], errors="coerce"
        ).fillna(0.0)
        df_lancamentos["tipo_clean"] = df_lancamentos["tipo"].str.strip().str.lower()
    else:
        df_lancamentos = pd.DataFrame(
            columns=["id", "data", "tipo", "categoria", "descricao", "valor"]
        )
        df_lancamentos["tipo_clean"] = ""

    total_receitas = (
        df_lancamentos[df_lancamentos["tipo_clean"].isin(["receita", "crédito", "credito", "entrada"])]["valor"].sum()
        if not df_lancamentos.empty
        else 0.0
    )

    total_gastos = (
        df_lancamentos[df_lancamentos["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])]["valor"].sum()
        if not df_lancamentos.empty
        else 0.0
    )

    # Saldo Atual da Conta Corrente: Entradas menos Gastos Comuns menos Aportes Realizados
    saldo = total_receitas - total_gastos - total_aportes

    st.subheader("Resumo do Mês e Visualização Gráfica")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Entradas", fmt_moeda(total_receitas))
    col2.metric("Gastos Comuns", fmt_moeda(total_gastos))
    col3.metric("Total em Aportes", fmt_moeda(total_aportes))

    if saldo >= 0:
        col4.metric("Saldo Atual", fmt_moeda(saldo), delta="No Azul 💙")
    else:
        col4.metric(
            "Saldo Atual",
            fmt_moeda(saldo),
            delta="No Vermelho 🔴",
            delta_color="inverse",
        )

    st.divider()

    st.subheader("Distribuição de Gastos e Investimentos (Visão Consolidada)")

    df_gastos_grafico = (
        df_lancamentos[df_lancamentos["tipo_clean"].isin(["despesa", "débito", "debito", "saida"])].copy()
        if not df_lancamentos.empty
        else pd.DataFrame()
    )

    if not df_aportes.empty:
        df_ap_graf = pd.DataFrame()
        df_ap_graf["categoria"] = ["Investimentos"] * len(df_aportes)
        df_ap_graf["valor"] = df_aportes["valor"]
        df_gastos_grafico = pd.concat(
            [df_gastos_grafico, df_ap_graf], ignore_index=True
        )

    if not df_gastos_grafico.empty and "valor" in df_gastos_grafico.columns:
        df_cat = (
            df_gastos_grafico.groupby("categoria")["valor"].sum().reset_index()
        )

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
            fig_pizza.update_traces(textposition="inside", textinfo="percent+label")
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
        st.info("Nenhum registro encontrado para gerar gráficos.")

    st.divider()
    st.subheader("Histórico Geral de Lançamentos")
    if not df_lancamentos.empty:
        df_exibicao = df_lancamentos.tail(10).copy()
        if "tipo_clean" in df_exibicao.columns:
            df_exibicao = df_exibicao.drop(columns=["tipo_clean"])
        df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_moeda)
        st.dataframe(df_exibicao.set_index("id"), use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado.")

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
                        "INSERT INTO lancamentos (data, tipo, categoria, descricao, valor) VALUES (%s, %s, %s, %s, %s)",
                        (data_l, tipo_l, categoria_l, descricao_l, float(valor_l)),
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
            "Este aporte será guardado na tabela de investimentos e abatido do"
            " saldo final da conta."
        )

        locais_geral = [
            "Banco Itaú",
            "Nomad (Investimentos em Dólar)",
            "Sofisa Direto (CDB 105% CDI)",
            "Banco Inter (CDB Liquidez Diária)",
            "Nubank (Caixinha / RDB 100% CDI)",
            "Tesouro Selic (Tesouro Direto)",
            "Banco XP / Rico (CDB ou LCI)",
            "Outro (Personalizado)",
        ]

        local_sel = st.selectbox("Local da Aplicação", locais_geral)
        local_outro = (
            st.text_input("Digite o nome do Banco ou Corretora personalizado:")
            if local_sel == "Outro (Personalizado)"
            else ""
        )

        with st.form("form_aporte_tabela"):
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

            descricao_aporte = st.text_input(
                "Descrição Opcional", value="Aporte para Reserva de Emergência"
            )

            if st.form_submit_button("💾 Salvar Aporte"):
                local_final = (
                    local_outro.strip()
                    if local_sel == "Outro (Personalizado)" and local_outro.strip()
                    else (local_sel if local_sel != "Outro (Personalizado)" else "Outro")
                )

                try:
                    datetime.strptime(data_aporte.strip(), "%d/%m/%Y")
                    conexao = obter_conexao()
                    cursor = conexao.cursor()
                    cursor.execute(
                        "INSERT INTO aportes (data, local_aplicacao, descricao, valor) VALUES (%s, %s, %s, %s)",
                        (
                            data_aporte.strip(),
                            local_final,
                            descricao_aporte,
                            float(valor_aporte),
                        ),
                    )
                    conexao.commit()
                    cursor.close()
                    conexao.close()
                    st.success("Aporte registado e abatido do saldo com sucesso!")
                    st.rerun()
                except ValueError:
                    st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

elif menu == "📋 Gerenciar Lançamentos":
    st.title("📋 Gerenciamento Geral de Lançamentos e Aportes")

    aba_ger = st.radio(
        "O que deseja gerenciar?", ["Lançamentos (Comuns)", "Aportes / Investimentos"]
    )

    if aba_ger == "Lançamentos (Comuns)":
        if not df_lancamentos.empty and "id" in df_lancamentos.columns:
            ids_lanc = df_lancamentos["id"].tolist()
            id_sel = st.selectbox(
                "Selecione o Lançamento para Editar ou Excluir", ids_lanc
            )

            if id_sel:
                lan_sel = df_lancamentos[df_lancamentos["id"] == id_sel].iloc[0]
                with st.form("form_ger_lanc"):
                    tipo_g = st.selectbox(
                        "Tipo",
                        ["Despesa", "Receita"],
                        index=0 if str(lan_sel["tipo"]).strip().lower() == "despesa" else 1,
                    )
                    cat_g = st.text_input("Categoria", value=str(lan_sel["categoria"]))
                    desc_g = st.text_input("Descrição", value=str(lan_sel["descricao"]))
                    val_g = st.number_input("Valor (R$)", value=float(lan_sel["valor"]))
                    data_g = st.text_input("Data", value=str(lan_sel["data"]))

                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        btn_salvar = st.form_submit_button("Salvar Alterações")
                    with col_g2:
                        btn_excluir = st.form_submit_button("🗑️ Excluir Lançamento")

                    if btn_salvar:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute(
                            "UPDATE lancamentos SET tipo = %s, categoria = %s, descricao = %s, valor = %s, data = %s WHERE id = %s",
                            (
                                tipo_g,
                                cat_g.strip(),
                                desc_g.strip(),
                                float(val_g),
                                data_g.strip(),
                                int(id_sel),
                            ),
                        )
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Atualizado com sucesso!")
                        st.rerun()

                    if btn_excluir:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (int(id_sel),))
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Excluído com sucesso!")
                        st.rerun()
        else:
            st.info("Nenhum lançamento comum registado.")
    else:
        if not df_aportes.empty and "id" in df_aportes.columns:
            ids_ap = df_aportes["id"].tolist()
            id_ap_sel = st.selectbox(
                "Selecione o Aporte para Editar ou Excluir", ids_ap
            )

            if id_ap_sel:
                ap_sel = df_aportes[df_aportes["id"] == id_ap_sel].iloc[0]
                with st.form("form_ger_ap"):
                    loc_g = st.text_input(
                        "Local da Aplicação", value=str(ap_sel["local_aplicacao"])
                    )
                    desc_ap_g = st.text_input(
                        "Descrição", value=str(ap_sel["descricao"])
                    )
                    val_ap_g = st.number_input(
                        "Valor (R$)", value=float(ap_sel["valor"])
                    )
                    data_ap_g = st.text_input("Data", value=str(ap_sel["data"]))

                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        btn_salvar_ap = st.form_submit_button("Salvar Alterações")
                    with col_a2:
                        btn_excluir_ap = st.form_submit_button("🗑️ Excluir Aporte")

                    if btn_salvar_ap:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute(
                            "UPDATE aportes SET local_aplicacao = %s, descricao = %s, valor = %s, data = %s WHERE id = %s",
                            (
                                loc_g.strip(),
                                desc_ap_g.strip(),
                                float(val_ap_g),
                                data_ap_g.strip(),
                                int(id_ap_sel),
                            ),
                        )
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Aporte atualizado com sucesso!")
                        st.rerun()

                    if btn_excluir_ap:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM aportes WHERE id = %s", (int(id_ap_sel),))
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Aporte excluído com sucesso!")
                        st.rerun()
        else:
            st.info("Nenhum aporte registado.")

elif menu == "🎯 Desafio Reserva / Aportes":
    st.title("🎯 Painel Consolidado de Reservas e Aportes")

    if not df_aportes.empty:
        total_guardado = df_aportes["valor"].sum()
        st.metric("Total Geral Guardado em Reservas", fmt_moeda(total_guardado))

        st.subheader("📊 Distribuição por Banco / Corretora")
        if "local_aplicacao" in df_aportes.columns:
            df_resumo = (
                df_aportes.groupby("local_aplicacao")["valor"].sum().reset_index()
            )
            df_resumo["% do Total"] = (
                (df_resumo["valor"] / total_guardado) * 100
            ).apply(lambda x: f"{x:.1f}%")
            df_resumo["Valor Acumulado"] = df_resumo["valor"].apply(fmt_moeda)
            df_tabela = df_resumo[
                ["local_aplicacao", "Valor Acumulado", "% do Total"]
            ].rename(columns={"local_aplicacao": "Instituição / Local"})
            st.dataframe(df_tabela, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📋 Histórico de Aportes Registrados")
        df_exibe_ap = df_aportes.copy()
        if "valor" in df_exibe_ap.columns:
            df_exibe_ap["valor"] = df_exibe_ap["valor"].apply(fmt_moeda)

        if "id" in df_exibe_ap.columns:
            st.dataframe(
                df_exibe_ap.rename(
                    columns={
                        "data": "Data",
                        "local_aplicacao": "Local",
                        "descricao": "Descrição",
                        "valor": "Valor",
                    }
                ).set_index("id"),
                use_container_width=True,
            )
        else:
            st.dataframe(df_exibe_ap, use_container_width=True)
    else:
        st.info(
            "Nenhum aporte registado na tabela dedicada a investimentos ainda."
        )

elif menu == "⚠️ Raio-X de Dívidas":
    st.title("⚠️ Raio-X de Dívidas Ativas")
    if not df_dividas.empty and "id" in df_dividas.columns:
        st.dataframe(df_dividas.set_index("id"), use_container_width=True)
    elif not df_dividas.empty:
        st.dataframe(df_dividas, use_container_width=True)
    else:
        st.info("Nenhuma dívida cadastrada no momento.")

elif menu == "💡 Orientação & Investimentos":
    st.title("💡 Orientação e Estratégias de Investimento")
    st.write(
        "Aqui você encontra orientações para organizar suas finanças e fazer sua"
        " reserva de emergência render com segurança."
    )