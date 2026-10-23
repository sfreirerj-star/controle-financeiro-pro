from datetime import datetime
import io
import urllib.parse
import pandas as pd
import psycopg2
import streamlit as st
from utils import aplicar_estilo_moderno

# 1. Apenas UMA chamada de set_page_config no topo absoluto do script
st.set_page_config(
    page_title="Relatórios e Consultas - Painel do Marcelo",
    page_icon="📈",
    layout="wide",
)
aplicar_estilo_moderno()


def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])


def extrair_competencia(data_str):
  try:
    dt = pd.to_datetime(data_str, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
      dt = pd.to_datetime(data_str, errors="coerce")
    if pd.notna(dt):
      return dt.strftime("%m/%Y"), dt.strftime("%Y-%m")
  except Exception:
    pass
  return "Indefinido", "9999-99"


def configurar_sidebar_competencia(conexao, prefixo_key="global"):
  mes_atual_sistema = datetime.now().strftime("%m/%Y")
  competencias_disponiveis = [mes_atual_sistema]
  mapeamento_comps = pd.DataFrame(
      {
          "competencia": [mes_atual_sistema],
          "comp_ordem": [datetime.now().strftime("%Y-%m")],
      }
  )

  try:
    df_l = pd.read_sql_query("SELECT data FROM lancamentos", conexao)
  except Exception:
    df_l = pd.DataFrame(columns=["data"])

  try:
    df_a = pd.read_sql_query("SELECT data FROM desafio_aportes", conexao)
  except Exception:
    df_a = pd.DataFrame(columns=["data"])

  for df_item in [df_l, df_a]:
    if not df_item.empty and "data" in df_item.columns:
      res = df_item["data"].apply(extrair_competencia)
      df_item["competencia"] = [x[0] for x in res]
      df_item["comp_ordem"] = [x[1] for x in res]

  if not df_l.empty or not df_a.empty:
    mapeamento_comps = pd.concat([
        df_l[["competencia", "comp_ordem"]]
        if not df_l.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
        df_a[["competencia", "comp_ordem"]]
        if not df_a.empty
        else pd.DataFrame(columns=["competencia", "comp_ordem"]),
    ]).drop_duplicates()

    mapeamento_comps = mapeamento_comps[
        mapeamento_comps["competencia"] != "Indefinido"
    ].sort_values("comp_ordem", ascending=False)

    if not mapeamento_comps.empty:
      competencias_disponiveis = mapeamento_comps["competencia"].tolist()

  if mes_atual_sistema not in competencias_disponiveis:
    competencias_disponiveis.insert(0, mes_atual_sistema)

  key_selectbox = f"selectbox_competencia_{prefixo_key}"

  if key_selectbox not in st.session_state:
    st.session_state[key_selectbox] = mes_atual_sistema

  try:
    index_atual = competencias_disponiveis.index(st.session_state[key_selectbox])
  except ValueError:
    index_atual = 0

  st.sidebar.markdown("---")
  st.sidebar.header("📅 Filtro de Competência")
  competencia_selecionada = st.sidebar.selectbox(
      "Selecione o Mês/Ano de Referência",
      options=competencias_disponiveis,
      index=index_atual,
      key=key_selectbox,
  )

  ordem_sel = (
      mapeamento_comps[
          mapeamento_comps["competencia"] == competencia_selecionada
      ]["comp_ordem"].values[0]
      if not mapeamento_comps.empty
      and competencia_selecionada in mapeamento_comps["competencia"].values
      else datetime.now().strftime("%Y-%m")
  )

  return competencia_selecionada, ordem_sel


st.title("💰 Controle Financeiro — Painel do Marcelo")
st.subheader("📈 Relatórios, Consultas e Fechamento de Mês")
st.write(
    "Filtre seus lançamentos detalhadamente, gerencie registros, exporte"
    " relatórios, acompanhe o fechamento mês a mês e projete seu saldo futuro."
)

# Configuração da barra lateral
try:
  conexao_sidebar = obter_conexao()
  competencia_selecionada, _ = configurar_sidebar_competencia(
      conexao_sidebar, prefixo_key="relatorios"
  )
  conexao_sidebar.close()
except Exception:
  competencia_selecionada = datetime.now().strftime("%m/%Y")

# Carregar dados do banco de dados
try:
  conexao = obter_conexao()
  df_lancamentos = pd.read_sql_query(
      "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos"
      " ORDER BY id DESC",
      conexao,
  )
  try:
    df_aportes = pd.read_sql_query("SELECT * FROM desafio_aportes", conexao)
  except Exception:
    df_aportes = pd.DataFrame()

  try:
    df_resgates = pd.read_sql_query("SELECT * FROM desafio_resgates", conexao)
  except Exception:
    df_resgates = pd.DataFrame()

  conexao.close()
except Exception as e:
  st.error(f"Erro ao carregar dados do banco: {e}")
  df_lancamentos = pd.DataFrame()
  df_aportes = pd.DataFrame()
  df_resgates = pd.DataFrame()


def fmt_moeda(v):
  return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


if not df_lancamentos.empty:
  df_lancamentos["data_dt"] = pd.to_datetime(
      df_lancamentos["data"], format="%d/%m/%Y", errors="coerce"
  )

  aba1, aba2, aba3, aba4 = st.tabs([
      "🔍 Consulta, Filtros e Ações",
      "📅 Fechamento de Mês (Saldo Remanescente)",
      "🔮 Projeção de Saldo Futuro",
      "📥 Central de Exportação e Backup",
  ])

  # --- ABA 1: CONSULTA, FILTROS E AÇÕES ---
  with aba1:
    st.markdown(
        f"### 🔎 Filtrar Lançamentos (Competência Ativa:"
        f" {competencia_selecionada})"
    )

    res_comp = df_lancamentos["data_dt"].apply(
        lambda x: x.strftime("%m/%Y") if pd.notna(x) else "Indefinido"
    )
    df_lancamentos["competencia_col"] = res_comp

    col_f0, col_f1, col_f2, col_f3 = st.columns(4)

    with col_f0:
      usar_filtro_comp = st.checkbox(
          "Filtrar por Mês Ativo",
          value=True,
          help=(
              "Se marcado, exibe apenas os lançamentos do mês selecionado na"
              " barra lateral."
          ),
      )
    with col_f1:
      tipos_disponiveis = ["Todos"] + list(
          df_lancamentos["tipo"].dropna().unique()
      )
      filtro_tipo = st.selectbox("Filtrar por Tipo", tipos_disponiveis)
    with col_f2:
      categorias_disponiveis = sorted(
          list(df_lancamentos["categoria"].dropna().unique())
      )
      filtro_categorias = st.multiselect(
          "Filtrar por Categoria(s)", categorias_disponiveis, default=[]
      )
    with col_f3:
      filtro_texto = st.text_input("Buscar na Descrição (Palavra-chave)")

    df_filtrado = df_lancamentos.copy()

    if usar_filtro_comp:
      df_filtrado = df_filtrado[
          df_filtrado["competencia_col"] == competencia_selecionada
      ]

    if filtro_tipo != "Todos":
      df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]

    if filtro_categorias:
      df_filtrado = df_filtrado[
          df_filtrado["categoria"].isin(filtro_categorias)
      ]

    if filtro_texto:
      df_filtrado = df_filtrado[
          df_filtrado["descricao"].str.contains(filtro_texto, case=False, na=False)
      ]

    df_exibicao = df_filtrado.copy()
    df_exibicao["valor_num"] = (
        pd.to_numeric(df_exibicao["valor"], errors="coerce")
        .fillna(0.0)
        .astype(float)
    )
    df_exibicao["valor_formatado"] = df_exibicao["valor_num"].apply(fmt_moeda)

    colunas_mostrar = [
        "id",
        "data",
        "tipo",
        "categoria",
        "descricao",
        "valor_formatado",
    ]

    st.dataframe(
        df_exibicao[colunas_mostrar]
        .rename(columns={"valor_formatado": "valor"})
        .set_index("id"),
        use_container_width=True,
        height=210,
    )

    total_filtrado = df_exibicao["valor_num"].sum()
    cat_str = ", ".join(filtro_categorias) if filtro_categorias else "Todas"
    st.info(f"📊 **Total dos lançamentos filtrados:** {fmt_moeda(total_filtrado)}")

    col_exp1, col_exp2, col_exp3 = st.columns(3)

    df_para_exportar = df_exibicao[
        ["id", "data", "tipo", "categoria", "descricao", "valor_num"]
    ].rename(columns={"valor_num": "valor"})

    with col_exp1:
      csv_data = df_para_exportar.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Baixar em CSV",
          data=csv_data,
          file_name=f"relatorio_lancamentos_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          use_container_width=True,
      )

    with col_exp2:
      output_excel = io.BytesIO()
      with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df_para_exportar.to_excel(writer, index=False, sheet_name="Lancamentos")
      excel_data = output_excel.getvalue()
      st.download_button(
          label="📊 Baixar em Excel (.xlsx)",
          data=excel_data,
          file_name=f"relatorio_lancamentos_{datetime.now().strftime('%Y%m%d')}.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          use_container_width=True,
      )

    with col_exp3:
      html_tabela = df_para_exportar.to_html(
          index=False, classes="table table-striped"
      )
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
    <p><b>Filtro Aplicado:</b> Competência ({competencia_selecionada}) | Tipo ({filtro_tipo}) | Categorias ({cat_str})</p>
    {html_tabela}
    <div class="total">Total Filtrado: {fmt_moeda(total_filtrado)}</div>
    <script>
        window.onload = function() {{ window.print(); }}
    </script>
</body>
</html>"""

      html_encoded = urllib.parse.quote(html_code)
      st.markdown(
          f"""
                <a href="data:text/html;charset=utf-8,{html_encoded}" target="_blank" style="text-decoration: none; display: block; width: 100%;">
                    <div style="background-color: #ff4b4b; color: white; text-align: center; padding: 10px 18px; border-radius: 4px; font-weight: bold; cursor: pointer; width: 100%;">
                        🖨️ Imprimir / PDF
                    </div>
                </a>
                """,
          unsafe_allow_html=True,
      )

    st.divider()

    st.markdown("### ✏️ Gerenciar Lançamento Filtrado (Editar ou Excluir)")
    if not df_filtrado.empty:
      df_filtrado["resumo_acao"] = (
          "ID: "
          + df_filtrado["id"].astype(str)
          + " | "
          + df_filtrado["data"]
          + " | "
          + df_filtrado["categoria"]
          + " | "
          + df_filtrado["descricao"].fillna("")
      )

      lanc_sel = st.selectbox(
          "Selecione o lançamento para alterar ou excluir:",
          df_filtrado["resumo_acao"].tolist(),
      )
      id_sel = int(lanc_sel.split(" | ")[0].replace("ID: ", ""))
      dado_reg = df_filtrado[df_filtrado["id"] == id_sel].iloc[0]

      col_a1, col_a2 = st.columns(2)
      with col_a1:
        with st.form("form_edicao_relatorio"):
          st.markdown("#### Corrigir Registro")
          ntipo = st.selectbox(
              "Tipo",
              ["Despesa", "Receita"],
              index=0 if dado_reg["tipo"] == "Despesa" else 1,
          )
          ncateg = st.text_input("Categoria", value=dado_reg["categoria"])
          ndesc = st.text_input("Descrição", value=dado_reg["descricao"])
          nval = st.number_input(
              "Valor (R$)", value=float(dado_reg["valor"]), format="%.2f"
          )
          ndata = st.text_input("Data (DD/MM/AAAA)", value=dado_reg["data"])

          if st.form_submit_button("Salvar Alterações"):
            try:
              datetime.strptime(ndata.strip(), "%d/%m/%Y")
              conexao = obter_conexao()
              cursor = conexao.cursor()
              cursor.execute(
                  "UPDATE lancamentos SET data = %s, tipo = %s, categoria = %s,"
                  " descricao = %s, valor = %s WHERE id = %s",
                  (ndata.strip(), ntipo, ncateg, ndesc, nval, id_sel),
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
        st.warning(
            "Atenção: Essa operação apagará o registro permanentemente."
        )
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
      st.info(
          "Nenhum registro disponível para gerenciar com os filtros atuais."
      )

  # --- ABA 2: FECHAMENTO DE MÊS LIMPO E MATEMÁTICO ---
  with aba2:
    st.markdown("### 📅 Fechamento Mensal e Evolução de Saldo")
    st.write(
        "Visão consolidada de entradas, saídas, resultado líquido do mês e o"
        " saldo remanescente acumulado."
    )

    df_lancamentos["comp_ordem"] = df_lancamentos["data"].apply(lambda x: extrair_competencia(x)[1])
    df_lancamentos["competencia"] = df_lancamentos["data"].apply(lambda x: extrair_competencia(x)[0])

    if not df_aportes.empty and "data" in df_aportes.columns:
      df_aportes["comp_ordem"] = df_aportes["data"].apply(lambda x: extrair_competencia(x)[1])
      df_aportes["valor_num"] = pd.to_numeric(df_aportes["valor"], errors="coerce").fillna(0.0)
    else:
      df_aportes["comp_ordem"] = "9999-99"
      df_aportes["valor_num"] = 0.0

    if not df_resgates.empty and "data" in df_resgates.columns:
      df_resgates["comp_ordem"] = df_resgates["data"].apply(lambda x: extrair_competencia(x)[1])
      df_resgates["valor_num"] = pd.to_numeric(df_resgates["valor"], errors="coerce").fillna(0.0)
    else:
      df_resgates["comp_ordem"] = "9999-99"
      df_resgates["valor_num"] = 0.0

    todas_ordens = sorted(
        list(
            set(
                df_lancamentos[df_lancamentos["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist()
                + df_aportes[df_aportes["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist()
                + df_resgates[df_resgates["comp_ordem"] != "9999-99"]["comp_ordem"].unique().tolist()
            )
        )
    )

    if todas_ordens:
      dados_fechamento = []
      saldo_acumulado_loop = 0.0

      for ord_comp in todas_ordens:
        ano, mes = ord_comp.split("-")
        comp_formatada = f"{mes}/{ano}"

        df_lan_ord = df_lancamentos[
            (df_lancamentos["comp_ordem"] == ord_comp)
            & (df_lancamentos["categoria"].str.strip().str.lower() != "resgate")
        ]

        rec_c = df_lan_ord[
            df_lan_ord["tipo"].str.strip().str.lower().isin(["receita", "crédito", "credito", "entrada"])
        ]["valor"].astype(float).sum() if not df_lan_ord.empty else 0.0

        gas_c = df_lan_ord[
            df_lan_ord["tipo"].str.strip().str.lower().isin(["despesa", "débito", "debito", "saida"])
        ]["valor"].astype(float).sum() if not df_lan_ord.empty else 0.0

        # Aportes (dinheiro que saiu para investimentos)
        apo_c = (
            df_aportes[
                (df_aportes["comp_ordem"] == ord_comp)
                & (~df_aportes["local_aplicacao"].str.contains("Rendimento", case=False, na=False))
            ]["valor_num"].sum()
            if not df_aportes.empty and "valor_num" in df_aportes.columns
            else 0.0
        )

        # Resgates (dinheiro que voltou dos investimentos)
        res_c = (
            df_resgates[df_resgates["comp_ordem"] == ord_comp]["valor_num"].sum()
            if not df_resgates.empty and "valor_num" in df_resgates.columns
            else 0.0
        )

        # Investimento líquido simples do mês (Aportes - Resgates)
        invest_liquido = apo_c - res_c

        # Resultado do Mês = Entradas - Saídas - Investimento Líquido
        resultado_mes = rec_c - gas_c - invest_liquido
        saldo_acumulado_loop += resultado_mes

        dados_fechamento.append({
            "Mês/Ano": comp_formatada,
            "Total Entradas": fmt_moeda(rec_c),
            "Total Saídas": fmt_moeda(gas_c),
            "Invest. Líquido": fmt_moeda(invest_liquido),
            "Resultado do Mês": fmt_moeda(resultado_mes),
            "Saldo Remanescente (Acumulado)": fmt_moeda(saldo_acumulado_loop),
        })

      df_tabela_mensal = pd.DataFrame(dados_fechamento)
      st.dataframe(df_tabela_mensal, use_container_width=True, height=210)
    else:
      st.warning(
          "Não há datas válidas o suficiente para gerar o fechamento mensal."
      )

  # --- ABA 3: PROJEÇÃO DE SALDO FUTURO ---
  with aba3:
    st.markdown("### 🔮 Simulador de Projeção de Saldo Futuro")
    st.write(
        "Projete o crescimento do seu saldo com base nas médias históricas de"
        " entradas e saídas ou defina valores personalizados."
    )

    if not df_lancamentos.empty and todas_ordens:
      saldo_atual_base = saldo_acumulado_loop

      media_entradas_hist = df_lancamentos[
          df_lancamentos["tipo"].str.strip().str.lower().isin(["receita", "crédito", "credito", "entrada"])
      ]["valor"].astype(float).mean() if not df_lancamentos.empty else 0.0

      media_saidas_hist = df_lancamentos[
          df_lancamentos["tipo"].str.strip().str.lower().isin(["despesa", "débito", "debito", "saida"])
      ]["valor"].astype(float).mean() if not df_lancamentos.empty else 0.0

      col_p1, col_p2, col_p3 = st.columns(3)
      with col_p1:
        patrimonio_inicial_proj = st.number_input(
            "Saldo Base Inicial (R$)",
            value=float(saldo_atual_base),
            step=100.0,
            format="%.2f",
        )
      with col_p2:
        entrada_mensal_proj = st.number_input(
            "Média de Entradas Mensais (R$)",
            value=float(media_entradas_hist),
            step=100.0,
            format="%.2f",
        )
      with col_p3:
        saida_mensal_proj = st.number_input(
            "Média de Saídas Mensais (R$)",
            value=float(media_saidas_hist),
            step=100.0,
            format="%.2f",
        )

      meses_proj = st.slider(
          "Meses à Frente para Projeção",
          min_value=1,
          max_value=24,
          value=6,
          step=1,
      )

      lista_proj = []
      saldo_loop = patrimonio_inicial_proj
      data_base = datetime.now()

      for i in range(1, meses_proj + 1):
        mes_futuro = (
            data_base.replace(day=1) + pd.DateOffset(months=i)
        ).strftime("%m/%Y")
        resultado_mes_proj = entrada_mensal_proj - saida_mensal_proj
        saldo_loop += resultado_mes_proj

        lista_proj.append({
            "Mês Projeção": mes_futuro,
            "Entradas Previstas (R$)": round(entrada_mensal_proj, 2),
            "Saídas Previstas (R$)": round(saida_mensal_proj, 2),
            "Resultado do Mês (R$)": round(resultado_mes_proj, 2),
            "Saldo Acumulado Projetado (R$)": round(saldo_loop, 2),
        })

      df_projecao = pd.DataFrame(lista_proj)

      st.write("")
      st.markdown("#### 📊 Resultado da Projeção Mês a Mês")

      df_proj_exibe = df_projecao.copy()
      df_proj_exibe["Entradas Previstas (R$)"] = df_proj_exibe[
          "Entradas Previstas (R$)"
      ].apply(fmt_moeda)
      df_proj_exibe["Saídas Previstas (R$)"] = df_proj_exibe[
          "Saídas Previstas (R$)"
      ].apply(fmt_moeda)
      df_proj_exibe["Resultado do Mês (R$)"] = df_proj_exibe[
          "Resultado do Mês (R$)"
      ].apply(fmt_moeda)
      df_proj_exibe["Saldo Acumulado Projetado (R$)"] = df_proj_exibe[
          "Saldo Acumulado Projetado (R$)"
      ].apply(fmt_moeda)

      st.dataframe(
          df_proj_exibe.set_index("Mês Projeção"), use_container_width=True
      )

      st.write("")
      st.markdown("#### 📈 Gráfico de Evolução Patrimonial Projetada")
      st.line_chart(
          df_projecao.set_index("Mês Projeção")[
              ["Saldo Acumulado Projetado (R$)"]
          ]
      )
    else:
      st.info(
          "Cadastre mais lançamentos com datas válidas para habilitar a"
          " projeção baseada em histórico."
      )

  # --- ABA 4: CENTRAL DE EXPORTAÇÃO E BACKUP ---
  with aba4:
    st.markdown("### 📥 Central de Exportação e Backup do Banco de Dados")
    st.write(
        "Exporte relatórios consolidados por mês, ano completo ou faça o backup"
        " completo de todas as tabelas do sistema."
    )

    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
      tipo_exportacao = st.selectbox(
          "Selecione o Escopo do Relatório:",
          [
              "Mês Atual / Ativo",
              "Ano Completo",
              "Backup Completo (Todas as Tabelas)",
          ],
          key="tipo_exportacao_relatorio",
      )

    with col_exp2:
      if tipo_exportacao == "Ano Completo":
        anos_disponiveis = [2026, 2025, 2024, 2023]
        ano_selecionado = st.selectbox(
            "Selecione o Ano de Referência:",
            anos_disponiveis,
            key="ano_exp_sel",
        )
      elif tipo_exportacao == "Mês Atual / Ativo":
        st.info(
            f"Exportando dados da competência ativa:"
            f" **{competencia_selecionada}**"
        )

    if st.button("📊 Gerar Arquivo para Download", type="primary"):
      try:
        conexao = obter_conexao()

        df_l = pd.read_sql_query("SELECT * FROM lancamentos", conexao)
        df_a = pd.read_sql_query("SELECT * FROM desafio_aportes", conexao)
        df_r = pd.read_sql_query("SELECT * FROM desafio_resgates", conexao)
        df_d = pd.read_sql_query("SELECT * FROM dividas", conexao)
        conexao.close()

        output = io.BytesIO()

        if tipo_exportacao == "Mês Atual / Ativo":
          df_l_exp = (
              df_l[df_l["data"].str.contains(f"/{competencia_selecionada}")]
              if not df_l.empty
              else df_l
          )
          df_a_exp = (
              df_a[df_a["data"].str.contains(f"/{competencia_selecionada}")]
              if not df_a.empty
              else df_a
          )
          df_r_exp = (
              df_r[df_r["data"].str.contains(f"/{competencia_selecionada}")]
              if not df_r.empty
              else df_r
          )

          with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_l_exp.to_excel(
                writer, sheet_name="Lancamentos_Mes", index=False
            )
            df_a_exp.to_excel(writer, sheet_name="Aportes_Mes", index=False)
            df_r_exp.to_excel(writer, sheet_name="Resgates_Mes", index=False)

          nome_arquivo = (
              f"Relatorio_Financeiro_{competencia_selecionada.replace('/', '_')}.xlsx"
          )

        elif tipo_exportacao == "Ano Completo":
          df_l_exp = (
              df_l[df_l["data"].str.contains(f"/{ano_selecionado}")]
              if not df_l.empty
              else df_l
          )
          df_a_exp = (
              df_a[df_a["data"].str.contains(f"/{ano_selecionado}")]
              if not df_a.empty
              else df_a
          )
          df_r_exp = (
              df_r[df_r["data"].str.contains(f"/{ano_selecionado}")]
              if not df_r.empty
              else df_r
          )

          with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_l_exp.to_excel(
                writer, sheet_name=f"Lancamentos_{ano_selecionado}", index=False
            )
            df_a_exp.to_excel(
                writer, sheet_name=f"Aportes_{ano_selecionado}", index=False
            )
            df_r_exp.to_excel(
                writer, sheet_name=f"Resgates_{ano_selecionado}", index=False
            )

          nome_arquivo = f"Relatorio_Anual_{ano_selecionado}.xlsx"

        else:  # Backup Completo
          with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_l.to_excel(writer, sheet_name="Todos_Lancamentos", index=False)
            df_a.to_excel(writer, sheet_name="Todos_Aportes", index=False)
            df_r.to_excel(writer, sheet_name="Todos_Resgates", index=False)
            df_d.to_excel(writer, sheet_name="Dividas", index=False)

          nome_arquivo = f"Backup_Banco_Dados_Completo_{datetime.now().strftime('%Y_%m_%d')}.xlsx"

        processed_data = output.getvalue()

        st.download_button(
            label=f"💾 Baixar Planilha ({nome_arquivo})",
            data=processed_data,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.success(
            "Planilha gerada com sucesso! Clique no botão de download acima."
        )

      except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")
else:
  st.info("Nenhum lançamento cadastrado no sistema para gerar relatórios.")