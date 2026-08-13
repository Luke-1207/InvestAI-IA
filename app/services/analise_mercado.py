from typing import Optional

from app.models import AtivoVariavelSchema


def calcular_posicao_52_semanas(ativo: AtivoVariavelSchema) -> Optional[str]:
    """
    Calcula a posição do preço atual dentro da faixa de 52 semanas de forma
    determinística — cobre os passos 2 e 4 do fluxo documentado (posição vs.
    histórico recente). Como o schema não tem um campo de "preço médio
    histórico" isolado, usa-se a posição relativa dentro do mín/máx como
    proxy — comunica a mesma informação ao usuário leigo sem exigir um
    campo novo no contrato de mensagem.
    """
    if not ativo.variacao52s:
        return None

    minimo, maximo = ativo.variacao52s.min, ativo.variacao52s.max
    if maximo <= minimo:
        return None

    posicao = max(0.0, min(100.0, (ativo.preco - minimo) / (maximo - minimo) * 100))

    if posicao >= 80:
        return f"próxima ao topo da faixa de 52 semanas ({posicao:.0f}% do intervalo)"
    if posicao <= 20:
        return f"próxima à base da faixa de 52 semanas ({posicao:.0f}% do intervalo)"
    return f"no meio da faixa de 52 semanas ({posicao:.0f}% do intervalo)"


def calcular_dy_vs_media_setorial(ativo: AtivoVariavelSchema) -> Optional[str]:
    """Compara o DY do ativo com a média setorial — cobre o passo 3 do fluxo documentado."""
    if ativo.mediaSetorialDY is None:
        return None

    diferenca = ativo.dy - ativo.mediaSetorialDY

    if diferenca > 0.1:
        return f"DY de {ativo.dy}% está {diferenca:.1f} pontos percentuais acima da média do setor ({ativo.mediaSetorialDY}%)"
    if diferenca < -0.1:
        return f"DY de {ativo.dy}% está {abs(diferenca):.1f} pontos percentuais abaixo da média do setor ({ativo.mediaSetorialDY}%)"
    return f"DY de {ativo.dy}% está alinhado à média do setor ({ativo.mediaSetorialDY}%)"