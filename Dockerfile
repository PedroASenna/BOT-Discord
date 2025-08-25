# Stage 1: Build com dependências
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Imagem final de produção
FROM python:3.11-slim

WORKDIR /app

# Copiar dependências instaladas do stage anterior
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copiar código da aplicação
COPY ./bot /app/bot

# Criar diretório de logs
RUN mkdir -p /app/logs

# Definir o comando para rodar o bot
CMD ["python", "-m", "bot.src.bot"]