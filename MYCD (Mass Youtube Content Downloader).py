'''' 
== MYCD - MASS YOUTUBE CONTENT DOWNLOADER ==
Script de automatização para download de músicas/vídeos do YouTube usando yt-dlp.
Criado por: Carlos Oliveira (GitHub: @CarlossOliveira)
'''
import os, re, subprocess, platform, time, fnmatch, random, json, winsound


boat_uncovered = False # Alterar só em caso de necessidade de aumentar a privacidade (OPTIONS: True or False)


# Função para atualizar yt-dlp
def update_yt_dlp(yt_dlp_path):
    try:
        print("Atualizador de Pacotes: Atualizando yt-dlp...")
        result = subprocess.run([yt_dlp_path, "-U"], capture_output=True, text=True, check=True)
        if "Updated yt-dlp to" in result.stdout:
            print("yt-dlp atualizado com sucesso.\n")
        else:
            print("yt-dlp já está na versão mais recente.\n")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao atualizar yt-dlp: {e.stderr.strip()}\n")


# Função para ler o arquivo de configuração
def read_config(config_file):
    config = {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"Erro ao ler o arquivo de configuração: {e}")
        exit(1)

    # Verificar se os parâmetros essenciais estão presentes
    required_keys = ['operation_mode', 'output_format', 'number_of_searched_queries']
    for key in required_keys:
        if key not in config or not config[key] and key != 'number_of_searched_queries':
            print(f"Erro: O parâmetro '{key}' não foi encontrado ou está vazio no arquivo de configuração.")
            exit(1)
        if key not in config or not config[key] and key == 'number_of_searched_queries' and config['operation_mode'].lower() == 'search':
            print(f"Erro: O parâmetro '{key}' não foi encontrado ou está vazio no arquivo de configuração.")
            exit(1)

    # Validar valores específicos
    if config['operation_mode'].lower() not in ['search', 'link']:
        print("Erro: O valor de 'operation_mode' deve ser 'search' ou 'link'.")
        exit(1)

    return config


# Funções para emitir sons de aviso
def emitir_som(modo):
    if modo.lower() == "aviso":
        if platform.system() == "Windows":
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        elif platform.system() == "Darwin":  # macOS
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        elif platform.system() == "Linux":
            os.system('aplay /usr/share/sounds/alsa/Front_Center.wav')
        else:
            print("Erro: Sistema Operativo não suportado.")
    elif modo.lower() == "fim":
        if platform.system() == "Windows":
            winsound.PlaySound("SystemNotification", winsound.SND_ALIAS)
        elif platform.system() == "Darwin":  # macOS
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        elif platform.system() == "Linux":
            os.system('aplay /usr/share/sounds/freedesktop/stereo/message.oga')  
        else:
            print("Erro: Sistema Operativo não suportado.")


# Função para validar se um caminho existe
def validate_path(path, description):
    if not path or not os.path.isfile(path):
        print(f"Erro: {description} '{path}' não encontrado.")
        exit(1)


# Função para validar formato de entrada de música ou link
def validate_music_entry(line, operation_mode):
    if not line:
        return False
    if operation_mode == "search":
        return " - " in line
    elif operation_mode == "link":
        return line.startswith("http://") or line.startswith("https://")
    return False


# Caminho para o arquivo de configuração
script_dir = os.path.dirname(os.path.abspath(__file__))  # Diretório do script
config_file = os.path.join(script_dir, "MYCD - CONFIGURATION.txt")


# Ler configurações
config = read_config(config_file)
yt_dlp_path = config.get("yt_dlp_path")
ffmpeg_path = config.get("ffmpeg_path")
operation_mode = config.get("operation_mode").lower().strip()
file_format = config.get("output_format").lower().strip()
if operation_mode == "search":
    numero_de_entradas_da_pesquisa = int(config.get("number_of_searched_queries"))
reject_title = config.get("words_to_reject_during_search", "")
search_title = config.get("search_matching", "")
output_folder_path = config.get("output_folder_path", "")

if not yt_dlp_path:
    yt_dlp_path = os.path.join(script_dir, "Program Files", "yt-dlp", "yt-dlp.exe")
if not ffmpeg_path:
    ffmpeg_path = os.path.join(script_dir, "Program Files", "ffmpeg", "bin", "ffmpeg.exe")
    
if output_folder_path:
    output_folder = str(output_folder_path)+r"\MYCD - Mass Youtube Content Downloader (Output Folder)"


# Validar se o yt-dlp e ffmpeg estão corretamente configurados
validate_path(yt_dlp_path, "yt-dlp")
validate_path(ffmpeg_path, "ffmpeg")


# Função para verificar números faltando em arquivos de um diretório
def verificar_numeros_em_falta(diretorio, file_format, error_log):
    # Listar todos os arquivos no diretório
    if file_format == "best_video_quality":
        arquivos = [f for f in os.listdir(diretorio)]
    else:
        arquivos = [f for f in os.listdir(diretorio) if f.endswith(file_format)]
    
    # Extrair os números dos arquivos com a estrutura [000]
    numeros = []
    for arquivo in arquivos:
        match = re.match(r'^\[(\d+)\]', arquivo)
        if match:
            # Se o arquivo seguir o formato correto, adiciona o número à lista
            numeros.append(int(match.group(1)))
    
    if not numeros:
        with open(error_log, "a", encoding="utf-8") as f:
            f.write("\n\nERRO INESPERADO: Nenhum arquivo com o formato [PLAYLIST_INDEX_NUMBER] encontrado.\n\n")
        return "\nERRO INESPERADO: Nenhum arquivo com o formato [PLAYLIST_INDEX_NUMBER] encontrado."
    
    # Verificar se os números estão em sequência
    numeros.sort()
    
    # Encontrar números faltando
    numeros_em_falta = []
    for i in range(numeros[0], numeros[-1] + 1):
        if i not in numeros:
            numeros_em_falta.append(i)
    
    if numeros_em_falta:
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n\nResultados da Verificação Final - Index dos títulos em falta (Número total de títulos faltantes: {len(numeros_em_falta)}): {numeros_em_falta}\n\n")
        return f"\nVerificação concluída!\nIndex dos títulos em falta (Número total de títulos faltantes: {len(numeros_em_falta)}): {numeros_em_falta}"
    else:
        return "\nVerificação concluída!\nTodos os títulos estão presentes."

# Função para renomear arquivos após confirmação de download de playlist
def renomear_arquivos(diretorio, file_format):
    # Listar todos os arquivos no diretório
    for nome_arquivo in os.listdir(diretorio):
        # Verificar se o arquivo tem a extensão especificada
        if nome_arquivo.endswith(str(file_format)) and file_format != "best_video_quality":
            # Verificar se o nome do arquivo segue o formato '[000]'
            match = re.match(r'^\[\d+\]\s*(.*)', nome_arquivo)
            if match:
                # Remover os números e os colchetes do início
                novo_nome = match.group(1)
                
                # Construir os caminhos completos
                caminho_antigo = os.path.join(diretorio, nome_arquivo)
                caminho_novo = os.path.join(diretorio, novo_nome)
                
                # Verificar se o arquivo de destino já existe
                if os.path.exists(caminho_novo):
                    base, ext = os.path.splitext(novo_nome)
                    i = 1
                    while os.path.exists(os.path.join(diretorio, f"{base}_{i}{ext}")):
                        i += 1
                    caminho_novo = os.path.join(diretorio, f"{base}_{i}{ext}")
                
                # Renomear o arquivo
                os.rename(caminho_antigo, caminho_novo)
                print(f'Ficheiro Renomeado: {nome_arquivo} -> {novo_nome}')

        elif file_format == "best_video_quality":
            match = re.match(r'^\[\d+\]\s*(.*)', nome_arquivo)
            if match:
                novo_nome = match.group(1)
                
                caminho_antigo = os.path.join(diretorio, nome_arquivo)
                caminho_novo = os.path.join(diretorio, novo_nome)
                
                if os.path.exists(caminho_novo):
                    base, ext = os.path.splitext(novo_nome)
                    i = 1
                    while os.path.exists(os.path.join(diretorio, f"{base}_{i}{ext}")):
                        i += 1
                    caminho_novo = os.path.join(diretorio, f"{base}_{i}{ext}")
                
                os.rename(caminho_antigo, caminho_novo)
                print(f'Ficheiro Renomeado: {nome_arquivo} -> {novo_nome}')


# Atualizar yt-dlp
try:
    update_yt_dlp(yt_dlp_path)
except Exception as e:
    print("Continuando com a versão atual do yt-dlp...\n")


# Determinar se o formato de saída é áudio ou vídeo
audio_formats = ['mp3', 'm4a', 'opus', 'aac', 'flac', 'wav']
video_formats = ['mp4', 'best_video_quality']
if file_format in audio_formats:
    output_type = "audio"
elif file_format == video_formats[1]:
    output_type = file_format
elif file_format == video_formats[0]:
    output_type = "video"
else:
    print("Erro: Formato de saída inválido. Verifique o arquivo de configuração.")
    exit(1)


# Função para normalizar nomes de arquivos para DEBUG
def normalizar_texto(texto):
    """
    Substitui caracteres problemáticos para padronizar títulos e nomes de arquivos.
    """
    substituicoes = {
        "/": "⧸",
        "\\": "⧸",
        ":": "-",
        "*": "",
        "?": "",
        "\"": "",
        "<": "",
        ">": "",
        "|": "",
        "(": "",
        ")": "",
        "[": "",
        "]": "",
    }
    for caractere, substituto in substituicoes.items():
        texto = texto.replace(caractere, substituto)
    return texto


# Configuration and User Input
browser_to_get_COOKIE = None  # Browser para extrair cookies (OPTIONS: None, "chrome", "edge", "firefox", (...))
path_to_big_COOKIE = None # Caminho para um arquivo de cookies do youtube (OPTIONS: None, r"[PATH_TO_COOKIE_FILE.txt]")
hardware_randomization = boat_uncovered

print("== MYCD - MASS YOUTUBE CONTENT DOWNLOADER ==")
print("Este script faz uso do yt-dlp para baixar músicas/vídeos.\nPara mais informações, contacte o desenvolvedor.\n")
input_file = str(input("Indique o caminho do ficheiro de entrada: ")).strip('"').strip("''").strip() # Caminho do ficheiro de entrada
metadados = str(input(f"Deseja incorporar metadados no(s) título(s) baixado(s) de {input_file}? ")).strip().strip('"').strip("''").replace(" ","").lower() # Incorporar metadados no arquivo de saída? (True/False)

if metadados in ["s", "t", "y", "true", "sim", "yes", "yup", "1", "verdadeiro", "afirmativo", "claro", "podeser"]:
    metadados = True
elif metadados in ["n", "f", "false", "não", "no", "nop", "nao", "falso", "0", "negativo"]:
    metadados = False
else:
    print(f'ERRO: "{metadados}", não é reconhecido como opção de escolha.')
    exit(1)

if not output_folder_path:
    output_folder = "MYCD - Output Folder"  # Pasta para salvar músicas/vídeos
debug_folder = os.path.join(output_folder, "DEBUG")  # Pasta para logs

print(f"Caminho para a pasta de saída: {os.path.abspath(output_folder)}")
print(f"=> Configurações atuais:")
print(f"| Modo de operação: {operation_mode.upper()}")
print(f"| Formato de saída: {file_format}") if output_type != "best_video_quality" else print("| Formato de saída: [Best Video Quality Available]")
print(f"| Download completo com metadados? {str(metadados).upper()}")
if operation_mode == "search":
    if search_title:
        print(f"| Filtros de pesquisa (Palavras Aceites): {search_title}")
    if reject_title:
        print(f"| Filtros de pesquisa (Palavras Rejeitadas): {reject_title}")
    print(f"| Número de entradas da pesquisa: {numero_de_entradas_da_pesquisa}\n")


# Ler músicas do ficheiro de entrada
try:
    with open(input_file, "r", encoding="utf-8") as f:
        all_songs = [line.strip() for line in f if line.strip()]
except Exception as e:
    print(f"Erro ao ler o arquivo de entrada: {e}")
    exit(1)


# Validar se as músicas têm formato adequado
invalid_songs = [line for line in all_songs if not validate_music_entry(line, operation_mode)]
if invalid_songs:
    print("Erro: As seguintes entradas estão no formato inválido:")
    for song in invalid_songs:
        print(f"  {song}")
    exit(1)


# Criar pastas de saída se não existirem
os.makedirs(output_folder, exist_ok=True)
os.makedirs(debug_folder, exist_ok=True)


# Caminhos dos arquivos de log
success_log = os.path.join(debug_folder, "MYCD - Downloads do Ficheiro de Entrada Realizados com Sucesso.txt")  # Log de sucessos
error_log = os.path.join(debug_folder, "MYCD - Downloads do Ficheiro de Entrada com Erro.txt ")  # Log de erros


print(f"Processando ficheiro de entrada: {input_file}")
print(f"Total de títulos a processar: {len(all_songs)}\n")


# Função para extração de duração e título
def extract_duration_and_title(entry):
    """Extrai o título e a duração (se presente) de uma entrada formatada."""
    if "§" in entry:
        try:
            title_part, duration_part = entry.rsplit("§", 1)
            duration = duration_part.strip("§")
            return title_part.strip(), duration
        except ValueError:
            return entry, None
    return entry, None


# Função para alterar o formato da duração
def format_duration(duration):
    """Converte a duração em formato legível pelo yt-dlp."""
    try:
        parts = duration.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return None
    return None


# Função para fazer download de títulos através dos seus links
def download_song_link(link, roulette):
    """Faz o download de uma música ou vídeo usando yt-dlp."""
    try:
        yt_dlp_args = [
            yt_dlp_path,
            "--print-json",
            "--embed-metadata" if metadados else None,
            "--embed-thumbnail" if metadados else None,
            "-f" if output_type == "video" or output_type == "best_video_quality" else None, f"bestvideo[ext={file_format}]+bestaudio[ext=m4a]/best[ext={file_format}]" if output_type == "video" else None, f"bestvideo+bestaudio/best" if output_type == "best_video_quality" else None,
            "--extract-audio" if output_type == "audio" else None,
            "--audio-quality" if output_type == "audio" else None, "0" if output_type == "audio" else None,
            "--audio-format" if output_type == "audio" else None, file_format if output_type == "audio" else None,
            "--ffmpeg-location", ffmpeg_path,
            
            "--cookies" if not browser_to_get_COOKIE and path_to_big_COOKIE else None, path_to_big_COOKIE if not browser_to_get_COOKIE and path_to_big_COOKIE else None,
            "--cookies-from-browser" if browser_to_get_COOKIE and not path_to_big_COOKIE else None, browser_to_get_COOKIE if browser_to_get_COOKIE and not path_to_big_COOKIE else None,
            
            "--rate-limit" if hardware_randomization else None, "500K" if hardware_randomization else None,
            "--user-agent" if hardware_randomization and (roulette == 0) else None, "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0" if hardware_randomization and (roulette == 0) else None,
            "--user-agent" if hardware_randomization and (roulette == 1) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.1 Safari/537.36" if hardware_randomization and (roulette == 1) else None,
            "--user-agent" if hardware_randomization and (roulette == 2) else None, "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36" if hardware_randomization and (roulette == 2) else None,
            "--user-agent" if hardware_randomization and (roulette == 3) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" if hardware_randomization and (roulette == 3) else None,
            "--user-agent" if hardware_randomization and (roulette == 4) else None, "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1" if hardware_randomization and (roulette == 4) else None,
            
            "-o", os.path.join(output_folder, "%(title)s.%(ext)s"),
            link,
        ]
        
        # Remover argumentos que são None
        yt_dlp_args = [arg for arg in yt_dlp_args if arg is not None]

        result = subprocess.run(
            yt_dlp_args,
            capture_output=True,
            text=True,
            check=True,
        )
        
        # Extrair informações do vídeo
        video_info = json.loads(result.stdout)
        video_title = video_info.get('title', 'Título desconhecido')

        # Normalizar o título original
        video_title_normalizado = normalizar_texto(video_title)

        arquivos_na_pasta = os.listdir(output_folder)

        # Verificar se o arquivo foi baixado com sucesso
        downloaded_files = [
            f for f in arquivos_na_pasta
            if video_title_normalizado in normalizar_texto(f)
        ]

        if downloaded_files:
            print(f"Download concluído para: {video_title}")
            with open(success_log, "a", encoding="utf-8") as f:
                f.write(f"Download concluído para: {video_title}\n")
            return True
        else:
            print(f"Erro durante o download para: {link} (Arquivo não encontrado)")
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"Erro durante o download para: {link} (Arquivo não encontrado)\n")
            return False
    except Exception as e:
        print(f"Erro ao processar o download: ({e})")
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"Erro ao processar o download para: {link} ({e})\n")
        return False


# Função para fazer download de playlists através dos links
def download_playlist(playlist_url, roulette):
    try:
        yt_dlp_args = [
            yt_dlp_path,
            "--quiet",
            "--yes-playlist",
            "--embed-metadata" if metadados else None,
            "--embed-thumbnail" if metadados else None,
            "-f" if output_type == "video" or output_type == "best_video_quality" else None, f"bestvideo[ext={file_format}]+bestaudio[ext=m4a]/best[ext={file_format}]" if output_type == "video" else None, f"bestvideo+bestaudio/best" if output_type == "best_video_quality" else None,
            "--extract-audio" if output_type == "audio" else None,
            "--audio-format" if output_type == "audio" else None, file_format if output_type == "audio" else None,
            "--audio-quality" if output_type == "audio" else None, "0" if output_type == "audio" else None,
            "--ffmpeg-location", ffmpeg_path,
            
            "--cookies" if not browser_to_get_COOKIE and path_to_big_COOKIE else None, path_to_big_COOKIE if not browser_to_get_COOKIE and path_to_big_COOKIE else None,
            "--cookies-from-browser" if browser_to_get_COOKIE and not path_to_big_COOKIE else None, browser_to_get_COOKIE if browser_to_get_COOKIE and not path_to_big_COOKIE else None,
            
            "--rate-limit" if hardware_randomization else None, "500K" if hardware_randomization else None,
            "--user-agent" if hardware_randomization and (roulette == 0) else None, "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0" if hardware_randomization and (roulette == 0) else None,
            "--user-agent" if hardware_randomization and (roulette == 1) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.1 Safari/537.36" if hardware_randomization and (roulette == 1) else None,
            "--user-agent" if hardware_randomization and (roulette == 2) else None, "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36" if hardware_randomization and (roulette == 2) else None,
            "--user-agent" if hardware_randomization and (roulette == 3) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" if hardware_randomization and (roulette == 3) else None,
            "--user-agent" if hardware_randomization and (roulette == 4) else None, "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1" if hardware_randomization and (roulette == 4) else None,
            
            "-o", os.path.join(output_folder, "[%(playlist_index)03d] %(title)s.%(ext)s"),
            playlist_url,
        ]

        yt_dlp_args = [arg for arg in yt_dlp_args if arg is not None]

        # Executar o comando yt-dlp
        result = subprocess.run(yt_dlp_args, check=True, capture_output=True, text=True)

        # Se o comando foi bem-sucedido, registrar no log de sucesso
        if result.returncode == 0:
            print(f"Download completo concluído para a playlist: {playlist_url}")
            with open(success_log, "a", encoding="utf-8") as f:
                f.write(f"Download completo concluído para a playlist: {playlist_url}\n")
            return True
    except subprocess.CalledProcessError as e:
        # Registrar o erro no log de falhas
        print(f"Erro durante o download para {playlist_url}:\n- {e.stderr}")
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"Erro durante o download para {playlist_url}:\n- {e.stderr}\n")
    except Exception as ex:
        # Capturar quaisquer outros erros inesperados
        print(f"Erro inesperado durante o download para {playlist_url}:\n- {ex}")
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"Erro inesperado durante o download para {playlist_url}:\n- {ex}\n")


# Função para fazer download de títulos através da pesquisa
def download_song_search(title_and_author, roulette, duration=None, retries=3):
    """Faz o download de uma música ou vídeo buscando no YouTube com retry."""
    title_and_author_formatado = title_and_author.replace("/", "&").replace("*", " ").replace("\\", " ").replace("|", "&").replace("?", " ").replace(":", "-").replace("\"", "").replace("<", "").replace(">", "")
    try:
        yt_dlp_args = [
            yt_dlp_path,
            "--print-json",
            "--embed-metadata" if metadados else None,
            "--embed-thumbnail" if metadados else None,
            "-f" if output_type == "video" or output_type == "best_video_quality" else None, f"bestvideo[ext={file_format}]+bestaudio[ext=m4a]/best[ext={file_format}]" if output_type == "video" else None, f"bestvideo+bestaudio/best" if output_type == "best_video_quality" else None,
            "--match-title" if search_title else None, f"(?i){search_title}" if search_title else None,
            "--reject-title" if reject_title else None, f"(?i){reject_title}" if reject_title else None,
            "--extract-audio" if output_type == "audio" else None,
            "--audio-format" if output_type == "audio" else None, file_format if output_type == "audio" else None,
            "--audio-quality" if output_type == "audio" else None, "0" if output_type == "audio" else None,
            "--ffmpeg-location", ffmpeg_path,
            
            "--cookies" if not browser_to_get_COOKIE and path_to_big_COOKIE else None, path_to_big_COOKIE if not browser_to_get_COOKIE and path_to_big_COOKIE else None,
            "--cookies-from-browser" if browser_to_get_COOKIE and not path_to_big_COOKIE else None, browser_to_get_COOKIE if browser_to_get_COOKIE and not path_to_big_COOKIE else None,
            
            "--rate-limit" if hardware_randomization else None, "500K" if hardware_randomization else None,
            "--user-agent" if hardware_randomization and (roulette == 0) else None, "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0" if hardware_randomization and (roulette == 0) else None,
            "--user-agent" if hardware_randomization and (roulette == 1) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.1 Safari/537.36" if hardware_randomization and (roulette == 1) else None,
            "--user-agent" if hardware_randomization and (roulette == 2) else None, "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36" if hardware_randomization and (roulette == 2) else None,
            "--user-agent" if hardware_randomization and (roulette == 3) else None, "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" if hardware_randomization and (roulette == 3) else None,
            "--user-agent" if hardware_randomization and (roulette == 4) else None, "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1" if hardware_randomization and (roulette == 4) else None,
            
            "-o", os.path.join(output_folder, (f"{title_and_author_formatado}"+".%(ext)s")),
            f"ytsearch{numero_de_entradas_da_pesquisa}:{title_and_author}",
        ]

        if duration:
            yt_dlp_args.extend(["--max-downloads", "1", "--match-filter", f"duration <= {duration}"])

        yt_dlp_args = [arg for arg in yt_dlp_args if arg is not None]

        for attempt in range(retries):
            result = subprocess.run(
                yt_dlp_args,
                capture_output=True,
                text=True,
                check=True,
            )

        # Verificar se o arquivo foi baixado com sucesso
        downloaded_files = [f for f in os.listdir(output_folder) if fnmatch.fnmatch(f, f"{title_and_author_formatado}.*")]
        if downloaded_files:
            print(f"Download concluído para: {title_and_author}")
            with open(success_log, "a", encoding="utf-8") as f:
                f.write(f"Download concluído para: {title_and_author}\n")
            return True
        else:
            print(f"Erro durante o download para: {title_and_author} (Arquivo não encontrado)")
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"Erro durante o download para: {title_and_author} (Arquivo não encontrado)\n")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Erro durante o download para: {title_and_author} (Erro do yt-dlp: {e.stderr.strip()})")
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"Erro durante o download para: {title_and_author} (Erro do yt-dlp: {e.stderr.strip()})\n")
        return False

    except Exception as e:
        print(f"Erro inesperado durante o download para: {title_and_author} ({str(e)})")
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"Erro inesperado durante o download para: {title_and_author} ({str(e)})\n")
        return False


# Medir o tempo total de execução
start_time = time.time()


# Fazer download das músicas
successful_downloads = 0
failed_downloads = 0

contador = 0
if operation_mode == "search":
    for i, line in enumerate(all_songs, 1):
        
        # Gerador de números aleatórios
        if contador % 5 == 0:
            roulette = random.randint(0,4)
        else:
            roulette = None
        contador += 1
        
        title, duration = extract_duration_and_title(line)
        formatted_duration = format_duration(duration) if duration else None

        print(f"({i}/{len(all_songs)}) Downloading: {title}")
        if download_song_search(title, roulette, duration=formatted_duration):
            successful_downloads += 1
        else:
            failed_downloads += 1
elif operation_mode == "link":
    for i, line in enumerate(all_songs, 1):
        
        if contador % 5 == 0:
            roulette = random.randint(0,4)
        else:
            roulette = None
        contador += 1
        
        # Verificar se a linha contém uma playlist
        if "playlist?" in line or "link=" in line:
            operation_mode_playlist = True
        else:
            operation_mode_playlist = False

        if not operation_mode_playlist:
            print(f"({i}/{len(all_songs)}) Downloading: {line}")
            if download_song_link(line, roulette):
                successful_downloads += 1
            else:
                failed_downloads += 1
        elif operation_mode_playlist:
            print(f"({i}/{len(all_songs)}) Playlist detetada! Downloading playlist: {line}")
            if download_playlist(line, roulette):
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Verificação de títulos faltantes em playlists
            in_ver = str(input("Deseja executar a verificação de títulos faltantes? ")).strip().replace(" ","").lower()
            emitir_som("aviso")
            if in_ver in ["y", "s", "t", "true", "sim", "yes", "yup", "1", "verdadeiro", "afirmativo", "claro", "podeser"]:
                print("Verificando e restaurando títulos...")
                mensagem_verificacao = verificar_numeros_em_falta(output_folder, file_format, error_log)
                renomear_arquivos(output_folder, file_format)
                print(mensagem_verificacao)
            else:
                print("Verificando e restaurando títulos...")
                renomear_arquivos(output_folder, file_format)
else:
    print("Modo de operação inválido. Verifique o arquivo de configuração.")
    exit(1)


# Resumo
end_time = time.time()
elapsed_time = end_time - start_time
elapsed_minutes, elapsed_seconds = divmod(elapsed_time, 60)
print("\nResumo das Operações:")
print(f"Tempo total de execução: {elapsed_minutes} minutos e {elapsed_seconds} segundos")
print(f"Total de downloads bem-sucedidos: {successful_downloads}")
print(f"Total de downloads falhados: {failed_downloads}")
emitir_som("fim")