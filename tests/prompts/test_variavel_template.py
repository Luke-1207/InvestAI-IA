from app.models import AtivoVariavelSchema, PerfilSchema
from app.prompts import variavel_template


def perfil():
    return PerfilSchema(
        perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
        objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
    )


def test_montar_prompt_deve_incluir_dados_completos_do_ativo():
    ativo = AtivoVariavelSchema(
        codigo="TAEE3", nome="Taesa", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1, pl=12.4, pvp=1.3,
        variacao52s={"min": 28.10, "max": 41.90}, mediaSetorialDY=5.2,
    )

    prompt = variavel_template.montar_prompt(ativo, perfil())

    assert "TAEE3" in prompt
    assert "Taesa" in prompt
    assert "12.4x" in prompt
    assert "MODERADO" in prompt


def test_montar_prompt_deve_lidar_com_campos_opcionais_ausentes():
    ativo = AtivoVariavelSchema(
        codigo="TAEE3", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1,
    )

    prompt = variavel_template.montar_prompt(ativo, perfil())

    assert "não disponível" in prompt
    assert "None" not in prompt