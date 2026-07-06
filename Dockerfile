# ============================================
# 1. BASE IMAGE
# ============================================
# Usa Python 3.11 slim (leve e segura)
FROM python:3.11-slim

# ============================================
# 2. ENVIRONMENT VARIABLES
# ============================================
# Define variáveis de ambiente para o Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ============================================
# 3. WORK DIRECTORY
# ============================================
# Cria e define o diretório de trabalho
WORKDIR /app

# ============================================
# 4. INSTALL DEPENDENCIES
# ============================================
# Copia apenas o requirements.txt primeiro (cache de camadas)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# 5. COPY APPLICATION CODE
# ============================================
# Copia o código fonte
COPY src/ ./src/
COPY main.py .
COPY cli.py .

# ============================================
# 6. COPY CREDENTIALS (OPCIONAL)
# ============================================
# Comentado: as credenciais devem ser fornecidas via volume ou secrets
# COPY credenciais.json .

# ============================================
# 7. EXPOSE PORT
# ============================================
# Porta usada pelo Cloud Run
EXPOSE 8080

# ============================================
# 8. HEALTHCHECK
# ============================================
# Verifica se o serviço está vivo
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# ============================================
# 9. START COMMAND
# ============================================
# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]