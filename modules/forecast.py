from sklearn.linear_model import LinearRegression
import numpy as np

def prever(df_mensal):
    if len(df_mensal) < 3:
        return None, None

    X = df_mensal["mes"].values.reshape(-1, 1)
    y = df_mensal["vendido"].values

    model = LinearRegression()
    model.fit(X, y)

    proximo = np.array([[df_mensal["mes"].max() + 1]])
    previsao = model.predict(proximo)[0]

    return previsao, model.coef_[0]