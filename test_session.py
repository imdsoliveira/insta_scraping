# test_session.py
import os
import instaloader
import time
import random
import requests
from dotenv import load_dotenv
from pathlib import Path

# Carrega variáveis do ambiente
load_dotenv()

# Configurações
MAX_RETRIES = 3
BASE_DELAY = 5
USE_DELAY = True

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def random_delay():
    """Implementa um delay aleatório mais natural"""
    if USE_DELAY:
        delay = random.uniform(3, 7) + random.random()
        time.sleep(delay)

class CustomInstaloader(instaloader.Instaloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurações adicionais para simular comportamento humano
        self.context.sleep = True
        self.context.max_connection_attempts = 3
        self.context.request_timeout = 30

    def get_anonymous_session(self):
        random_delay()
        return super().get_anonymous_session()

def retry_operation(operation, max_retries=MAX_RETRIES):
    """Tenta uma operação com retry e delay exponencial"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            last_error = e
            if attempt == max_retries - 1:
                raise
            delay = BASE_DELAY * (2 ** attempt) + random.uniform(2, 5)
            log_info(f"Tentativa {attempt + 1} falhou. Aguardando {delay:.1f}s...")
            time.sleep(delay)
    raise last_error

def test_instagram_session():
    """Testa a sessão do Instagram"""
    try:
        username = os.getenv("INSTAGRAM_USERNAME")
        if not username:
            raise ValueError("INSTAGRAM_USERNAME não configurado no .env")
            
        session_file = os.path.abspath(f"{username}_session")
        
        if not os.path.exists(session_file):
            raise ValueError(f"Arquivo de sessão não encontrado: {session_file}")
        
        log_info(f"Encontrado arquivo de sessão: {session_file}")
        
        # Criar instância customizada do Instaloader
        loader = CustomInstaloader(
            sleep=True,
            quiet=False,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern=''
        )
        
        # Carregar sessão
        log_info("Tentando carregar sessão...")
        loader.load_session_from_file(username, session_file)
        log_info("Sessão carregada com sucesso!")
        
        def test_profile(test_username):
            def _get_profile():
                random_delay()
                profile = instaloader.Profile.from_username(loader.context, test_username)
                log_info(f"Perfil acessado: @{profile.username}")
                log_info(f"Nome completo: {profile.full_name}")
                log_info(f"Seguidores: {profile.followers}")
                return profile
            
            return retry_operation(_get_profile)

        # Lista de perfis para teste (menos populares primeiro)
        test_profiles = ['natgeo', 'nasa', 'bbcnews']
        
        log_info("\nIniciando testes com perfis...")
        for test_username in test_profiles:
            try:
                log_info(f"\nTestando acesso ao perfil @{test_username}")
                profile = test_profile(test_username)
                log_info(f"Teste com @{test_username} bem sucedido!")
                return True
            except instaloader.exceptions.ConnectionException as e:
                log_error(f"Erro de conexão ao testar @{test_username}: {str(e)}")
                time.sleep(random.uniform(7, 15))
            except Exception as e:
                log_error(f"Erro ao testar perfil @{test_username}: {str(e)}")
                time.sleep(random.uniform(5, 10))
        
        raise Exception("Nenhum teste foi bem sucedido")
        
    except Exception as e:
        log_error(f"Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando teste de sessão do Instagram...")
    try:
        success = test_instagram_session()
        print(f"\nResultado final do teste: {'SUCESSO' if success else 'FALHA'}")
    except KeyboardInterrupt:
        print("\nTeste interrompido pelo usuário")
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}")