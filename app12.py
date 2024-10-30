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

# Função para adicionar uma nova variável
def adicionar_selecao():
    st.session_state["selecoes"].append({"ente": None, "variavel": None})

# Função para remover uma variável pelo índice
def remover_selecao(indice):
    if len(st.session_state["selecoes"]) > 1:  # Sempre manter pelo menos uma variável
        del st.session_state["selecoes"][indice]

# Inicializar seleções na sessão
if "selecoes" not in st.session_state:
    st.session_state["selecoes"] = [{"ente": None, "variavel": None}]

# Mostrar seletores dinâmicos com botão de remoção
for i, selecao in enumerate(st.session_state["selecoes"]):
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        ente = st.selectbox(f"Escolha o ente {i + 1}:", entes, key=f"ente_{i}")
        st.session_state["selecoes"][i]["ente"] = ente

    with col2:
        variaveis_disponiveis = df[df.iloc[:, 0] == ente].iloc[:, 1].unique()
        variavel = st.selectbox(
            f"Escolha a variável para o ente {ente}:", variaveis_disponiveis, key=f"variavel_{i}"
        )
        st.session_state["selecoes"][i]["variavel"] = variavel

    with col3:
        if i > 0:  # Exibir botão de remoção apenas para variáveis adicionais
            st.button("Remover", key=f"remover_{i}", on_click=remover_selecao, args=(i,))

st.button("+ Adicionar variável", on_click=adicionar_selecao)

# Preparar os dados para o gráfico
df_grafico = pd.DataFrame()
percentuais = []

for selecao in st.session_state["selecoes"]:
    if selecao["ente"] and selecao["variavel"]:
        dados = df[(df.iloc[:, 0] == selecao["ente"]) & (df.iloc[:, 1] == selecao["variavel"])]
        anos = dados.columns[2:].astype(int)
        valores = pd.to_numeric(dados.iloc[0, 2:], errors="coerce").where(lambda x: ~x.isna(), None)

        # Detectar se os valores são percentuais e preparar para o eixo secundário
        if valores.max() <= 1:
            valores *= 100  # Converter para porcentagem
            percentuais.append(f"{selecao['ente']} - {selecao['variavel']}")

        coluna_nome = f"{selecao['ente']} - {selecao['variavel']}"
        df_temp = pd.DataFrame(valores.values, index=anos, columns=[coluna_nome])

        if coluna_nome not in df_grafico.columns:
            df_grafico = pd.concat([df_grafico, df_temp], axis=1)

# Criar o gráfico e separar variáveis normais e percentuais
fig = go.Figure()

for coluna in df_grafico.columns:
    if coluna in percentuais:
        fig.add_trace(
            go.Scatter(
                x=df_grafico.index,
                y=df_grafico[coluna],
                mode="lines+markers+text",
                name=coluna,
                text=[f"{v:.2f}%" if v is not None else "" for v in df_grafico[coluna]],
                textposition="top center",
                yaxis="y2",
                line=dict(dash="dot"),
                hovertemplate="<b>%{text}</b><br>Ano: %{x}<br>Percentual: %{y}%<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df_grafico.index,
                y=df_grafico[coluna],
                mode="lines+markers+text",
                name=coluna,
                text=[f"{v:.2f}" if v is not None else "" for v in df_grafico[coluna]],
                textposition="top center",
                hovertemplate="<b>%{text}</b><br>Ano: %{x}<br>Valor: %{y}<extra></extra>",
            )
        )

# Configurar o layout para habilitar o eixo secundário
fig.update_layout(
    xaxis_title="Ano",
    yaxis_title="Valores Absolutos",
    yaxis2=dict(title="Percentual (%)", overlaying="y", side="right"),
    legend=dict(x=0, y=1.2, orientation="h"),
    dragmode=False,
    modebar_remove=["zoom", "pan", "zoomIn", "zoomOut", "autoScale", "resetScale"],
)

# Exibir o gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)
