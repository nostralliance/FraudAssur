import os
from mylib import functions, criterias
import signal
from datetime import datetime
import uuid
import shutil
import pathlib
from pydantic import BaseModel
from typing import Annotated, Union, List
import hashlib
import hmac
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests
from fastapi.responses import JSONResponse

# Configuration de l'API externe
OCR_API_URL = "https://kfjqcvjg55254bjskf45s23kg4sg.giesima.fr"  # Remplacez par l'URL de votre API
OCR_API_LOGIN = "apin@fraude.fr"
OCR_API_PASSWORD = "zeFraude"

# Base de données simulée des utilisateurs
fake_users_db = {
    "tomloupierron": {
        "username": "tomloupierron",
        "full_name": "tom pierron",
        "email": "tomlou70@icloud.com",
        "hashed_password": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
        "disabled": False,
    },
    "benilboudo": {
        "username": "benilboudo",
        "full_name": "ben ilboudo",
        "email": "ben@gmai.com",
        "hashed_password": "35224d0d3465d74e855f8d69a136e79c744ea35a675d3393360a327cbf6359a2",
        "disabled": False,
    },
}

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

app = FastAPI()

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

class PDFRequest(BaseModel):
    url: str
    idm: str

# Variables globales pour les statistiques
total_factures = 0
total_ok = 0
total_ko = 0
total_taux_compare = 0
total_dateferiee = 0
total_refarchivesfaux = 0
total_rononsoumis = 0
total_finessfaux = 0
total_datecompare = 0
total_count_ref = 0
total_adherentssoussurveillance = 0
total_medical_materiel = 0
total_meta = 0
total_modification_creation = 0

@app.post('/process_json')
async def process_file(current_user: Annotated[User, Depends(get_current_active_user)], request: PDFRequest):
    global total_modification_creation, total_factures, total_ok, total_ko, total_taux_compare, total_dateferiee, total_refarchivesfaux, total_rononsoumis, total_finessfaux, total_datecompare, total_count_ref, total_adherentssoussurveillance, total_medical_materiel, total_meta
    total_factures += 1
    
    ident = request.idm
    file = request.url
    results = []
    
    print(f'Les noms de fichiers sont : {file}')
    try:
        if not os.path.exists(file):
            raise HTTPException(status_code=400, detail="File does not exist")

        with open(file, 'rb') as file_handle:
            binary_data = file_handle.read()

        file_extension = criterias.detect_file_type(binary_data)
        result = {"docid": ident, "success": "ko", "message": "Pas de suspicion de fraude sur cette facture"}  # Default result

        if file_extension == 'pdf':
            pdf_file_path = f'temp_{ident}.pdf'
            with open(pdf_file_path, 'wb') as pdf_out:
                pdf_out.write(binary_data)
            
            if criterias.detecter_fraude_documentaire(pdf_file_path):
                total_ok += 1
                total_meta += 1
                result = {"docid": ident, "success": "ok", "message": "la provenance du document est suspicieuse : photoshop, canva, excel ou word"}

            elif criterias.detect_modification_creation(pdf_file_path):
                total_ok += 1
                total_modification_creation += 1
                result = {"docid": ident, "success": "ok", "message": "date de modification supérieur a 1 mois par rapport a la date de création"}
            
            else:
                pages = None
                png_files = functions.pdf2img(pdf_file_path, pages)
                for png_file in png_files:
                    print("---Traitement de la page : " + os.path.basename(png_file) + "...")
                    png_text = functions.img2text(png_file)
                    try:
                        if criterias.finessfaux(png_text):
                            total_ok += 1
                            total_finessfaux += 1
                            result = {"docid": ident, "success": "ok", "message": "numéro finess sur facture"}
                            break

                        if criterias.adherentssoussurveillance(png_text):
                            total_ok += 1
                            total_adherentssoussurveillance += 1
                            result = {"docid": ident, "success": "ok", "message": "adherent suspicieux"}
                            break

                        if criterias.refarchivesfaux(png_text):
                            total_ok += 1
                            total_refarchivesfaux += 1
                            result = {"docid": ident, "success": "ok", "message": "reference archivage fausse sur facture"}
                            break

                        if criterias.rononsoumis(png_text):
                            total_ok += 1
                            total_rononsoumis += 1
                            result = {"docid": ident, "success": "ok", "message": "regime obligatoire non soumis sur facture"}
                            break

                        png_text_list = functions.img2textlist(png_file)
                        if criterias.date_compare(png_text_list):
                            total_ok += 1
                            total_datecompare += 1
                            result = {"docid": ident, "success": "ok", "message": "date reglement supérieur a date de soins sur facture"}
                            break

                        if criterias.medical_materiel(png_text):
                            total_ok += 1
                            total_medical_materiel += 1
                            result = {"docid": ident, "success": "ok", "message": "montant superieur a 150 euros sur facture medical"}
                            break

                        if criterias.dateferiee(png_text):
                            total_ok += 1
                            total_dateferiee += 1
                            result = {"docid": ident, "success": "ok", "message": "date fériée sur facture"}
                            break

                    except Exception as e:
                        print(e)
                        total_ko += 1
                        result = {"docid": ident, "success": "ko", "message": "500, erreur sur le document"}
                        break

                os.remove(pdf_file_path)

        elif file_extension in ['jpg', 'jpeg', 'png']:
            print("OCR fichier image " + file)
            if criterias.detecter_fraude_documentaire(file):
                total_ok += 1
                total_meta += 1
                result = {"docid": ident, "success": "ok", "message": "la provenance du document est suspicieuse : photoshop, canva, excel ou word"}
            else:
                png_text = functions.img2text(file)
                if criterias.finessfaux(png_text):
                    total_ok += 1
                    total_finessfaux += 1
                    result = {"docid": ident, "success": "ok", "message": "numéro finess sur facture"}
                elif criterias.adherentssoussurveillance(png_text):
                    total_ok += 1
                    total_adherentssoussurveillance += 1
                    result = {"docid": ident, "success": "ok", "message": "adherent suspicieux"}
                elif criterias.refarchivesfaux(png_text):
                    total_ok += 1
                    total_refarchivesfaux += 1
                    result = {"docid": ident, "success": "ok", "message": "reference archivage fausse sur facture"}
                elif criterias.rononsoumis(png_text):
                    total_ok += 1
                    total_rononsoumis += 1
                    result = {"docid": ident, "success": "ok", "message": "regime obligatoire non soumis sur facture"}
                else:
                    png_text_list = functions.img2textlist(file)
                    if criterias.date_compare(png_text_list):
                        total_ok += 1
                        total_datecompare += 1
                        result = {"docid": ident, "success": "ok", "message": "date reglement supérieur a date de soins sur facture"}
                    elif criterias.medical_materiel(png_text):
                        total_ok += 1
                        total_medical_materiel += 1
                        result = {"docid": ident, "success": "ok", "message": "montant superieur a 150 euros sur facture medical"}
                    elif criterias.dateferiee(png_text):
                        total_ok += 1
                        total_dateferiee += 1
                        result = {"docid": ident, "success": "ok", "message": "date fériée sur facture"}
                    else:
                        total_ko += 1
                        result = {"docid": ident, "success": "ko", "message": "Pas de suspicion de fraude sur cette facture"}
        
        # Envoi des résultats à l'API externe
        try:
            auth_response = requests.post(OCR_API_URL + "/secure/token", json={"login": OCR_API_LOGIN, "password": OCR_API_PASSWORD})
            auth_response.raise_for_status()
            access_token = auth_response.json().get('access_token')

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            response = requests.post(OCR_API_URL+"/callback/fraude", json=result, headers=headers)
            response.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending results to external API: {e}")

    except Exception as e:
        print(e)
        total_ko += 1
        result = {"docid": ident, "success": "ko", "message": "500, erreur sur le document"}

    return JSONResponse(content=result)


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------print_statistics------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------

def print_statistics(signal, frame):
    print(f"Total factures traitées: {total_factures}")
    print(f"Total de facture suspicieuse: {total_ok}")
    print(f"Total de facture non suspicieuse: {total_ko}")
    print(f"nombre de suspicion la différence prix/taux/total: {total_taux_compare}")
    print(f"nombre de suspicion sur la date feriee: {total_dateferiee}")
    print(f"nombre de reference d'archivage suspicieuse: {total_refarchivesfaux}")
    print(f"nombre de RO non soumis: {total_rononsoumis}")
    print(f"nombre de finess suspicieux: {total_finessfaux}")
    print(f"nombre de date de soins suspicieuse par rapport a la date de réglement: {total_datecompare}")
    print(f"nombre de reference d'archivage supérieur a 17: {total_count_ref}")
    print(f"nombre d'adherent suspicieux: {total_adherentssoussurveillance}")
    print(f"nombre de montant superieur a 150 sur facture materiel: {total_medical_materiel}")
    print(f"metadonne trouver : {total_meta}")
    print(f"a lheure:{datetime.now()}")
    exit(0)

#Ces lignes de code enregistrent une fonction pour imprimer des statistiques lorsque le programme reçoit des signaux d'interruption (Ctrl+C) ou de terminaison, afin de s'arrêter proprement.
signal.signal(signal.SIGINT, print_statistics)
signal.signal(signal.SIGTERM, print_statistics)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------lancer l'app------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)