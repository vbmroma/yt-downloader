import os
import yt_dlp
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu-segredo-aqui!' # Necessario para SocketIO
socketio = SocketIO(app)

# Configura o logging
logging.basicConfig(level=logging.INFO)

# Caminho da pasta de downloads
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """ Rota principal que renderiza o frontend """
    return render_template('index.html')


def get_safe_filename(title, extension, prefix=""):
    """ Limpa o nome do arquivo """
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
    return f"{prefix}{safe_title}.{extension}"


@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    """ 
    Endpoint para buscar informacoes do video (preview).
    (Sem alteracoes, continua igual)
    """
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL nao fornecida'}), 400

        ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        title = info.get('title', 'Video Sem Titulo')
        thumbnail_url = info.get('thumbnail', '')

        formats = info.get('formats', [])
        has_video = any(
            f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' 
            for f in formats
        )
        has_audio = any(f.get('vcodec') == 'none' and f.get('acodec') != 'none' for f in formats)

        info_out = {
            'title': title,
            'thumbnail_url': thumbnail_url,
            'has_video': has_video,
            'has_audio': has_audio
        }
        return jsonify(info_out)
        
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp falhou ao extrair info: {e}")
        return jsonify({'error': 'Falha ao buscar info do video. Link invalido ou privado?'}), 500
    except Exception as e:
        logging.error(f"Erro generico ao buscar info: {e}")
        return jsonify({'error': str(e)}), 500


@socketio.on('start_download')
def handle_download_event(data):
    """ 
    Esta funcao e chamada quando o frontend emite o evento 'start_download'.
    Substitui a antiga rota '/download'.
    """
    url = data.get('url')
    format_choice = data.get('format', 'mp4')
    
    if not url:
        emit('download_error', {'error': 'URL nao fornecida'})
        return

    try:
        # 1. Extrai info primeiro (para o nome do arquivo e metadados)
        info_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video_baixado')
            thumbnail = info.get('thumbnail', '')

        # 2. Define o "Hook de Progresso"
        # Esta funcao interna sera chamada pelo yt-dlp em cada atualizacao
        def progress_hook(d):
            if d['status'] == 'downloading':
                # USA OS BYTES TOTAIS PARA CALCULAR - MAIS CONFIAVEL
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes')
                
                if total_bytes and downloaded_bytes:
                    percent = (downloaded_bytes / total_bytes) * 100
                    # Emite o progresso de volta para o navegador
                    emit('download_progress', {'percent': percent})
                # Se nao tivermos os bytes, nao enviamos o progresso
            
            if d['status'] == 'finished':
                # O download terminou, vamos salvar os metadados
                # (O restante desta funcao continua igual)
                final_filename = os.path.basename(d.get('filename'))
                meta_filename = final_filename + '.meta'
                meta_filepath = os.path.join(DOWNLOAD_FOLDER, meta_filename)
                
                meta_data = {
                    'title': title,
                    'thumbnail': thumbnail,
                    'original_url': url,
                    'downloaded_file': final_filename
                }
                
                with open(meta_filepath, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f)

        # 3. Define as opcoes de Download
        if format_choice == 'mp4':
                # Baixa o video (stream com audio e video)
                safe_name = get_safe_filename(title, 'mp4', prefix="[VIDEO] ")
                
                ydl_opts = {
                    'format': 'best[ext=mp4][acodec!=none][vcodec!=none]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(DOWNLOAD_FOLDER, safe_name),
                    'noplaylist': True,
                    'progress_hooks': [progress_hook],
                    
                    # --- MUDANCA AQUI ---
                    # Adiciona um pos-processador para chamar o FFmpeg
                    # e mover o "moov atom" (indice) para o inicio.
                    'postprocessors': [{
                        'key': 'FFmpegMoveMoovAtom',
                    }]
                }
        else: # mp3
            safe_name = get_safe_filename(title, 'm4a', prefix="[AUDIO] ")
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, safe_name),
                'progress_hooks': [progress_hook], # <-- AQUI ESTA A MAGICA
                'noplaylist': True,
            }

        # 4. Inicia o Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 5. Emite a conclusao
        emit('download_finished', {'message': f"'{safe_name}' baixado com sucesso!"})

    except Exception as e:
        logging.error(f"Erro no download (socket): {e}")
        emit('download_error', {'error': str(e)})


@app.route('/get_downloads')
def get_downloads():
    """ 
    Endpoint modificado para ler os arquivos .meta
    e retornar uma lista de objetos
    """
    try:
        files = os.listdir(DOWNLOAD_FOLDER)
        # Filtra apenas os arquivos .meta
        meta_files = [f for f in files if f.endswith('.meta')]
        
        downloaded_items = []
        for meta_file in meta_files:
            try:
                with open(os.path.join(DOWNLOAD_FOLDER, meta_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Garante que o arquivo de video/audio ainda exista
                    if os.path.exists(os.path.join(DOWNLOAD_FOLDER, data['downloaded_file'])):
                        downloaded_items.append({
                            'title': data.get('title'),
                            'thumbnail': data.get('thumbnail'),
                            'filename': data.get('downloaded_file')
                        })
            except Exception:
                continue # Ignora arquivos meta corrompidos
                
        return jsonify({'files': downloaded_items})
        
    except Exception as e:
        logging.error(f"Erro ao listar arquivos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<filename>')
def serve_download(filename):
    """ 
    Permite que o usuario acesse o arquivo baixado.
    Alterado para VISUALIZAR (streaming) em vez de baixar.
    """
    return send_from_directory(
        DOWNLOAD_FOLDER, 
        filename, 
        as_attachment=False, # <-- MUDANCA AQUI (de True para False)
        conditional=True
    )


if __name__ == '__main__':
    # Modificado para usar socketio.run()
    logging.info("Iniciando servidor com SocketIO...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)