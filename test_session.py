# test_session.py
import os
import instaloader
import time
import random
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
    """Implementa um delay aleatório"""
    if USE_DELAY:
        delay = random.uniform(2, 5)
        time.sleep(delay)

class CustomInstaloader(instaloader.Instaloader):
    def get_anonymous_session(self):
        """Sobrescreve o método para adicionar delays"""
        random_delay()
        return super().get_anonymous_session()

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

def test_instagram_session():
    """Testa a sessão do Instagram"""
    try:
        # Verificar credenciais
        username = os.getenv("INSTAGRAM_USERNAME")
        if not username:
            raise ValueError("INSTAGRAM_USERNAME não configurado no .env")
            
        # Usar caminho completo do arquivo de sessão
        session_file = os.path.abspath(f"{username}_session")
        
        if not os.path.exists(session_file):
            raise ValueError(f"Arquivo de sessão não encontrado: {session_file}")
        
        log_info(f"Encontrado arquivo de sessão: {session_file}")
        
        # Criar instância do Instaloader com delays
        loader = CustomInstaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            request_timeout=30
        )
        
        # Carregar sessão usando caminho completo
        log_info("Tentando carregar sessão...")
        loader.load_session_from_file(username, session_file)
        log_info("Sessão carregada com sucesso!")
        
        # Função para testar um perfil
        def test_profile(test_username):
            def _get_profile():
                random_delay()
                profile = instaloader.Profile.from_username(loader.context, test_username)
                log_info(f"Perfil acessado: @{profile.username}")
                log_info(f"Nome completo: {profile.full_name}")
                log_info(f"Seguidores: {profile.followers}")
                return profile
            
            return retry_operation(_get_profile)
        
        # Testar com alguns perfis populares
        test_profiles = ['instagram', 'cristiano', 'neymarjr']
        
        log_info("\nIniciando testes com perfis...")
        for test_username in test_profiles:
            try:
                log_info(f"\nTestando acesso ao perfil @{test_username}")
                profile = test_profile(test_username)
                log_info(f"Teste com @{test_username} bem sucedido!")
                # Se conseguir acessar um perfil, podemos considerar que está funcionando
                return True
            except Exception as e:
                log_error(f"Erro ao testar perfil @{test_username}: {str(e)}")
                continue
        
        raise Exception("Nenhum teste foi bem sucedido")
        
    except Exception as e:
        log_error(f"Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando teste de sessão do Instagram...")
    success = test_instagram_session()
    print(f"\nResultado final do teste: {'SUCESSO' if success else 'FALHA'}")