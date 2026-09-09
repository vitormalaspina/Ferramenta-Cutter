#!/usr/bin/env bash
# ============================================================
# YouTube Cutter — Script de Instalação
# Compatível com: Fedora / RHEL / Linux
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
warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       YouTube Cutter — Setup         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Verificar Python ──────────────────────────────────────────
info "Verificando Python..."
if ! command -v python3 &>/dev/null; then
    error "Python 3 não encontrado. Instale com: sudo dnf install python3"
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PYTHON_VERSION encontrado."

# ── Verificar FFmpeg ──────────────────────────────────────────
info "Verificando FFmpeg..."
if ! command -v ffmpeg &>/dev/null; then
    warning "FFmpeg não encontrado."
    echo ""
    echo "  Instale o FFmpeg com:"
    echo "  sudo dnf install ffmpeg"
    echo "  (pode precisar do repositório RPM Fusion)"
    echo ""
    echo "  Para habilitar RPM Fusion:"
    echo "  sudo dnf install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-\$(rpm -E %fedora).noarch.rpm"
    echo "  sudo dnf install https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-\$(rpm -E %fedora).noarch.rpm"
    echo ""
    error "Instale o FFmpeg e execute o setup novamente."
fi
FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')
success "FFmpeg $FFMPEG_VERSION encontrado."

# ── Criar diretórios de storage ───────────────────────────────
info "Criando diretórios de armazenamento..."
mkdir -p storage/temp storage/jobs storage/output logs
success "Diretórios criados."

# ── Copiar .env ───────────────────────────────────────────────
if [ ! -f ".env" ]; then
    info "Criando arquivo .env a partir do .env.example..."
    cp .env.example .env
    success ".env criado. Edite conforme necessário."
else
    info ".env já existe, mantendo configurações atuais."
fi

# ── Virtualenv Python ─────────────────────────────────────────
info "Configurando ambiente virtual Python..."
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
    success "Virtualenv criado em backend/venv"
else
    info "Virtualenv já existe."
fi

VENV_PIP="backend/venv/bin/pip"
VENV_PYTHON="backend/venv/bin/python"

info "Atualizando pip..."
"$VENV_PIP" install --upgrade pip --quiet

info "Instalando dependências Python..."
"$VENV_PIP" install -r backend/requirements.txt --quiet
success "Dependências Python instaladas."

# ── Verificar/instalar yt-dlp ─────────────────────────────────
info "Verificando yt-dlp..."
if ! "$VENV_PYTHON" -c "import yt_dlp" 2>/dev/null; then
    info "Instalando yt-dlp..."
    "$VENV_PIP" install yt-dlp --quiet
fi
YTDLP_VERSION=$("$VENV_PYTHON" -c "import yt_dlp; print(yt_dlp.version.__version__)" 2>/dev/null || echo "instalado")
success "yt-dlp $YTDLP_VERSION disponível."

# ── Node.js via nvm ───────────────────────────────────────────
info "Verificando Node.js..."

NVM_DIR="$HOME/.nvm"

if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js $NODE_VERSION já instalado."
else
    info "Node.js não encontrado. Instalando via nvm..."

    if [ ! -d "$NVM_DIR" ]; then
        info "Instalando nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi

    # Carregar nvm para este script
    export NVM_DIR="$HOME/.nvm"
    # shellcheck disable=SC1091
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    info "Instalando Node.js LTS..."
    nvm install --lts
    nvm use --lts

    NODE_VERSION=$(node --version)
    success "Node.js $NODE_VERSION instalado."
fi

# Garantir npm disponível
if ! command -v npm &>/dev/null; then
    # Tentar carregar nvm novamente
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

if ! command -v npm &>/dev/null; then
    error "npm não encontrado. Verifique a instalação do Node.js."
fi

NPM_VERSION=$(npm --version)
success "npm $NPM_VERSION disponível."

# ── Instalar dependências frontend ────────────────────────────
info "Instalando dependências do frontend..."
cd frontend
npm install --silent
cd ..
success "Dependências frontend instaladas."

# ── Verificação final ─────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Instalação concluída com sucesso! ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Para iniciar a aplicação:"
echo ""
echo -e "    ${YELLOW}./start.sh${NC}"
echo ""
echo "  Acesse no navegador:"
echo ""
echo -e "    ${BLUE}http://localhost:3000${NC}"
echo ""

