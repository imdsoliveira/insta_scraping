# save_cookies.py
import instaloader
from dotenv import load_dotenv
import os
import shutil

def save_session_local():
    try:
        # Carrega variáveis do ambiente
        load_dotenv()
        
        # Obtém credenciais do .env
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        
        # Cria instância do Instaloader
        L = instaloader.Instaloader()
        print(f"Tentando login com usuário {username}...")
        
        # Faz login
        L.login(username, password)
        print("Login bem sucedido!")
        
        # Salva a sessão
        session_file = f"{username}_session"
        L.save_session_to_file(session_file)
        print(f"Sessão salva em {session_file}")
        
        # Cria uma cópia de backup
        backup_file = f"{session_file}.backup"
        shutil.copy2(session_file, backup_file)
        print(f"Backup criado em {backup_file}")
        
        return True
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

if __name__ == "__main__":
    save_session_local()