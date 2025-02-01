# test_instaloader.py

import os
from dotenv import load_dotenv
import instaloader

# Carrega as variáveis do arquivo .env
load_dotenv()

# Correção: Use os nomes das variáveis, não os valores
ig_username = os.getenv("IG_USERNAME")
ig_password = os.getenv("IG_PASSWORD")

loader = instaloader.Instaloader()

try:
    loader.login(ig_username, ig_password)
    print("Login realizado com sucesso!")
except instaloader.exceptions.BadCredentialsException:
    print("Erro: Credenciais inválidas fornecidas.")
except instaloader.exceptions.TwoFactorAuthRequiredException:
    print("Erro: Autenticação de dois fatores (2FA) requerida.")
except Exception as e:
    print(f"Erro ao fazer login: {e}")
