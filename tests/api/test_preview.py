from fastapi.testclient import TestClient

from main import create_app

CORRELATION_ID = "550e8400-e29b-41d4-a716-446655440000"


def perfil_dict():
    return dict(
        perfilRisco="MODERADO", horizonte="LONGO_PRAZO",
        objetivo="RENDA_PASSIVA", valorDisponivel=5000.0,
    )


def ativo_ranking_dict():
    return dict(
        codigo="TAEE3", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1, volatilidade="BAIXA",
    )


def ativo_resumo_dict():
    return dict(
        codigo="TAEE3", nome="Taesa", tipo="ACAO", setor="Energia Elétrica",
        preco=38.42, dy=6.8, variacao30d=5.1,
    )


class TestPreviewHabilitado:
    client = TestClient(create_app(enable_preview=True, start_consumers=False))

    def test_ranking_preview_deve_retornar_200_com_lista_rankeada(self):
        payload = {
            "correlationId": CORRELATION_ID,
            "modulo": "VARIAVEL",
            "perfil": perfil_dict(),
            "ativos": [ativo_ranking_dict()],
        }

        response = self.client.post("/ranking/preview", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["correlationId"] == CORRELATION_ID
        assert body["ativos"][0]["codigo"] == "TAEE3"

    def test_ranking_preview_deve_retornar_422_quando_payload_invalido(self):
        response = self.client.post("/ranking/preview", json={"correlationId": "nao-e-uuid"})

        assert response.status_code == 422

    def test_resumo_preview_deve_retornar_200_com_texto_stub(self):
        payload = {
            "correlationId": CORRELATION_ID,
            "modulo": "VARIAVEL",
            "perfil": perfil_dict(),
            "ativo": ativo_resumo_dict(),
        }

        response = self.client.post("/resumo/preview", json=payload)

        assert response.status_code == 200
        assert response.json()["resumo"] is not None


class TestPreviewDesabilitado:
    client = TestClient(create_app(enable_preview=False, start_consumers=False))

    def test_ranking_preview_nao_deve_existir_quando_desabilitado(self):
        response = self.client.post("/ranking/preview", json={})
        assert response.status_code == 404

    def test_resumo_preview_nao_deve_existir_quando_desabilitado(self):
        response = self.client.post("/resumo/preview", json={})
        assert response.status_code == 404