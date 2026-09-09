#!/usr/bin/env bash
# ============================================================
# YouTube Cutter — Script de Inicialização
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

# Carregar nvm se necessário
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       YouTube Cutter — Iniciando      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Verificar dependências básicas ────────────────────────────
if [ ! -f "backend/venv/bin/python" ]; then
    error "Ambiente virtual não encontrado. Execute ./setup.sh primeiro."
fi

if ! command -v ffmpeg &>/dev/null; then
    error "FFmpeg não encontrado. Execute ./setup.sh primeiro."
fi

if ! command -v node &>/dev/null; then
    error "Node.js não encontrado. Execute ./setup.sh primeiro."
fi

# ── Criar diretórios se não existirem ─────────────────────────
mkdir -p storage/temp storage/jobs storage/output logs

# ── Carregar variáveis de ambiente ───────────────────────────
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

APP_PORT="${APP_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# ── Função para matar processos filhos ao sair ───────────────
cleanup() {
    echo ""
    info "Encerrando serviços..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}Encerrado.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Iniciar Backend ───────────────────────────────────────────
info "Iniciando backend na porta $APP_PORT..."
PYTHONPATH=backend backend/venv/bin/python -m uvicorn main:app \
    --app-dir backend \
    --host "${BIND_HOST:-127.0.0.1}" \
    --port "$APP_PORT" \
    --log-level "$UVICORN_LOG_LEVEL" \
    2>&1 | tee -a logs/backend.log &
BACKEND_PID=$!

# Aguardar backend estar pronto
info "Aguardando backend iniciar..."
for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$APP_PORT/api/health" >/dev/null 2>&1; then
        success "Backend pronto."
        break
    fi
    if [ "$i" -eq 30 ]; then
        error "Backend não iniciou em 30 segundos. Verifique logs/backend.log"
    fi
    sleep 1
done

# ── Iniciar Frontend ──────────────────────────────────────────
info "Iniciando frontend na porta $FRONTEND_PORT..."
cd frontend
npm run dev -- --port "$FRONTEND_PORT" --host 127.0.0.1 \
    2>&1 | tee -a ../logs/frontend.log &
FRONTEND_PID=$!
cd ..

# Aguardar frontend estar pronto
info "Aguardando frontend iniciar..."
for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:$FRONTEND_PORT" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     YouTube Cutter está rodando!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Acesse: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo "  Pressione Ctrl+C para encerrar."
echo ""

# Aguardar
wait $BACKEND_PID $FRONTEND_PID

