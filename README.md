# YouTube Cutter

Aplicação web local para cortar vídeos do YouTube em clipes para TikTok, Instagram Reels e YouTube Shorts.

> ⚠️ **Aviso sobre direitos autorais:** Esta ferramenta é destinada ao processamento de conteúdo que você tenha autorização para baixar e reutilizar. O usuário é responsável por possuir os direitos necessários sobre o conteúdo processado. Não utilize esta ferramenta para contornar medidas de proteção de conteúdo.

---

## Funcionalidades

- 🔗 Suporte a canais, playlists e vídeos individuais do YouTube
- 📋 Listagem e seleção de vídeos com filtros e ordenação
- ✂️ Cortes automáticos por duração configurável
- 🎬 Conversão de formato: 9:16 (TikTok/Shorts), 16:9, 1:1, Original
- 📦 Exportação em ZIP organizado por vídeo
- 📊 Progresso em tempo real com estimativa de tempo
- 🗂️ Histórico de trabalhos realizados
- 🧹 Limpeza automática de arquivos temporários

---

## Requisitos

| Dependência | Versão Mínima | Instalação (Fedora) |
|---|---|---|
| Python | 3.10+ | `sudo dnf install python3` |
| FFmpeg | Qualquer | Ver abaixo |
| Node.js | 18+ | Instalado pelo setup.sh via nvm |
| yt-dlp | Qualquer | Instalado pelo setup.sh |

### Instalando FFmpeg no Fedora

O FFmpeg precisa do repositório RPM Fusion:

```bash
# Habilitar RPM Fusion
sudo dnf install \
  https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

# Instalar FFmpeg
sudo dnf install ffmpeg
```

---

## Instalação

```bash
# 1. Clone ou extraia o projeto
cd youtube-cutter

# 2. Execute o setup (instala todas as dependências)
chmod +x setup.sh start.sh
./setup.sh
```

O `setup.sh` irá:
- Verificar FFmpeg e Python
- Criar ambiente virtual Python
- Instalar dependências Python (`requirements.txt`)
- Instalar yt-dlp
- Instalar Node.js via nvm (se necessário)
- Instalar dependências do frontend

---

## Configuração

```bash
# O setup.sh cria o .env automaticamente a partir do .env.example
# Edite conforme necessário:
nano .env
```

Principais variáveis:

```env
APP_PORT=8000          # Porta do backend
FRONTEND_PORT=3000     # Porta do frontend
MAX_CONCURRENT_JOBS=2  # Vídeos processados simultaneamente
TEMP_FILE_TTL_HOURS=24 # Horas para manter temporários
ZIP_FILE_TTL_HOURS=72  # Horas para manter ZIPs
LOG_LEVEL=INFO
```

---

## Iniciando

```bash
./start.sh
```

Acesse no navegador:

```
http://localhost:3000
```

Para encerrar: `Ctrl+C`

---

## Uso

### Fluxo completo

1. **Fonte** — Cole a URL do YouTube (canal, playlist ou vídeo)
2. **Vídeos** — Selecione os vídeos desejados
3. **Cortes** — Escolha o modo de corte (por duração)
4. **Configurações** — Formato, resolução, legenda, zoom, áudio
5. **Resumo** — Revise e inicie o processamento
6. **Processando** — Acompanhe o progresso em tempo real
7. **Concluído** — Gere o ZIP
8. **Download** — Baixe o arquivo ZIP

### URLs suportadas

```
https://www.youtube.com/@canal
https://www.youtube.com/channel/UCxxxxxxxx
https://www.youtube.com/c/Canal
https://www.youtube.com/playlist?list=XXXXXXXX
https://www.youtube.com/watch?v=XXXXXXXX
https://youtu.be/XXXXXXXX
```

---

## Estrutura do ZIP gerado

```
cortes_youtube_2026-09-02.zip
├── Video_01_Titulo/
│   ├── corte_001.mp4
│   ├── corte_002.mp4
│   └── corte_003.mp4
├── Video_02_Titulo/
│   ├── corte_001.mp4
│   └── corte_002.mp4
└── ...
```

---

## Estrutura do Projeto

```
youtube-cutter/
├── frontend/                  # React + TypeScript + Vite
│   └── src/
│       ├── api/               # Cliente HTTP tipado
│       ├── components/        # Componentes reutilizáveis
│       │   ├── steps/         # Etapas do wizard
│       │   └── ui/            # UI base (Button, Card, etc.)
│       ├── hooks/             # useSSE e outros hooks
│       ├── pages/             # Páginas (History)
│       └── types/             # TypeScript types
│
├── backend/                   # Python FastAPI
│   ├── api/routes/            # Endpoints HTTP
│   ├── services/              # Serviços modulares
│   │   ├── youtube_service.py # yt-dlp: metadados + download
│   │   ├── ffmpeg_service.py  # Processamento FFmpeg
│   │   ├── video_service.py   # Orquestrador por vídeo
│   │   ├── zip_service.py     # Geração do ZIP
│   │   ├── job_service.py     # CRUD de jobs (SQLite)
│   │   ├── disk_service.py    # Verificação de espaço
│   │   ├── transcription_service.py  # [STUB] Whisper
│   │   ├── ai_clip_analyzer.py       # [STUB] IA modular
│   │   └── subtitle_service.py       # [STUB] Legendas
│   ├── workers/               # Background tasks
│   ├── models/                # SQLAlchemy + Pydantic
│   └── utils/                 # Utilitários
│
├── storage/
│   ├── temp/                  # Downloads temporários
│   ├── jobs/                  # Banco SQLite
│   └── output/                # Cortes finais + ZIPs
│
├── logs/                      # Logs da aplicação
├── .env.example
├── setup.sh
├── start.sh
└── README.md
```

---

## Solução de Problemas

### "Backend não iniciou"
```bash
# Verifique o log do backend
tail -50 logs/backend.log

# Teste manualmente
backend/venv/bin/python -m uvicorn backend.main:app --port 8000
```

### "yt-dlp não encontrado"
```bash
backend/venv/bin/pip install yt-dlp
```

### "FFmpeg não encontrado"
```bash
sudo dnf install ffmpeg
# Se não encontrar o pacote, habilite o RPM Fusion (ver acima)
```

### "Erro ao baixar vídeo"
- Verifique se o vídeo é público
- Atualize o yt-dlp: `backend/venv/bin/pip install -U yt-dlp`

### "Node.js não encontrado após setup"
```bash
source ~/.bashrc  # ou ~/.zshrc
# Ou ative o nvm manualmente:
source ~/.nvm/nvm.sh
node --version
```

### Permissão negada nos scripts
```bash
chmod +x setup.sh start.sh
```

---

## Logs

```bash
# Log do backend
tail -f logs/app.log

# Log do backend (uvicorn)
tail -f logs/backend.log

# Log do frontend
tail -f logs/frontend.log
```

---

## Como adicionar integração com IA (Melhores Momentos)

A arquitetura já está preparada. Edite o arquivo:

```
backend/services/ai_clip_analyzer.py
```

A interface é:

```python
class AIClipAnalyzer:
    async def find_best_moments(
        self,
        transcript: list[dict],  # [{start, end, text}]
        count: int,
        min_duration: int,       # segundos
        max_duration: int,       # segundos
        style: str               # informative|funny|controversial|etc
    ) -> list[dict]:             # [{start_sec, end_sec, score, reason}]
        ...
```

### Exemplo com OpenAI:
1. Adicione `OPENAI_API_KEY` no `.env`
2. Instale: `backend/venv/bin/pip install openai`
3. Implemente `find_best_moments` usando a API OpenAI
4. O sistema usará automaticamente quando o modo "Melhores Momentos" for selecionado

### Como adicionar Whisper (Legendas/Transcrição):
1. Instale: `backend/venv/bin/pip install openai-whisper`
2. Edite `backend/services/transcription_service.py`
3. Implemente o método `transcribe()`
4. As legendas estarão disponíveis na interface

---

## Formato de Vídeo — Como Funciona

### 9:16 (TikTok/Reels/Shorts) a partir de vídeo horizontal:
O FFmpeg aplica crop centralizado mantendo a proporção:
```
scale=ih*9/16*2:ih*2, crop=ih*9/16:ih
```

### 1:1 (Quadrado):
```
crop=min(iw\,ih):min(iw\,ih), scale=1080:1080
```

---

## Licença

MIT — uso pessoal e não comercial.

Lembre-se: respeite os Termos de Serviço do YouTube e os direitos autorais dos criadores de conteúdo.

