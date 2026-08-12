from app.models import PerfilSchema, ResumoRequestSchema
from app.services import resumo_service


def test_gerar_resumo_deve_retornar_texto_stub_sem_erro():
    request = ResumoRequestSchema(
        correlationId="550e8400-e29b-41d4-a716-446655440000",
        modulo="VARIAVEL",
        perfil=PerfilSchema(
            perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
            objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
        ),
        ativo=dict(codigo="TAEE3", tipo="ACAO", setor="Energia", preco=38.42, dy=6.8, variacao30d=5.1),
    )

    response = resumo_service.gerar_resumo(request)

    assert response.resumo is not None
    assert response.erro is None