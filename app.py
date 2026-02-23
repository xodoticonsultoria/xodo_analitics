import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine
from sklearn.linear_model import LinearRegression
import numpy as np

# ===============================
# CONFIGURAÇÃO
# ===============================

st.set_page_config(layout="wide")
st.title("📊 Production Intelligence Dashboard")

# ===============================
# BUSCAR DADOS
# ===============================

query = """
SELECT 
    o.data,
    p.nome AS produto,
    o.produzido,
    o.vendido,
    o.enviado_filial,
    o.sobra_real
FROM operacao_diaria o
JOIN produtos p ON o.produto_id = p.id
"""

df = pd.read_sql(query, engine)

if df.empty:
    st.warning("Nenhum dado disponível.")
    st.stop()

df["data"] = pd.to_datetime(df["data"])
df["mes"] = df["data"].dt.month
df["ano"] = df["data"].dt.year

# ===============================
# FILTROS
# ===============================

st.sidebar.header("Filtros")

mes_selecionado = st.sidebar.selectbox(
    "Mês",
    sorted(df["mes"].unique())
)

produto_selecionado = st.sidebar.multiselect(
    "Produto",
    df["produto"].unique(),
    default=df["produto"].unique()
)

df_filtrado = df[
    (df["mes"] == mes_selecionado) &
    (df["produto"].isin(produto_selecionado))
].copy()

# ===============================
# KPIs
# ===============================

total_produzido = df_filtrado["produzido"].sum()
total_vendido = df_filtrado["vendido"].sum()
total_enviado = df_filtrado["enviado_filial"].sum()
total_sobra = df_filtrado["sobra_real"].sum()

desperdicio_medio = (total_sobra / total_produzido) * 100 if total_produzido > 0 else 0
eficiencia_venda = (total_vendido / total_produzido) * 100 if total_produzido > 0 else 0
producao_nao_explicada = total_produzido - total_vendido - total_enviado - total_sobra

# ===============================
# SCORE DE RISCO
# ===============================

score = 0
score += min(desperdicio_medio * 2, 40)
score += min((100 - eficiencia_venda) * 0.4, 40)
score += min(abs(producao_nao_explicada) * 0.2, 20)
score = min(score, 100)

if score < 30:
    risco_label = "🟢 BAIXO"
elif score < 60:
    risco_label = "🟡 MODERADO"
else:
    risco_label = "🔴 CRÍTICO"

# ===============================
# EXIBIR KPIs
# ===============================

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("📦 Produzido", f"{total_produzido:.0f}")
col2.metric("🟢 Vendido", f"{total_vendido:.0f}")
col3.metric("🚚 Enviado", f"{total_enviado:.0f}")
col4.metric("🔴 Desperdício", f"{desperdicio_medio:.2f}%")
col5.metric("⚠️ Não Explicada", f"{producao_nao_explicada:.0f}")
col6.metric("📊 Score", f"{score:.0f} - {risco_label}")

st.divider()

# ===============================
# GRÁFICO TENDÊNCIA
# ===============================

df_agrupado = df_filtrado.groupby("data", as_index=False)[
    ["produzido", "vendido", "enviado_filial"]
].sum()

fig1 = px.line(
    df_agrupado,
    x="data",
    y=["produzido", "vendido", "enviado_filial"],
    markers=True,
    template="plotly_dark",
    title="Produção vs Venda vs Envio"
)

st.plotly_chart(fig1, use_container_width=True)

# ===============================
# DESPERDÍCIO POR PRODUTO
# ===============================

df_produto = df_filtrado.groupby("produto").agg({
    "produzido": "sum",
    "sobra_real": "sum"
}).reset_index()

df_produto["desperdicio_percentual"] = (
    df_produto["sobra_real"] / df_produto["produzido"]
) * 100

fig2 = px.bar(
    df_produto,
    x="produto",
    y="desperdicio_percentual",
    color="desperdicio_percentual",
    color_continuous_scale=["green", "yellow", "red"],
    template="plotly_dark",
    title="Desperdício Médio por Produto (%)"
)

st.plotly_chart(fig2, use_container_width=True)

# ===============================
# RANKING EFICIÊNCIA
# ===============================

st.subheader("🏆 Ranking de Eficiência")

df_eficiencia = df_filtrado.groupby("produto").agg({
    "produzido": "sum",
    "vendido": "sum"
}).reset_index()

df_eficiencia["eficiencia_percentual"] = (
    df_eficiencia["vendido"] / df_eficiencia["produzido"]
) * 100

df_eficiencia = df_eficiencia.sort_values("eficiencia_percentual", ascending=False)

fig3 = px.bar(
    df_eficiencia,
    x="produto",
    y="eficiencia_percentual",
    color="eficiencia_percentual",
    color_continuous_scale=["red", "yellow", "green"],
    template="plotly_dark",
    title="Eficiência de Venda (%)"
)

st.plotly_chart(fig3, use_container_width=True)

# ===============================
# CLASSIFICAÇÃO ABC
# ===============================

st.subheader("🏆 Classificação ABC")

df_abc = df_filtrado.groupby("produto")["vendido"].sum().reset_index()
df_abc = df_abc.sort_values("vendido", ascending=False)

if df_abc["vendido"].sum() > 0:
    df_abc["percentual"] = df_abc["vendido"] / df_abc["vendido"].sum()
    df_abc["percentual_acumulado"] = df_abc["percentual"].cumsum()
else:
    df_abc["percentual"] = 0
    df_abc["percentual_acumulado"] = 0

def classificar_abc(x):
    if x <= 0.7:
        return "A"
    elif x <= 0.9:
        return "B"
    else:
        return "C"

df_abc["classe"] = df_abc["percentual_acumulado"].apply(classificar_abc)

st.dataframe(df_abc)

# ===============================
# PREVISÃO AVANÇADA POR PRODUTO
# ===============================

st.subheader("🔮 Forecast Inteligente por Produto")

for produto in df_filtrado["produto"].unique():

    df_prod = df[df["produto"] == produto]
    df_mensal = df_prod.groupby("mes")["vendido"].sum().reset_index()

    if len(df_mensal) < 3:
        continue

    df_mensal = df_mensal.sort_values("mes").tail(3)

    X = df_mensal["mes"].values.reshape(-1, 1)
    y = df_mensal["vendido"].values

    model = LinearRegression()
    model.fit(X, y)

    proximo_mes = np.array([[df_mensal["mes"].max() + 1]])
    previsao = model.predict(proximo_mes)[0]
    tendencia = model.coef_[0]

    df_plot = df_mensal.copy()
    df_plot["tipo"] = "Histórico"

    df_future = pd.DataFrame({
        "mes": [df_mensal["mes"].max() + 1],
        "vendido": [previsao],
        "tipo": ["Previsão"]
    })

    df_plot = pd.concat([df_plot, df_future])

    fig = px.line(
        df_plot,
        x="mes",
        y="vendido",
        color="tipo",
        markers=True,
        template="plotly_dark",
        title=f"{produto} - Histórico + Previsão"
    )

    st.plotly_chart(fig, use_container_width=True)

    if tendencia < 0:
        st.warning(f"⚠️ {produto} apresenta tendência de queda.")

    st.divider()

# ===============================
# RESUMO EXECUTIVO
# ===============================

st.subheader("📌 Resumo Executivo Inteligente")

resumo = []

if desperdicio_medio < 10:
    resumo.append("🟢 O desperdício está saudável.")
elif desperdicio_medio < 20:
    resumo.append("🟡 O desperdício está moderado.")
else:
    resumo.append("🔴 O desperdício está crítico.")

if eficiencia_venda < 40:
    resumo.append("🔴 Eficiência de venda crítica.")
elif eficiencia_venda < 70:
    resumo.append("🟡 Eficiência moderada.")
else:
    resumo.append("🟢 Eficiência alta.")

if abs(producao_nao_explicada) > 10:
    resumo.append("⚠️ Produção não explicada relevante.")

for frase in resumo:
    st.write("• " + frase)

# ============================================================
# 📥 IMPORTAÇÃO HISTÓRICA OFICIAL (MESES ANTERIORES)
# ============================================================

from sqlalchemy import text

st.subheader("📥 Importação Histórica de Operações")

arquivo = st.file_uploader("Upload Excel Histórico", type=["xlsx"])

if arquivo is not None:

    df_import = pd.read_excel(arquivo)

    obrigatorias = ["data", "produto", "produzido", "vendido", "enviado_filial", "sobra_real"]

    if not all(col in df_import.columns for col in obrigatorias):
        st.error("Planilha fora do padrão. Verifique as colunas obrigatórias.")
    else:

        inseridos = 0
        atualizados = 0
        erros = 0

        for _, row in df_import.iterrows():

            try:
                produto_id = pd.read_sql(
                    f"SELECT id FROM produtos WHERE nome = '{row['produto']}'",
                    engine
                )["id"].values[0]

                check_query = text("""
                    SELECT id FROM operacao_diaria
                    WHERE data = :data AND produto_id = :produto_id
                """)

                with engine.connect() as conn:

                    existente = conn.execute(check_query, {
                        "data": row["data"],
                        "produto_id": int(produto_id)
                    }).fetchone()

                    if existente:

                        update_query = text("""
                            UPDATE operacao_diaria
                            SET produzido = :produzido,
                                vendido = :vendido,
                                enviado_filial = :enviado,
                                sobra_real = :sobra
                            WHERE data = :data AND produto_id = :produto_id
                        """)

                        conn.execute(update_query, {
                            "data": row["data"],
                            "produto_id": int(produto_id),
                            "produzido": row["produzido"],
                            "vendido": row["vendido"],
                            "enviado": row["enviado_filial"],
                            "sobra": row["sobra_real"]
                        })

                        atualizados += 1

                    else:

                        insert_query = text("""
                            INSERT INTO operacao_diaria
                            (data, produto_id, produzido, vendido, enviado_filial, sobra_real)
                            VALUES
                            (:data, :produto_id, :produzido, :vendido, :enviado, :sobra)
                        """)

                        conn.execute(insert_query, {
                            "data": row["data"],
                            "produto_id": int(produto_id),
                            "produzido": row["produzido"],
                            "vendido": row["vendido"],
                            "enviado": row["enviado_filial"],
                            "sobra": row["sobra_real"]
                        })

                        inseridos += 1

                    conn.commit()

            except Exception as e:
                erros += 1

        st.success("Importação concluída!")
        st.write(f"✔ Inseridos: {inseridos}")
        st.write(f"🔁 Atualizados: {atualizados}")
        st.write(f"❌ Erros: {erros}")