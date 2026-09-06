from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Desafio Reserva & Investimentos", page_icon="🎯", layout="wide"
)


def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


def garantir_tabelas():
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


garantir_tabelas()

st.subheader("🎯 Desafio Personalizado & Gestão de Portfólio")
st.write(
    "Controle seus aportes mensais, diversifique suas instituições financeiras e acompanhe seus saldos por local de aplicação."
)


def fmt_moeda(v):
    return (
        f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


# Criando abas para separar a gestão do desafio e a consultoria de investimentos
aba_desafio, aba_orientacao = st.tabs(
    ["🎯 Meu Desafio & Aportes", "📈 Consultoria Diária de Investimentos (Moderado)"]
)

# --- ABA 1: MEU DESAFIO E APORTES ---
with aba_desafio:
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

    # Buscar aportes do banco
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
            locais_disponiveis = [
                "Sofisa Direto (CDB 105% CDI)",
                "Banco Inter (CDB Liquidez Diária)",
                "Nubank (Caixinha / RDB 100% CDI)",
                "Tesouro Selic (Tesouro Direto)",
                "Banco XP / Rico (CDB ou LCI)",
                "Outro (Personalizado)",
            ]
            local_selecionado = st.selectbox(
                "Local da Aplicação", locais_disponiveis
            )

        # Se escolher outro, permite digitar
        local_aporte = local_selecionado
        if local_selecionado == "Outro (Personalizado)":
            local_aporte = st.text_input("Especifique o Banco / Corretora")

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
                st.success("Aporte registrado com sucesso!")
                st.rerun()
            except ValueError:
                st.error("Data inválida. Utilize o formato DD/MM/AAAA.")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.divider()

    # --- SALDO POR INSTITUIÇÃO (DIVERSIFICAÇÃO) ---
    st.markdown("### 🏦 Saldo e Distribuição por Banco / Corretora")
    if not df_aportes.empty:
        df_resumo_bancos = (
            df_aportes.groupby("local_aplicacao")["valor_num"]
            .sum()
            .reset_index()
        )
        df_resumo_bancos["Valor Acumulado"] = df_resumo_bancos[
            "valor_num"
        ].apply(fmt_moeda)
        df_resumo_bancos["% do Total"] = (
            (df_resumo_bancos["valor_num"] / total_guardado) * 100
        ).apply(lambda x: f"{x:.1f}%")

        df_tabela_bancos = df_resumo_bancos[
            ["local_aplicacao", "Valor Acumulado", "% do Total"]
        ].rename(columns={"local_aplicacao": "Instituição / Local"})
        st.dataframe(
            df_tabela_bancos, use_container_width=True, hide_index=True
        )
    else:
        st.info(
            "Nenhuma aplicação registrada para calcular a distribuição por banco ainda."
        )

    st.divider()

    st.markdown("### 📊 Extrato de Aportes Realizados")
    if not df_aportes.empty:
        df_tabela_final = df_aportes[
            ["id", "data", "local_aplicacao", "valor_num"]
        ].rename(
            columns={
                "local_aplicacao": "Local da Aplicação",
                "valor_num": "Valor",
            }
        )
        df_tabela_final["Valor"] = df_tabela_final["Valor"].apply(fmt_moeda)
        st.dataframe(
            df_tabela_final.set_index("id"), use_container_width=True, height=180
        )

        if st.button("🗑️ Excluir Último Aporte Registrado"):
            try:
                ultimo_id = df_aportes["id"].max()
                conexao = obter_conexao()
                cursor = conexao.cursor()
                cursor.execute(
                    "DELETE FROM desafio_aportes WHERE id = %s",
                    (int(ultimo_id),),
                )
                conexao.commit()
                cursor.close()
                conexao.close()
                st.warning("Último aporte removido com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
    else:
        st.info("Nenhum aporte registrado ainda.")

# --- ABA 2: CONSULTORIA DIÁRIA DE INVESTIMENTOS (MODERADO) ---
with aba_orientacao:
    st.markdown(
        "### 📈 Painel Diário de Alocação & Mercado (Perfil Moderado)"
    )
    st.write(
        "Opções recomendadas no mercado financeiro para diversificação segura e rentável:"
    )

    col_inf1, col_inf2, col_inf3 = st.columns(3)
    with col_inf1:
        st.metric(
            "Retorno Médio Esperado", "105% a 110% CDI", delta="Pós-fixado"
        )
    with col_inf2:
        st.metric(
            "Segurança Coberta", "FGC & Tesouro Nacional", delta="Garantido"
        )
    with col_inf3:
        st.metric("Liquidez Principal", "Diária (D+0)", delta="Resgate Imediato")

    st.markdown("#### 🏦 Melhores Opções de Bancos e Corretoras no Mercado")

    data_instituicoes = {
        "Instituição / Corretora": [
            "Sofisa Direto",
            "Banco Inter",
            "Tesouro Direto",
            "XP / Rico / Clear",
        ],
        "Produto Recomendado": [
            "CDB Liquidez Diária (105% CDI)",
            "CDB Mais Limite / Liquidez Diária",
            "Tesouro Selic 2029 / 2031",
            "LCIs / LCAs com Liquidez (Isentas de IR)",
        ],
        "Vantagem para Reserva": [
            "Excelente taxa para pós-fixado com FGC",
            "Praticidade e solidez de banco múltiplo",
            "Segurança soberana máxima do governo",
            "Isenção de Imposto de Renda em LCIs",
        ],
    }
    st.dataframe(
        pd.DataFrame(data_instituicoes), use_container_width=True, hide_index=True
    )

    st.markdown("#### 💡 Estratégia de Diversificação (Regra dos Ovos)")
    st.info(
        "📌 **Dica de Ouro:** Dividir os aportes entre 2 ou 3 instituições diferentes (por exemplo, um pouco no Sofisa Direto e um pouco no Inter ou Tesouro) protege seu patrimônio, garante que você aproveite taxas promocionais distintas e mantém o valor total sempre dentro do limite de cobertura do FGC (R$ 250 mil por instituição)."
    )
