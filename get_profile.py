import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import time
import random

import instaloader
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Controle de upload para Minio
UPLOAD_TO_MINIO = True

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

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
        with open('auth/credentials.json') as f:
            credentials = json.load(f)
        
        endpoint = "s3.supercaso.com.br"
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

def get_instagram_session():
    """Carrega e retorna uma sessão do Instagram"""
    try:
        username = os.getenv("INSTAGRAM_USERNAME")
        if not username:
            raise ValueError("INSTAGRAM_USERNAME não configurado no .env")
            
        L = instaloader.Instaloader()
        L.load_session_from_file(username)
        log_info("Sessão do Instagram carregada com sucesso")
        return L
    except Exception as e:
        log_error(f"Erro ao carregar sessão: {str(e)}")
        return None

def get_profile_with_retry(context, username, max_retries=3):
    """Obtém perfil do Instagram com sistema de retry"""
    for attempt in range(max_retries):
        try:
            return instaloader.Profile.from_username(context, username)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = (2 ** attempt) + random.uniform(1, 3)
            log_info(f"Tentativa {attempt + 1} falhou. Aguardando {delay:.1f}s...")
            time.sleep(delay)

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
            
            try:
                client.remove_object(bucket_name, object_name)
                log_info(f"Objeto existente removido: {object_name}")
            except:
                pass
            
            log_info(f"Iniciando upload de {file_name}")
            client.fput_object(bucket_name, object_name, str(file_path), content_type=content_type)
            log_info(f"Upload concluído: {object_name}")
        
        return True
        
    except Exception as e:
        log_error(f"Erro no upload para Minio: {str(e)}")
        return False

def save_instagram_data(username):
    """Coleta e salva dados do Instagram"""
    try:
        user_dir = setup_directory(username)
        
        # Carrega sessão do Instagram
        loader = get_instagram_session()
        if not loader:
            raise Exception("Não foi possível carregar a sessão do Instagram")
        
        # Configura o Instaloader para usar o diretório correto
        loader.dirname_pattern = str(user_dir)
        loader.download_pictures = True
        loader.download_videos = False
        loader.download_video_thumbnails = False
        loader.download_geotags = False
        loader.download_comments = False
        loader.save_metadata = False
        
        # Obtém o perfil com retry
        profile = get_profile_with_retry(loader.context, username)
        log_info("Dados do perfil obtidos com sucesso")
        
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
            "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Salva JSON
        json_path = user_dir / "profile_info.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_info, f, indent=4, ensure_ascii=False)
        log_info(f"Arquivo JSON criado: {json_path}")
        
        # Download da foto
        log_info("Baixando foto de perfil...")
        loader.download_profilepic(profile)
        
        # Renomeia a foto
        for file in os.listdir(user_dir):
            if file.endswith('_profile_pic.jpg'):
                old_path = user_dir / file
                new_path = user_dir / "profile_pic.jpg"
                os.rename(old_path, new_path)
                log_info("Foto de perfil renomeada para profile_pic.jpg")
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