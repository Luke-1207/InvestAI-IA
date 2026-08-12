# 🧠 InvestAI IA

### Microsserviço de Inteligência Artificial da Plataforma InvestAI

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-green?style=for-the-badge&logo=fastapi)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-AMQP-orange?style=for-the-badge&logo=rabbitmq)
![Status](https://img.shields.io/badge/status%20em%20desenvolvimento-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

# 📖 Sobre o serviço

O **InvestAI IA** é o microsserviço responsável pela camada de inteligência da plataforma InvestAI:

- 🧮 Ranqueamento determinístico de ativos por perfil de investidor
- 🧠 Geração de resumos em linguagem natural via LLM externo (Anthropic/OpenAI)
- 📨 Comunicação assíncrona com o backend principal (Java) via RabbitMQ

Não é chamado diretamente pelo frontend — todo tráfego passa pelo `InvestAI-API` (Spring Boot), que publica mensagens no RabbitMQ e este serviço consome, processa e responde.

---

# ⚙️ Stack Tecnológica

- Python 3.11
- FastAPI
- Pika (cliente RabbitMQ)
- httpx (cliente HTTP assíncrono para o LLM externo)
- Pydantic (validação e contratos de mensagem)
- python-dotenv

---

# 🚀 Como Executar

## Pré-requisitos
- Python 3.11
- RabbitMQ rodando localmente (ou via Docker)

## Clone o projeto
```bash
git clone https://github.com/Luke-1207/InvestAI-IA
cd InvestAI-IA
```

## Crie e ative o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate
```

## Instale as dependências
```bash
pip install -r requirements.txt
```

## Configure as variáveis de ambiente
```bash
copy .env.example .env
```

## Execute a aplicação
```bash
uvicorn main:app --reload --port 8000
```

---

# 🔑 Variáveis de Ambiente
- RABBITMQ_URL= URL do Serviço de mensageria RabbitMQ em execução
- LLM_API_KEY= chave de API de LLM
- LLM_PROVIDER= provider de LLM
- ENABLE_PREVIEW_ENDPOINTS= habilitar preview de endpoints
---

# 📨 Comunicação Assíncrona

RabbitMQ é usado para:
- Receber pedidos de ranqueamento do `InvestAI-API`
- Receber pedidos de geração de resumo em linguagem natural
- Publicar as respostas de volta nas filas de retorno

---

# 👨‍💻 Autor

## Lucas Fabiano
### Backend Developer • Java • Python • Software Architecture

[![](https://img.shields.io/badge/GitHub-Profile-black?style=for-the-badge&logo=github)](https://github.com/Luke-1207)