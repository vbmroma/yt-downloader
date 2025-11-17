📥 YouTube Downloader (Web App)
Um aplicativo web simples, construído com Flask e yt-dlp, para baixar vídeos e áudios do YouTube. A interface inclui pré-visualização, seleção de formato, barra de progresso em tempo real e uma galeria de vídeos baixados.

✨ Funcionalidades
Pré-visualização: Cole um link do YouTube para ver o título e a miniatura (thumbnail) antes de baixar.

Seleção de Formato: Escolha entre baixar o vídeo completo (MP4) ou somente o áudio (M4A/MP3).

Barra de Progresso: Acompanhe o download em tempo real com uma barra de progresso que usa WebSockets (Flask-SocketIO).

Galeria de Downloads: Todos os downloads são listados com thumbnail e título.

Visualização no Navegador: Clique em "Visualizar" para abrir o vídeo ou áudio baixado em uma nova aba para reprodução imediata.

Pós-processamento: Utiliza FFmpeg automaticamente para corrigir arquivos MP4 (movendo o "moov atom"), permitindo que o streaming/visualização no navegador funcione perfeitamente.

🛠️ Tecnologias Utilizadas
Backend:

Python 3

Flask: Microframework web.

Flask-SocketIO: Para comunicação em tempo real (barra de progresso).

yt-dlp: O motor de download de vídeos.

Frontend:

HTML5

Bootstrap 5: Para o estilo "simples e bonito".

JavaScript: Para lógica do cliente (Fetch API, Socket.IO Client).

Dependências Externas:

FFmpeg: Essencial para o pós-processamento e correção dos vídeos.

🚀 Guia de Instalação e Execução
Siga estes passos para configurar e executar o projeto localmente.

1. Pré-requisitos (Obrigatório)
Esta aplicação exige que o FFmpeg esteja instalado e acessível no PATH do seu sistema operacional.

Por quê? O yt-dlp baixa vídeos em fragmentos. O FFmpeg é usado para "reparar" o arquivo .mp4 final, movendo seu índice (o "moov atom") para o início. Sem isso, a função "Visualizar" no navegador (tela preta) falhará.

Como instalar o FFmpeg:
Windows:

Baixe o "essentials build" de https://www.gyan.dev/ffmpeg/builds/.

Extraia o arquivo (ex: para C:\ffmpeg).

Adicione a pasta bin (ex: C:\ffmpeg\bin) ao PATH das "Variáveis de Ambiente" do seu sistema.

macOS (via Homebrew):

Bash

brew install ffmpeg
Linux (Debian/Ubuntu):

Bash

sudo apt update
sudo apt install ffmpeg
➡️ Verifique a instalação: Feche e reabra seu terminal. Digite ffmpeg -version. Se você vir as informações da versão, está funcionando.

2. Instalação do Projeto
Clone ou baixe os arquivos para uma pasta (ex: C:\dev\yt-downloader).

Crie um ambiente virtual (recomendado):

Bash

python -m venv venv
Ative o ambiente virtual:

Windows: .\venv\Scripts\activate

Mac/Linux: source venv/bin/activate

Instale as dependências do Python:

Bash

pip install Flask flask-socketio yt-dlp
3. Executando a Aplicação
Com seu ambiente virtual ativado, execute o script app.py:

Bash

python app.py
O servidor será iniciado (geralmente em modo de depuração).

INFO: Iniciando servidor com SocketIO...
* Running on http://127.0.0.1:5000
Abra seu navegador e acesse: http://127.0.0.1:5000

📁 Estrutura do Projeto
yt-downloader/
│
├── app.py             # O servidor backend (Flask, SocketIO, yt-dlp)
│
├── templates/
│   └── index.html     # O frontend (HTML, CSS, JavaScript)
│
└── downloads/         # Pasta onde os vídeos, áudios e arquivos .meta são salvos
