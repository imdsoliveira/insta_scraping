from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import instaloader
import requests

app = FastAPI()

class InstagramProfile(BaseModel):
    username: str

@app.post("/get_profile/")
async def get_instagram_profile(data: InstagramProfile):
    username = data.username
    loader = instaloader.Instaloader()

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        profile_pic_url = profile.profile_pic_url
        response = requests.get(profile_pic_url)
        if response.status_code == 200:
            return Response(content=response.content, media_type="image/jpeg")
        else:
            raise HTTPException(status_code=500, detail="Erro ao baixar a imagem.")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error: {str(e)}")