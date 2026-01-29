# Usa uma imagem oficial leve do Python
FROM python:3.11-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Variáveis de ambiente para evitar arquivos .pyc e logs presos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para o driver pg8000/psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para dentro do container
COPY . .

# Expõe a porta 8000 (padrão do Uvicorn)
EXPOSE 8000

# Comando para rodar a API quando o container subir
# host 0.0.0.0 é OBRIGATÓRIO para Docker
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]