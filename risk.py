def calcular_score(desperdicio, eficiencia, nao_explicada):
    score = 0
    score += min(desperdicio * 2, 40)
    score += min((100 - eficiencia) * 0.4, 40)
    score += min(abs(nao_explicada) * 0.2, 20)
    return min(score, 100)