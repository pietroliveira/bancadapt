import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import textwrap

# Função para formatar valores no estilo brasileiro
def formatar_valor(valor):
    if isinstance(valor, (int, float)):
        valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return valor_formatado.rstrip(",00")
    return valor

# Função para quebrar texto longo sem cortar palavras
def quebrar_texto_html(texto):
    return "<br>".join(textwrap.wrap(texto, width=30, break_long_words=False))

# Inicializar o estado da sessão
if "selecoes" not in st.session_state:
    st.session_state["selecoes"] = [{"ente": None, "variavel": None}]

# Interface do Streamlit
st.title("Painel Bancada do PT: Economia")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    entes = df.iloc[:, 0].unique()

    # Função para adicionar mais seleções
    def adicionar_selecao():
        st.session_state["selecoes"].append({"ente": None, "variavel": None})

    # Exibir seletores dinâmicos
    for i, selecao in enumerate(st.session_state["selecoes"]):
        col1, col2 = st.columns([1, 3])

        with col1:
            ente = st.selectbox(
                f"Escolha o ente {i + 1}:",
                entes,
                key=f"ente_{i}",
            )
            st.session_state["selecoes"][i]["ente"] = ente

        with col2:
            variaveis_disponiveis = df[df.iloc[:, 0] == ente].iloc[:, 1].unique()
            variavel = st.selectbox(
                f"Escolha a variável para o ente {ente}:",
                variaveis_disponiveis,
                key=f"variavel_{i}",
            )
            st.session_state["selecoes"][i]["variavel"] = variavel

    st.button("+ Adicionar variável", on_click=adicionar_selecao)

    # Preparar os dados para o gráfico
    df_grafico = pd.DataFrame()
    percentuais = []

    for selecao in st.session_state["selecoes"]:
        if selecao["ente"] and selecao["variavel"]:
            dados = df[(df.iloc[:, 0] == selecao["ente"]) &
                       (df.iloc[:, 1] == selecao["variavel"])]

            anos = dados.columns[2:].astype(int)
            valores = pd.to_numeric(dados.iloc[0, 2:], errors='coerce')

            # Substituir valores ausentes por None
            valores = valores.where(~valores.isna(), None)

            # Verificar se é uma série percentual
            is_percentual = np.all(valores.fillna(0) < 1)

            if is_percentual:
                valores *= 100
                percentuais.append(f"{selecao['ente']} - {selecao['variavel']}")

            coluna_nome = f"{selecao['ente']} - {selecao['variavel']}"
            df_temp = pd.DataFrame(valores.values, index=anos, columns=[coluna_nome])

            # Adicionar ao DataFrame apenas se não houver duplicação
            if coluna_nome not in df_grafico.columns:
                df_grafico = pd.concat([df_grafico, df_temp], axis=1)

    # Exibir o gráfico se houver dados
    if not df_grafico.empty:
        fig = go.Figure()

        # Adicionar traços para variáveis normais e percentuais separadamente
        for coluna in df_grafico.columns:
            if coluna in percentuais:
                fig.add_trace(go.Scatter(
                    x=df_grafico.index,
                    y=df_grafico[coluna],
                    name=coluna,
                    mode='lines+markers+text',
                    text=[formatar_valor(v) + "%" if v is not None else "" for v in df_grafico[coluna]],
                    textposition="top center",
                    yaxis="y2",
                    line=dict(dash="dot"),
                    hovertemplate="<b>%{text}</b><br>Ano: %{x}<br>Percentual: %{y}%<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df_grafico.index,
                    y=df_grafico[coluna],
                    name=coluna,
                    mode='lines+markers+text',
                    text=[formatar_valor(v) if v is not None else "" for v in df_grafico[coluna]],
                    textposition="top center",
                    hovertemplate="<b>%{text}</b><br>Ano: %{x}<br>Valor: %{y}<extra></extra>"
                ))

        fig.update_layout(
            xaxis_title="Ano",
            yaxis_title="Valores Absolutos",
            yaxis2=dict(title="Percentual (%)", overlaying="y", side="right"),
            legend=dict(x=0, y=1.2, orientation="h")
        )

        st.plotly_chart(fig)

        # Exibir a tabela formatada
        df_formatado = df_grafico.rename(columns=lambda x: quebrar_texto_html(x)).applymap(formatar_valor).transpose()
        st.write("Tabela de Dados:")
        st.markdown(
            df_formatado.style.set_properties(**{
                'white-space': 'pre-wrap',
                'max-width': '20ch'
            }).to_html(escape=False), unsafe_allow_html=True
        )
