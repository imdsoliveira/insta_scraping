# main.py

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import instaloader
import requests
import logging
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class InstagramProfile(BaseModel):
    username: str

@app.post("/api/get_instagram_profile")
async def get_instagram_profile(data: InstagramProfile):
    """
    Endpoint para obter a imagem de perfil de um usuário do Instagram.
    Retorna a imagem como 'image/jpeg'.
    """
    username = data.username
    loader = instaloader.Instaloader()

    try:
        ig_username = os.getenv("IG_USERNAME")
        ig_password = os.getenv("IG_PASSWORD")

        if not ig_username or not ig_password:
            logger.error("Credenciais de login não fornecidas no .env.")
            raise HTTPException(status_code=500, detail="Credenciais de login não configuradas.")

        logger.info("Tentando fazer login no Instagram...")
        try:
            loader.login(ig_username, ig_password)
            logger.info("Login realizado com sucesso!")
        except instaloader.exceptions.BadCredentialsException:
            logger.error("Credenciais inválidas fornecidas.")
            raise HTTPException(status_code=401, detail="Credenciais inválidas fornecidas.")
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            logger.error("Autenticação de dois fatores (2FA) requerida.")
            raise HTTPException(status_code=403, detail="Autenticação de dois fatores (2FA) requerida.")
        except Exception as e:
            logger.error(f"Falha no login: {e}")
            raise HTTPException(status_code=500, detail=f"Falha no login: {e}")

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
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
