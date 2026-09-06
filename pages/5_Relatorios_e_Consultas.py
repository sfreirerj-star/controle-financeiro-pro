from datetime import datetime
import urllib.parse
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Relatórios e Consultas", page_icon="📈", layout="wide")

def obter_conexao():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

st.subheader("📈 Relatórios, Consultas e Fechamento de Mês")
st.write("Filtre seus lançamentos detalhadamente, gerencie registros, exporte relatórios e acompanhe o fechamento mês a mês.")

# Carregar todos os lançamentos do banco
try:
    conexao = obter_conexao()
    df_lancamentos = pd.read_sql_query("SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC", conexao)
    conexao.close()
except Exception as e:
    st.error(f"Erro ao carregar lançamentos: {e}")
    df_lancamentos = pd.DataFrame()

if not df_lancamentos.empty:
    df_lancamentos["data_dt"] = pd.to_datetime(df_lancamentos["data"], format="%d/%m/%Y", errors="coerce")
    
    aba1, aba2 = st.tabs(["🔍 Consulta, Filtros e Ações", "📅 Fechamento de Mês (Saldo Remanescente)"])

    # --- ABA 1: CONSULTA, FILTROS E AÇÕES ---
    with aba1:
        st.markdown("### 🔎 Filtrar Lançamentos")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            tipos_disponiveis = ["Todos"] + list(df_lancamentos["tipo"].dropna().unique())
            filtro_tipo = st.selectbox("Filtrar por Tipo", tipos_disponiveis)
            
        with col_f2:
            categorias_disponiveis = sorted(list(df_lancamentos["categoria"].dropna().unique()))
            filtro_categorias = st.multiselect("Filtrar por Categoria(s)", categorias_disponiveis, default=[])
            
        with col_f3:
            filtro_texto = st.text_input("Buscar na Descrição (Palavra-chave)")

        # Aplicação dos filtros
        df_filtrado = df_lancamentos.copy()
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]
            
        if filtro_categorias:
            df_filtrado = df_filtrado[df_filtrado["categoria"].isin(filtro_categorias)]
            
        if filtro_texto:
            df_filtrado = df_filtrado[df_filtrado["descricao"].str.contains(filtro_texto, case=False, na=False)]

        def fmt_moeda(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        df_exibicao = df_filtrado.copy()
        df_exibicao["valor_num"] = pd.to_numeric(df_exibicao["valor"], errors="coerce").fillna(0.0)
        df_exibicao["valor"] = df_exibicao["valor_num"].apply(fmt_moeda)
        
        colunas_mostrar = ["id", "data", "tipo", "categoria", "descricao", "valor"]
        
        # Tabela perfeitamente alinhada com largura total e altura fixa (5 registros + barra de rolagem)
        st.dataframe(
            df_exibicao[colunas_mostrar].set_index("id"), 
            use_container_width=True,
            height=210
        )
        
        total_filtrado = df_exibicao["valor_num"].sum()
        cat_str = ", ".join(filtro_categorias) if filtro_categorias else "Todas"
        st.info(f"📊 **Total dos lançamentos filtrados:** {fmt_moeda(total_filtrado)}")

        # --- BOTÕES DE EXPORTAÇÃO E IMPRESSÃO (EXatamente ABAIXO DA TABELA E DO TOTAL) ---
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            csv_data = df_exibicao[colunas_mostrar].to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar Relatório (CSV / Excel)",
                data=csv_data,
                file_name="relatorio_lancamentos.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_exp2:
            html_tabela = df_exibicao[colunas_mostrar].to_html(index=False, classes="table table-striped")
            html_code = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Relatório de Lançamentos</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
        h2 {{ color: #111; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 14px; }}
        th {{ background-color: #f5f5f5; }}
        .total {{ margin-top: 20px; font-weight: bold; font-size: 18px; }}
    </style>
</head>
<body>
    <h2>Relatório de Lançamentos - Sistema Financeiro</h2>
    <p><b>Filtro Aplicado:</b> Tipo ({filtro_tipo}) | Categorias ({cat_str})</p>
    {html_tabela}
    <div class="total">Total Filtrado: {fmt_moeda(total_filtrado)}</div>
    <script>
        window.onload = function() {{ window.print(); }}
    </script>
</body>
</html>"""
            
            # Codificação segura da URL para evitar vazamentos de código na tela
            html_encoded = urllib.parse.quote(html_code)
            
            st.markdown(
                f"""
                <a href="data:text/html;charset=utf-8,{html_encoded}" target="_blank" style="text-decoration: none; display: block; width: 100%;">
                    <div style="background-color: #ff4b4b; color: white; text-align: center; padding: 10px 18px; border-radius: 4px; font-weight: bold; cursor: pointer; width: 100%;">
                        🖨️ Imprimir / Salvar Relatório em PDF
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )

        st.divider()

        # --- SEÇÃO DE EDIÇÃO E EXCLUSÃO RÁPIDA NA CONSULTA ---
        st.markdown("### ✏️ Gerenciar Lançamento Filtrado (Editar ou Excluir)")
        if not df_filtrado.empty:
            df_filtrado["resumo_acao"] = "ID: " + df_filtrado["id"].astype(str) + " | " + df_filtrado["data"] + " | " + df_filtrado["categoria"] + " | " + df_filtrado["descricao"].fillna("")
            
            lanc_sel = st.selectbox("Selecione o lançamento para alterar ou excluir:", df_filtrado["resumo_acao"].tolist())
            id_sel = int(lanc_sel.split(" | ")[0].replace("ID: ", ""))
            dado_reg = df_filtrado[df_filtrado["id"] == id_sel].iloc[0]

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                with st.form("form_edicao_relatorio"):
                    st.markdown("#### Corrigir Registro")
                    ntipo = st.selectbox("Tipo", ["Despesa", "Receita"], index=0 if dado_reg["tipo"] == "Despesa" else 1)
                    ncateg = st.text_input("Categoria", value=dado_reg["categoria"])
                    ndesc = st.text_input("Descrição", value=dado_reg["descricao"])
                    nval = st.number_input("Valor (R$)", value=float(dado_reg["valor"]), format="%.2f")
                    ndata = st.text_input("Data (DD/MM/AAAA)", value=dado_reg["data"])

                    if st.form_submit_button("Salvar Alterações"):
                        try:
                            datetime.strptime(ndata.strip(), "%d/%m/%Y")
                            conexao = obter_conexao()
                            cursor = conexao.cursor()
                            cursor.execute(
                                "UPDATE lancamentos SET data = %s, tipo = %s, categoria = %s, descricao = %s, valor = %s WHERE id = %s",
                                (ndata.strip(), ntipo, ncateg, ndesc, nval, id_sel)
                            )
                            conexao.commit()
                            cursor.close()
                            conexao.close()
                            st.success("Atualizado com sucesso!")
                            st.rerun()
                        except ValueError:
                            st.error("Data inválida. Use DD/MM/AAAA.")
                        except Exception as e:
                            st.error(f"Erro: {e}")

            with col_a2:
                st.markdown("#### Excluir Registro")
                st.warning("Atenção: Essa operação apagará o registro permanentemente.")
                if st.button("Excluir Lançamento Selecionado", type="primary"):
                    try:
                        conexao = obter_conexao()
                        cursor = conexao.cursor()
                        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (id_sel,))
                        conexao.commit()
                        cursor.close()
                        conexao.close()
                        st.success("Excluído com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
        else:
            st.info("Nenhum registro disponível para gerenciar com os filtros atuais.")

    # --- ABA 2: FECHAMENTO DE MÊS (FLUXO E SALDO REMANESCENTE) ---
    with aba2:
        st.markdown("### 📅 Fechamento Mensal e Evolução de Saldo")
        st.write("Visão consolidada de entradas, saídas, resultado líquido do mês e o saldo remanescente acumulado.")

        df_lancamentos["ano_mes"] = df_lancamentos["data_dt"].dt.to_period("M")
        
        if df_lancamentos["ano_mes"].notna().any():
            df_receitas = df_lancamentos[df_lancamentos["tipo"] == "Receita"].groupby("ano_mes")["valor"].sum().reset_index(name="entradas")
            df_despesas = df_lancamentos[df_lancamentos["tipo"] == "Despesa"].groupby("ano_mes")["valor"].sum().reset_index(name="saidas")
            
            df_fechamento = pd.merge(df_receitas, df_despesas, on="ano_mes", how="outer").fillna(0.0)
            df_fechamento = df_fechamento.sort_values(by="ano_mes", ascending=True).reset_index(drop=True)
            
            df_fechamento["resultado_mes"] = df_fechamento["entradas"] - df_fechamento["saidas"]
            df_fechamento["saldo_remanescente"] = df_fechamento["resultado_mes"].cumsum()
            df_fechamento["mes_ano_str"] = df_fechamento["ano_mes"].dt.strftime("%m/%Y")
            
            df_tabela_mensal = pd.DataFrame({
                "Mês/Ano": df_fechamento["mes_ano_str"],
                "Total Entradas": df_fechamento["entradas"].apply(fmt_moeda),
                "Total Saídas": df_fechamento["saidas"].apply(fmt_moeda),
                "Resultado do Mês": df_fechamento["resultado_mes"].apply(fmt_moeda),
                "Saldo Remanescente (Acumulado)": df_fechamento["saldo_remanescente"].apply(fmt_moeda)
            })
            
            st.dataframe(df_tabela_mensal, use_container_width=True, height=210)
        else:
            st.warning("Não há datas válidas o suficiente para gerar o fechamento mensal.")
else:
    st.info("Nenhum lançamento cadastrado no sistema para gerar relatórios.")