import pandas as pd

def calcular_kpis(df):

    total_produzido = df["produzido"].sum()
    total_vendido = df["vendido"].sum()
    total_enviado = df["enviado_filial"].sum()
    total_sobra = df["sobra_real"].sum()

    desperdicio_medio = (total_sobra / total_produzido) * 100 if total_produzido > 0 else 0
    eficiencia_media = (total_vendido / total_produzido) * 100 if total_produzido > 0 else 0

    return {
        "total_produzido": total_produzido,
        "total_vendido": total_vendido,
        "total_enviado": total_enviado,
        "desperdicio_medio": desperdicio_medio,
        "eficiencia_media": eficiencia_media
    }