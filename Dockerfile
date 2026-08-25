FROM python:3.11-slim

WORKDIR /app

# Copia só o requirements.txt primeiro pra aproveitar cache de camada do Docker —
# as dependências só são reinstaladas se o requirements.txt mudar, não a cada
# alteração de código-fonte.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py .

# Usuário não-root — mesma prática de segurança do Dockerfile do Java
RUN useradd --create-home investai
USER investai

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]