from app.models import PerfilSchema, RankingRequestSchema
from app.services import ranking_service


def test_ranquear_deve_retornar_um_item_rankeado_por_ativo_enviado():
    request = RankingRequestSchema(
        correlationId="550e8400-e29b-41d4-a716-446655440000",
        modulo="VARIAVEL",
        perfil=PerfilSchema(
            perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
            objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
        ),
        ativos=[
            dict(codigo="TAEE3", tipo="ACAO", setor="Energia", preco=38.42, dy=6.8, variacao30d=5.1),
            dict(codigo="PETR4", tipo="ACAO", setor="Petróleo", preco=38.90, dy=14.2, variacao30d=-0.4),
        ],
    )

    response = ranking_service.ranquear(request)

    assert len(response.ativos) == 2
    assert {a.codigo for a in response.ativos} == {"TAEE3", "PETR4"}