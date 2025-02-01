import os
import instaloader
import time
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def test_instagram_session():
    try:
        username = os.getenv("INSTAGRAM_USERNAME")
        session_file = f"{username}_session"
        
        if not os.path.exists(session_file):
            print(f"Arquivo de sessão não encontrado: {session_file}")
            return False
        
        print(f"Encontrado arquivo de sessão: {session_file}")
        
        # Criar instância do Instaloader
        L = instaloader.Instaloader()
        
        # Carregar sessão
        print("Tentando carregar sessão...")
        L.load_session_from_file(username, session_file)
        print("Sessão carregada!")
        
        # Testar com um perfil
        print("\nTestando com perfil @instagram...")
        profile = instaloader.Profile.from_username(L.context, "instagram")
        print(f"Nome completo: {profile.full_name}")
        print(f"Seguidores: {profile.followers}")
        
        return True
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando teste de sessão do Instagram...")
    success = test_instagram_session()
    print(f"\nResultado do teste: {'SUCESSO' if success else 'FALHA'}")