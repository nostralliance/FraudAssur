from typing import Annotated, Union
import hashlib
import hmac
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Base de données simulée des utilisateurs
fake_users_db = {
    "tomloupierron": {
        "username": "tomloupierron",
        "full_name": "tom pierron",
        "email": "tomlou70@icloud.com",
        "hashed_password": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",  # hashed version of 'secret'
        "disabled": False,
    },
    "benilboudo": {
        "username": "benilboudo",
        "full_name": "ben ilboudo",
        "email": "ben@gmai.com",
        "hashed_password": "35224d0d3465d74e855f8d69a136e79c744ea35a675d3393360a327cbf6359a2",  # hashed version of 'secret2'
        "disabled": False,
    },
}

app = FastAPI()

# Fonction pour hasher le mot de passe en utilisant hashlib
def hash_password(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Fonction pour vérifier le mot de passe
def verify_password(plain_password: str, hashed_password: str):
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

# OAuth2PasswordBearer s'attend à ce que le client fournisse le token en tant que Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modèle de données pour un utilisateur
class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

# Modèle de données pour un utilisateur avec mot de passe haché
class UserInDB(User):
    hashed_password: str

# Récupération d'un utilisateur depuis la base de données simulée
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

# Décodage du token en tant que username
def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user

# Récupération de l'utilisateur courant
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Vérification que l'utilisateur n'est pas désactivé
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoint pour générer un token
@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Le `access_token` est maintenant défini comme le `username`
    return {"access_token": user.username, "token_type": "bearer"}

# Endpoint pour lire les informations de l'utilisateur courant
@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
