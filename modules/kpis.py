def calcular_kpis(df):
    total_produzido = df["produzido"].sum()
    total_vendido = df["vendido"].sum()
    total_enviado = df["enviado_filial"].sum()
    total_sobra = df["sobra_real"].sum()

    desperdicio = (total_sobra / total_produzido) * 100 if total_produzido > 0 else 0
    eficiencia = (total_vendido / total_produzido) * 100 if total_produzido > 0 else 0

    return {
        "produzido": total_produzido,
        "vendido": total_vendido,
        "enviado": total_enviado,
        "sobra": total_sobra,
        "desperdicio": desperdicio,
        "eficiencia": eficiencia
    }