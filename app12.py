import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Verificar se o arquivo existe e carregá-lo
try:
    df = pd.read_excel("Painelteste - Copia.xlsx")
except FileNotFoundError:
    st.error("Erro: O arquivo 'Painelteste - Copia.xlsx' não foi encontrado. Verifique se ele está no repositório.")
    st.stop()

st.title("Painel Bancada do PT - Economia")

entes = df.iloc[:, 0].unique()

def adicionar_selecao():
    st.session_state["selecoes"].append({"ente": None, "variavel": None})

if "selecoes" not in st.session_state:
    st.session_state["selecoes"] = [{"ente": None, "variavel": None}]

for i, selecao in enumerate(st.session_state["selecoes"]):
    col1, col2 = st.columns([1, 3])

    with col1:
        ente = st.selectbox(f"Escolha o ente {i + 1}:", entes, key=f"ente_{i}")
        st.session_state["selecoes"][i]["ente"] = ente

    with col2:
        variaveis_disponiveis = df[df.iloc[:, 0] == ente].iloc[:, 1].unique()
        variavel = st.selectbox(
            f"Escolha a variável para o ente {ente}:", variaveis_disponiveis, key=f"variavel_{i}"
        )
        st.session_state["selecoes"][i]["variavel"] = variavel

st.button("+ Adicionar variável", on_click=adicionar_selecao)

df_grafico = pd.DataFrame()
for selecao in st.session_state["selecoes"]:
    if selecao["ente"] and selecao["variavel"]:
        dados = df[(df.iloc[:, 0] == selecao["ente"]) & (df.iloc[:, 1] == selecao["variavel"])]
        anos = dados.columns[2:].astype(int)
        valores = pd.to_numeric(dados.iloc[0, 2:], errors="coerce")
        valores = valores.where(~valores.isna(), None)

        coluna_nome = f"{selecao['ente']} - {selecao['variavel']}"
        df_temp = pd.DataFrame(valores.values, index=anos, columns=[coluna_nome])

        if coluna_nome not in df_grafico.columns:
            df_grafico = pd.concat([df_grafico, df_temp], axis=1)

# Criar o gráfico e desativar o zoom
fig = go.Figure()
for coluna in df_grafico.columns:
    fig.add_trace(
        go.Scatter(x=df_grafico.index, y=df_grafico[coluna], mode="lines+markers", name=coluna)
    )

# Configurar o layout para desativar o zoom
fig.update_layout(
    xaxis_title="Ano",
    yaxis_title="Valores Absolutos",
    dragmode=False,  # Desativa o zoom ao arrastar
    showlegend=True,
    yaxis2=dict(title="Percentual (%)", overlaying="y", side="right"),
    legend=dict(x=0, y=1.2, orientation="h"),
)

# Remover os botões de zoom da interface
fig.update_layout(
    modebar_remove=["zoom", "pan", "zoomIn", "zoomOut", "autoScale", "resetScale"]
)

# Exibir o gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)
