import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

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
        
        # Usar o endpoint S3 definido na stack
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

def upload_to_minio(user_dir: Path):
    """Realiza upload dos arquivos para o Minio"""
    try:
        client = get_minio_client()
        bucket_name = os.getenv("BUCKET_NAME")
        
        if not bucket_name:
            raise ValueError("BUCKET_NAME não encontrado no .env")
        
        # Verifica/cria o bucket
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            log_info(f"Bucket '{bucket_name}' criado")
        
        # Upload dos arquivos
        for file_path in user_dir.glob('*'):
            file_name = file_path.name
            object_name = f"{user_dir.name}/{file_name}"
            
            # Define o content type apropriado
            content_type = 'image/jpeg' if file_name.endswith('.jpg') else 'application/json'
            
            # Remove objeto existente se houver
            try:
                client.remove_object(bucket_name, object_name)
                log_info(f"Objeto existente removido: {object_name}")
            except:
                pass
            
            # Faz upload
            log_info(f"Iniciando upload de {file_name}")
            client.fput_object(
                bucket_name,
                object_name,
                str(file_path),
                content_type=content_type
            )
            log_info(f"Upload concluído: {object_name}")
        
        log_info("Todos os arquivos foram enviados para o Minio")
        return True
        
    except Exception as e:
        log_error(f"Erro no upload para Minio: {str(e)}")
        return False

def save_instagram_data(username):
    """Coleta e salva dados do Instagram"""
    try:
        # Preparar diretório
        user_dir = setup_directory(username)
        
        # Configurar Instaloader com o diretório correto
        loader = instaloader.Instaloader(dirname_pattern=str(user_dir))
        
        # Obter dados do perfil
        profile = instaloader.Profile.from_username(loader.context, username)
        log_info("Dados do perfil obtidos com sucesso")
        
        # Preparar informações para JSON
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
        
        # Salvar JSON
        json_path = user_dir / "profile_info.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_info, f, indent=4, ensure_ascii=False)
        log_info(f"Arquivo JSON criado: {json_path}")
        
        # Download da foto de perfil
        log_info("Baixando foto de perfil...")
        loader.download_profilepic(profile)
        
        # Renomear a foto de perfil
        for file in os.listdir(user_dir):
            if file.endswith('_profile_pic.jpg'):
                old_path = user_dir / file
                new_path = user_dir / "profile_pic.jpg"
                os.rename(old_path, new_path)
                log_info("Foto de perfil renomeada para profile_pic.jpg")
                break
        
        # Exibir informações
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