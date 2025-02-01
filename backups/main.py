# main.py

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import instaloader
import requests
import logging
import os
import json
import http.cookiejar as cookiejar
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (se existir)
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class InstagramProfile(BaseModel):
    username: str

def load_cookies(cookies_file: str) -> cookiejar.CookieJar:
    """
    Carrega cookies de um arquivo JSON e os converte para CookieJar.
    """
    jar = cookiejar.CookieJar()
    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
            for cookie in cookies:
                c = cookiejar.Cookie(
                    version=0,
                    name=cookie['name'],
                    value=cookie['value'],
                    port=None,
                    port_specified=False,
                    domain=cookie['domain'],
                    domain_specified=bool(cookie['domain']),
                    domain_initial_dot=cookie['domain'].startswith('.'),
                    path=cookie['path'],
                    path_specified=bool(cookie['path']),
                    secure=cookie['secure'],
                    expires=int(cookie['expirationDate']) if 'expirationDate' in cookie and cookie['expirationDate'] else None,
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={'HttpOnly': cookie.get('httpOnly', False)},
                    rfc2109=False,
                )
                jar.set_cookie(c)
        logger.info("Cookies carregados com sucesso!")
    except FileNotFoundError:
        logger.error(f"Arquivo de cookies '{cookies_file}' não encontrado.")
    except Exception as e:
        logger.error(f"Erro ao carregar cookies: {e}")
    return jar

# Inicializa Instaloader e carrega os cookies
loader = instaloader.Instaloader()

cookies_file = 'cookies.json'  # Caminho para o arquivo de cookies

if os.path.exists(cookies_file):
    logger.info("Carregando cookies do arquivo...")
    jar = load_cookies(cookies_file)
    if hasattr(loader.context, 'session'):
        loader.context.session.cookies = jar  # Atribuição correta
        logger.info("Cookies atribuídos à sessão do Instaloader.")
    else:
        logger.error("Atributo 'session' não encontrado em 'InstaloaderContext'. Verifique a versão do Instaloader.")
else:
    logger.error(f"Arquivo de cookies '{cookies_file}' não encontrado.")
    # Opcional: você pode optar por sair ou continuar sem autenticação
    # Aqui, continuaremos sem autenticação

@app.post("/api/get_instagram_profile")
async def get_instagram_profile(data: InstagramProfile):
    """
    Endpoint para obter a imagem de perfil de um usuário do Instagram.
    Retorna a imagem como 'image/jpeg'.
    """
    username = data.username
    try:
        logger.info(f"Buscando perfil: {username}")
        profile = instaloader.Profile.from_username(loader.context, username)
        profile_pic_url = profile.profile_pic_url
        logger.info(f"URL da foto de perfil: {profile_pic_url}")

        response = requests.get(profile_pic_url)
        if response.status_code == 200:
            logger.info("Imagem de perfil baixada com sucesso.")
            return Response(content=response.content, media_type="image/jpeg")
        else:
            logger.error("Erro ao baixar a imagem de perfil.")
            raise HTTPException(status_code=500, detail="Erro ao baixar a imagem de perfil.")
    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"Perfil '{username}' não encontrado.")
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    except instaloader.exceptions.ConnectionException as e:
        logger.error(f"Erro de conexão: {e}")
        raise HTTPException(status_code=500, detail="Erro de conexão com o Instagram.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
