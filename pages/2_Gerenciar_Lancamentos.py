from datetime import datetime
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="Gerenciar Lançamentos", page_icon="✏️")

def obter_conexao():
  return psycopg2.connect(st.secrets["DATABASE_URL"])

st.subheader("✏️ Editar ou Excluir Lançamentos")

try:
  conexao = obter_conexao()
  # Busca todos os lançamentos sem restrição de data (traz passados, presentes e futuros)
  df = pd.read_sql_query(
      "SELECT id, data, tipo, categoria, descricao, valor FROM lancamentos ORDER BY id DESC",
      conexao,
  )
  conexao.close()
except Exception as e:
  st.error(f"Erro ao carregar dados: {e}")
  df = pd.DataFrame()

if not df.empty:
  st.write("Selecione um lançamento abaixo para alterar os dados ou excluí-lo se foi cadastrado errado. Aqui você gerencia registros passados, presentes e futuros.")

  # Função auxiliar para formatar moeda
  def fmt_moeda(v):
      return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

  # Formatar o valor para a string de exibição ficar amigável (ex: R$ 1.500,00)
  df["valor_fmt"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0).apply(fmt_moeda)

  df["resumo_label"] = (
      "ID: "
      + df["id"].astype(str)
      + " | "
      + df["data"]
      + " | "
      + df["tipo"]
      + " | "
      + df["categoria"]
      + " | "
      + df["valor_fmt"]
      + " ("
      + df["descricao"].fillna("")
      + ")"
  )

  lancamento_selecionado = st.selectbox(
      "Escolha o lançamento para gerenciar:", df["resumo_label"].tolist()
  )

  id_selecionado = int(lancamento_selecionado.split(" | ")[0].replace("ID: ", ""))
  dados_atuais = df[df["id"] == id_selecionado].iloc[0]

  st.divider()

  col_edit1, col_edit2 = st.columns(2)

  with col_edit1:
    st.markdown("### 🔄 Atualizar Lançamento")
    with st.form("form_edicao"):
      novo_tipo = st.selectbox(
          "Tipo",
          ["Despesa", "Receita"],
          index=0 if dados_atuais["tipo"] == "Despesa" else 1,
      )
      nova_categoria = st.text_input("Categoria", value=dados_atuais["categoria"])
      nova_descricao = st.text_input("Descrição", value=dados_atuais["descricao"])
      novo_valor = st.number_input(
          "Valor (R$)",
          min_value=0.0,
          format="%.2f",
          value=float(dados_atuais["valor"]),
      )
      nova_data = st.text_input("Data (DD/MM/AAAA)", value=dados_atuais["data"])

      salvar_alteracao = st.form_submit_button("Salvar Alterações")

      if salvar_alteracao:
        try:
          # Valida rigorosamente se a data digitada está no formato DD/MM/AAAA correto
          datetime.strptime(nova_data.strip(), "%d/%m/%Y")

          conexao = obter_conexao()
          cursor = conexao.cursor()
          cursor.execute(
              """
              UPDATE lancamentos 
              SET data = %s, tipo = %s, categoria = %s, descricao = %s, valor = %s
              WHERE id = %s
              """,
              (
                  nova_data.strip(),
                  novo_tipo,
                  nova_categoria,
                  nova_descricao,
                  novo_valor,
                  id_selecionado,
              ),
          )
          conexao.commit()
          cursor.close()
          conexao.close()
          st.success("Lançamento atualizado com sucesso!")
          st.rerun()
        except ValueError:
          st.error("A data digitada é inválida. Utilize estritamente o formato DD/MM/AAAA.")
        except Exception as e:
          st.error(f"Erro ao atualizar: {e}")

  with col_edit2:
    st.markdown("### 🗑️ Excluir Lançamento")
    st.warning("Atenção: Essa operação apagará permanentemente este registro.")

    if st.button("Excluir este Lançamento", type="primary"):
      try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM lancamentos WHERE id = %s", (id_selecionado,))
        conexao.commit()
        cursor.close()
        conexao.close()
        st.success("Lançamento excluído com sucesso!")
        st.rerun()
      except Exception as e:
        st.error(f"Erro ao excluir: {e}")
else:
  st.info("Nenhum lançamento encontrado para gerenciar.")