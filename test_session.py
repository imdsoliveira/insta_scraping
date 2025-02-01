import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import time
import random

import instaloader
from minio import Minio
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
UPLOAD_TO_MINIO = True
MAX_RETRIES = 3
BASE_DELAY = 5
USE_DELAY = True

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def random_delay():
    """Implementa um delay aleatório para evitar detecção"""
    if USE_DELAY:
        delay = random.uniform(2, 5)
        time.sleep(delay)

class CustomInstaloader(instaloader.Instaloader):
    def get_anonymous_session(self):
        """Sobrescreve o método para adicionar delays"""
        random_delay()
        return super().get_anonymous_session()

def setup_directory(username):
    """Cria e retorna o diretório para o usuário"""
    base_dir = Path("dados")
    base_dir.mkdir(exist_ok=True)
    log_info("Diretório base 'dados' verificado")
    
    user_dir = base_dir / username
    if user_dir.exists():
        shutil.rmtree(user_dir)
    user_dir.mkdir()
    log_info(f"Diretório limpo criado em: {user_dir}")
    
    return user_dir

def get_minio_client():
    """Configura e retorna o cliente Minio"""
    try:
        endpoint = "s3.supercaso.com.br"
        with open('auth/credentials.json') as f:
            credentials = json.load(f)
        
        log_info(f"Configurando Minio com endpoint: {endpoint}")
        
        client = Minio(
            endpoint,
            access_key=credentials["accessKey"],
            secret_key=credentials["secretKey"],
            secure=True
        )
        log_info("Cliente Minio configurado com sucesso")
        return client
    except Exception as e:
        log_error(f"Erro ao configurar cliente Minio: {str(e)}")
        raise

def retry_operation(operation, max_retries=MAX_RETRIES):
    """Tenta uma operação com retry e delay exponencial"""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = BASE_DELAY * (2 ** attempt) + random.uniform(1, 3)
            log_info(f"Tentativa {attempt + 1} falhou. Aguardando {delay:.1f}s...")
            time.sleep(delay)

def get_instagram_data(username):
    """Obtém dados do Instagram com retry"""
    def _get_data():
        # Configura o Instaloader com delays
        loader = CustomInstaloader(
            download_pictures=True,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            request_timeout=30
        )
        
        # Carrega sessão se disponível
        try:
            session_file = f"{os.getenv('INSTAGRAM_USERNAME')}_session"
            if os.path.exists(session_file):
                loader.load_session_from_file(os.getenv('INSTAGRAM_USERNAME'))
                log_info("Sessão carregada")
        except:
            log_info("Continuando sem sessão")

        random_delay()
        profile = instaloader.Profile.from_username(loader.context, username)
        return loader, profile

    return retry_operation(_get_data)

def upload_to_minio(user_dir: Path):
    """Realiza upload dos arquivos para o Minio"""
    try:
        client = get_minio_client()
        bucket_name = os.getenv("BUCKET_NAME")
        
        if not bucket_name:
            raise ValueError("BUCKET_NAME não encontrado no .env")
        
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            log_info(f"Bucket '{bucket_name}' criado")
        
        for file_path in user_dir.glob('*'):
            file_name = file_path.name
            object_name = f"{user_dir.name}/{file_name}"
            content_type = 'image/jpeg' if file_name.endswith('.jpg') else 'application/json'
            
            def _upload():
                try:
                    client.remove_object(bucket_name, object_name)
                except:
                    pass
                
                log_info(f"Iniciando upload de {file_name}")
                client.fput_object(
                    bucket_name,
                    object_name,
                    str(file_path),
                    content_type=content_type
                )
                log_info(f"Upload concluído: {object_name}")
            
            retry_operation(_upload)
        
        return True
        
    except Exception as e:
        log_error(f"Erro no upload para Minio: {str(e)}")
        return False

def save_instagram_data(username):
    """Coleta e salva dados do Instagram"""
    try:
        user_dir = setup_directory(username)
        
        # Obtém dados do Instagram
        loader, profile = get_instagram_data(username)
        log_info("Dados do perfil obtidos com sucesso")
        
        # Define o diretório de download
        loader.dirname_pattern = str(user_dir)
        
        # Prepara informações
        profile_info = {
            "username": username,
            "full_name": profile.full_name,
            "biography": profile.biography,
            "mediacount": profile.mediacount,
            "followers": profile.followers,
            "following": profile.followees,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified,
            "profile_pic_url": profile.profile_pic_url,
            "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Salva JSON
        json_path = user_dir / "profile_info.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_info, f, indent=4, ensure_ascii=False)
        log_info(f"Arquivo JSON criado: {json_path}")
        
        # Download da foto com retry
        def _download_pic():
            loader.download_profilepic(profile)
        retry_operation(_download_pic)
        
        # Renomeia a foto
        for file in os.listdir(user_dir):
            if file.endswith('_profile_pic.jpg'):
                old_path = user_dir / file
                new_path = user_dir / "profile_pic.jpg"
                os.rename(old_path, new_path)
                log_info("Foto de perfil renomeada")
                break
        
        # Exibe informações
        print("\nInformações do perfil:")
        for key, value in profile_info.items():
            print(f"{key}: {value}")
        
        # Upload para Minio
        if UPLOAD_TO_MINIO:
            log_info("Iniciando upload para Minio...")
            if upload_to_minio(user_dir):
                log_info("Upload para Minio concluído com sucesso")
            else:
                log_error("Falha no upload para Minio")
        
        log_info(f"Processo concluído. Dados salvos em dados/{username}/")
        
    except Exception as e:
        log_error(f"Erro ao processar perfil de @{username}: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Obtém informações de um perfil do Instagram')
    parser.add_argument('--username', type=str, required=True, 
                      help='Nome de usuário do Instagram (com ou sem @)')
    
    args = parser.parse_args()
    username = args.username.lstrip('@')
    save_instagram_data(username)

if __name__ == "__main__":
    main()