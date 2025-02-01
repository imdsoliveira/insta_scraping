# save_session.py
import os
import instaloader
from dotenv import load_dotenv

def save_session():
    try:
        # Carrega variáveis do ambiente
        load_dotenv()
        
        # Obtém credenciais do .env
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        
        if not username or not password:
            print("Erro: Configure INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD no .env")
            return False
        
        # Cria instância do Instaloader
        L = instaloader.Instaloader()
        print(f"Tentando login com usuário {username}...")
        
        # Faz login
        L.login(username, password)
        print("Login bem sucedido!")
        
        # Salva a sessão
        L.save_session_to_file()
        print(f"Sessão salva em {username}_session")
        
        # Testa a sessão
        print("\nTestando a sessão...")
        test = instaloader.Instaloader()
        test.load_session_from_file(username)
        
        # Tenta acessar um perfil
        test_profile = "instagram"
        profile = instaloader.Profile.from_username(test.context, test_profile)
        print(f"Teste concluído! Conseguimos acessar o perfil @{test_profile}")
        
        return True
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

if __name__ == "__main__":
    save_session()