import instaloader

# Cria uma instância do Instaloader
loader = instaloader.Instaloader()

# Define o nome de usuário do perfil desejado
username = 'dracintiacardoso'

# Obtém o perfil
profile = instaloader.Profile.from_username(loader.context, username)

# Exibe as informações desejadas
print(f"Nome completo: {profile.full_name}")
print(f"Biografia: {profile.biography}")
print(f"Total de publicações: {profile.mediacount}")
print(f"Total de seguidores: {profile.followers}")
print(f"URL da foto de perfil: {profile.profile_pic_url}")

# Opcional: Baixa a foto de perfil
loader.download_profilepic(profile)
