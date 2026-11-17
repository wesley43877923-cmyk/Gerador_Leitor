import io
import json
import pandas as pd
import streamlit as st
from omr_engine import OMRGenerator, OMRProcessor

st.set_page_config(
    page_title="Sistema OMR - Correção de Provas", page_icon="📝", layout="wide"
)

st.title("Gerador e Leitor de Cartões-Resposta")
st.markdown(
    "Aplicação para geração de folhas de resposta personalizadas e correção"
    " automatizada por visão computacional."
)

tabs = st.tabs([
    "🖨️ 1. Gerar Cartões-Resposta",
    "📷 2. Corrigir Avaliações",
    "ℹ️ Instruções de Uso",
])

# ----------------- ABA 1: GERADOR -----------------
with tabs[0]:
  st.header("Gerador de Cartões-Resposta em PDF")

  col1, col2 = st.columns([1, 2])

  with col1:
    st.subheader("Configurações da Prova")
    escola = st.text_input(
        "Nome da Escola", value="", placeholder="Ex: C.E. Maria Veralba Ferraz"
    )
    disciplina = st.text_input(
        "Disciplina / Matéria", value="", placeholder="Ex: Matemática"
    )
    avaliacao = st.text_input(
        "Nome da Avaliação",
        value="",
        placeholder="Ex: Teste do 1º trimestre",
    )

    incluir_assinatura = st.checkbox(
        "Incluir campo de Assinatura do Aluno no Cartão", value=True
    )

    num_questoes = st.number_input(
        "Quantidade de Questões", min_value=1, max_value=45, value=10, step=1
    )
    num_alternativas = st.number_input(
        "Número de Alternativas", min_value=2, max_value=5, value=5, step=1
    )
 
    arquivo_alunos = st.file_uploader(
        "Upload de Planilha Excel (.xlsx) ou CSV",
        type=["xlsx", "csv"],
        key="upload_alunos",
    )
    usar_exemplo = st.checkbox("Usar dados de exemplo para teste")

    st.subheader("Lista de Alunos")
    
        # --- MODELO APENAS COM MATRÍCULA, NOME E TURMA ---
    st.caption("Baixe o modelo padronizado para preencher com seus alunos:")
    
    df_modelo_alunos = pd.DataFrame({
            "matricula": ["2024001", "2024002", "2024003"],
            "nome": ["Ana Silva", "Bruno Costa", "Carla Oliveira"],
            "turma": ["9º Ano A", "9º Ano A", "9º Ano B"],
        })
    
    buf_alunos_excel = io.BytesIO()
    with pd.ExcelWriter(buf_alunos_excel, engine="openpyxl") as writer:
          df_modelo_alunos.to_excel(writer, index=False, sheet_name="Alunos")
    buf_alunos_excel.seek(0)
    
    col_al_mod1, col_al_mod2 = st.columns(2)
    with col_al_mod1:
          st.download_button(
              label="📄 Modelo (.xlsx)",
              data=buf_alunos_excel.getvalue(),
              file_name="modelo_alunos.xlsx",
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              key="btn_dl_alunos_xlsx",
          )
    with col_al_mod2:
          st.download_button(
              label="📄 Modelo (.csv)",
              data=df_modelo_alunos.to_csv(index=False).encode("utf-8"),
              file_name="modelo_alunos.csv",
              mime="text/csv",
              key="btn_dl_alunos_csv",
          )

  with col2:
    df_alunos = None
    if arquivo_alunos is not None:
      if arquivo_alunos.name.endswith(".csv"):
        df_alunos = pd.read_csv(arquivo_alunos)
      else:
        df_alunos = pd.read_excel(arquivo_alunos)
    elif usar_exemplo:
      df_alunos = pd.DataFrame({
          "matricula": [
              "2024001",
              "2024002",
              "2024003",
              "2024004",
              "2024005",
          ],
          "nome": [
              "Ana Silva",
              "Bruno Costa",
              "Carla Oliveira",
              "Daniel Santos",
              "Eduarda Lima",
          ],
          "turma": [
              "9º Ano A",
              "9º Ano A",
              "9º Ano B",
              "9º Ano B",
              "9º Ano A",
          ],
      })

    if df_alunos is not None:
      st.success(f"Carregados {len(df_alunos)} alunos com sucesso!")
      st.dataframe(df_alunos, height=200)

      if st.button("🚀 Gerar PDF dos Cartões-Resposta", type="primary"):
        with st.spinner(
            "Gerando arquivo PDF contendo QR Codes e marcadores..."
        ):
          # Escola, disciplina e avaliação do formulário são passadas como parâmetros padrão
          pdf_bytes = OMRGenerator.generate_pdf(
              df_alunos=df_alunos,
              num_questoes=num_questoes,
              num_alternativas=num_alternativas,
              escola_padrao=escola or "C.E. Maria Veralba Ferraz",
              disciplina_padrao=disciplina or "Matemática",
              avaliacao_padrao=avaliacao or "Teste do 1º trimestre",
              incluir_assinatura=incluir_assinatura,
          )

          nome_slug = (disciplina or "prova").lower().replace(" ", "_")
          st.download_button(
              label="📥 Baixar PDF dos Cartões Prontos para Impressão",
              data=pdf_bytes,
              file_name=f"cartoes_resposta_{nome_slug}.pdf",
              mime="application/pdf",
          )
    else:
      st.info(
          "Faça o upload do arquivo de alunos ou marque 'Usar dados de exemplo'"
          " para prosseguir."
      )

# ----------------- ABA 2: LEITOR E CORRETOR -----------------
with tabs[1]:
  st.header("Leitor OMR & Corretor de Cartões")

  col_gab, col_proc = st.columns([1, 2])

  with col_gab:
    st.subheader("1. Cadastrar Gabarito Oficial")

    modo_gabarito = st.radio(
        "Forma de inserção do gabarito:",
        ["✍️ Preenchimento Manual", "📁 Upload de Arquivo (CSV / Excel)"],
        horizontal=True,
    )

    gabarito = {}

    if modo_gabarito == "✍️ Preenchimento Manual":
      n_q_gabarito = st.number_input(
          "Nº de Questões da Prova", min_value=1, max_value=45, value=10, step=1
      )
      n_alt_gabarito = st.number_input(
          "Nº de Alternativas (ex: 5 = A-E)",
          min_value=2,
          max_value=5,
          value=5,
          step=1,
      )

      letras_disp = ["A", "B", "C", "D", "E"][:n_alt_gabarito]
      st.markdown("**Selecione a resposta correta de cada questão:**")

      g_cols = st.columns(3)
      for q in range(1, n_q_gabarito + 1):
        c_target = g_cols[(q - 1) % 3]
        gabarito[q] = c_target.selectbox(
            f"Q{q:02d}", letras_disp, key=f"gab_q_{q}"
        )

    else:
      st.markdown("---")
      st.markdown("### 📥 Baixar Modelo de Gabarito")
      st.caption(
          "Baixe o modelo abaixo, preencha as colunas `questao` e `resposta` e"
          " envie o arquivo."
      )

      df_modelo = pd.DataFrame({
          "questao": list(range(1, 11)),
          "resposta": ["A", "B", "C", "D", "E", "A", "B", "C", "D", "E"],
      })

      buf_excel = io.BytesIO()
      with pd.ExcelWriter(buf_excel, engine="openpyxl") as writer:
        df_modelo.to_excel(writer, index=False, sheet_name="Gabarito")
      buf_excel.seek(0)

      col_mod1, col_mod2 = st.columns(2)
      with col_mod1:
        st.download_button(
            label="📄 Baixar Modelo (.xlsx)",
            data=buf_excel.getvalue(),
            file_name="modelo_gabarito.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            key="btn_dl_gab_xlsx",
        )
      with col_mod2:
        st.download_button(
            label="📄 Baixar Modelo (.csv)",
            data=df_modelo.to_csv(index=False).encode("utf-8"),
            file_name="modelo_gabarito.csv",
            mime="text/csv",
            key="btn_dl_gab_csv",
        )

      st.markdown("---")
      st.markdown("### 📤 Upload do Gabarito Preenchido")
      arquivo_gabarito = st.file_uploader(
          "Envie a planilha do gabarito (.xlsx ou .csv)",
          type=["xlsx", "csv"],
          key="upload_gab",
      )

      if arquivo_gabarito is not None:
        try:
          if arquivo_gabarito.name.endswith(".csv"):
            df_gab = pd.read_csv(arquivo_gabarito)
          else:
            df_gab = pd.read_excel(arquivo_gabarito)

          df_gab.columns = [str(c).strip().lower() for c in df_gab.columns]

          if "questao" in df_gab.columns and "resposta" in df_gab.columns:
            for _, row in df_gab.iterrows():
              q_num = int(row["questao"])
              resp_letra = str(row["resposta"]).strip().upper()
              gabarito[q_num] = resp_letra

            st.success(
                "Gabarito carregado com sucesso! Total de"
                f" {len(gabarito)} questões."
            )
            st.dataframe(df_gab, height=180)
          else:
            st.error(
                "O arquivo deve conter as colunas 'questao' e 'resposta'."
                " Baixe o modelo acima."
            )
        except Exception as e:
          st.error(f"Erro ao ler o arquivo do gabarito: {e}")
      else:
        st.info("Aguardando upload da planilha de gabarito.")

  with col_proc:
    st.subheader("2. Upload das Fotos/Digitalizações")
    fotos_upload = st.file_uploader(
        "Envie as imagens dos cartões-resposta (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if fotos_upload:
      st.success(
          f"{len(fotos_upload)} cartões carregados para processamento."
      )

      if not gabarito:
        st.warning(
            "⚠️ Por favor, cadastre ou envie a planilha do gabarito antes de"
            " iniciar a correção."
        )
      else:
        if st.button(
            "📊 Processar e Corrigir Todas as Provas", type="primary"
        ):
          resultados = []
          bar = st.progress(0)

          for idx, item_foto in enumerate(fotos_upload):
            img_bytes = item_foto.read()
            res = OMRProcessor.process_card(img_bytes, gabarito)
            resultados.append(res)
            bar.progress((idx + 1) / len(fotos_upload))

          df_res = pd.DataFrame(resultados)
          st.subheader("Resultados da Correção")
          st.dataframe(df_res)

          buffer_out = io.BytesIO()
          with pd.ExcelWriter(buffer_out, engine="openpyxl") as writer:
            df_res.to_excel(writer, index=False, sheet_name="Notas")
          buffer_out.seek(0)

          st.download_button(
              label="📥 Baixar Planilha Final de Notas (.xlsx)",
              data=buffer_out.getvalue(),
              file_name="relatorio_notas_corrigidas.xlsx",
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              key="btn_dl_notas_final",
          )

# ----------------- ABA 3: INSTRUÇÕES -----------------
with tabs[2]:
  st.markdown("""
    ### 📖 Como Utilizar o Sistema OMR
    
    1. **Gerar os Cartões**:
       - Preencha os dados da prova (Escola, Disciplina, Nome da Avaliação) nos campos da tela.
       - Faça download do modelo em `.xlsx` ou `.csv` na Aba 1 e preencha a lista de alunos (apenas colunas `matricula`, `nome` e `turma`).
       - Defina a quantidade de questões (1 a 45) e alternativas (A-B até A-E).
       - Marque a opção de incluir o campo de assinatura, se necessário.
       - Baixe o PDF gerado e imprima em folha A4 em escala 100% (sem redimensionar).
       
    2. **Aplicação e Preenchimento**:
       - Os alunos devem assinar o cartão (se habilitado) e preencher completamente o círculo da opção desejada com caneta escura.
       
    3. **Fotografia / Digitalização**:
       - Tire fotos das provas com boa iluminação, garantindo que os 4 cantos pretos da folha estejam visíveis na foto.
       
    4. **Cadastrar ou Importar Gabarito**:
       - Preencha manualmente no painel ou faça upload de um arquivo `.xlsx` / `.csv` contendo as colunas `questao` e `resposta`.
       
    5. **Correção Automática**:
       - Faça upload de todas as fotos de uma vez.
       - O sistema identificará o aluno via QR Code e calculará a nota automaticamente exportando em Excel.
    """)