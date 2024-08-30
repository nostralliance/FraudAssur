import os
from mylib import functions, criterias
import signal
from datetime import datetime
from pydantic import BaseModel
from typing import Annotated, Union, List
import hashlib
import hmac
from fastapi import Depends, FastAPI, HTTPException, status, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import requests
from fastapi.responses import JSONResponse
import shutil

app = FastAPI()

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


# Dossier de destination pour les documents suspicieux
meta_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\metadonne"
date_crea_mod_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\crea_mod"
adher_suspic_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\adherent_suspicieux"
date_compare_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\date_compare"
date_feriee_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\date_feriee"
ref_archiv_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\ref_archivage"
finess_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\finess_faux"
medic_mater_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\medical_materiel"
ro_non_soum_folder = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\ro_non_soumis"
no_suspicion = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\dataset_result\pas_fraude"



folder_path = r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\FraudAssur\pdf_test\POUR CONTROLE ET AVIS  N164164 LIORAH CHETRIT"



@app.post('/process_json')
async def process_files():
    global total_modification_creation, total_factures, total_ok, total_ko, total_taux_compare, total_dateferiee, total_refarchivesfaux, total_rononsoumis, total_finessfaux, total_datecompare, total_count_ref, total_adherentssoussurveillance, total_medical_materiel, total_meta

    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Folder does not exist")

    results = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, 'rb') as file_handle:
                binary_data = file_handle.read()
                
            file_extension = criterias.detect_file_type(binary_data)
            result = {"filename": filename, "success": "False", "message": "Pas de suspicion de fraude sur ce document"}  # Default result
            shutil.move(file_path, no_suspicion)

            if file_extension == 'pdf':
                total_factures += 1
                pdf_file_path = f'temp_{filename}'
                print(f"le fichier en court de traitement est :{pdf_file_path}")
                with open(pdf_file_path, 'wb') as pdf_out:
                    pdf_out.write(binary_data)
                
                if criterias.detecter_fraude_documentaire(pdf_file_path):
                    total_ok += 1
                    total_meta += 1
                    result = {"filename": filename, "success": "True", "message": "La provenance du document est suspicieuse : photoshop, canva, excel ou word"}
                    shutil.move(file_path, meta_folder)


                else:
                    pages = None
                    png_files = functions.pdf2img(pdf_file_path, pages)
                    for png_file in png_files:
                        png_text = functions.img2text(png_file)
                        try:


                            if criterias.refarchivesfaux(png_text):
                                total_ok += 1
                                total_refarchivesfaux += 1
                                result = {"filename": filename, "success": "True", "message": "Fausse référence d'archivage trouvée sur ce document"}
                                shutil.move(file_path, ref_archiv_folder)
                                break

                        except Exception as e:
                            print(e)
                            total_ko += 1
                            result = {"filename": filename, "success": "False", "message": "Erreur sur le document"}
                            break

                    os.remove(pdf_file_path)

            elif file_extension in ['jpg', 'jpeg', 'png']:
                try:
                    
                    if criterias.detecter_fraude_documentaire(file_path):
                        total_ok += 1
                        total_meta += 1
                        result = {"filename": filename, "success": "True", "message": "La provenance du document est suspicieuse : photoshop, canva, excel ou word"}
                    
                    else:
                        png_text = functions.img2text(file_path)

                        
                        if criterias.refarchivesfaux(png_text):
                            total_ok += 1
                            total_refarchivesfaux += 1
                            result = {"filename": filename, "success": "True", "message": "Fausse référence d'archivage trouvée sur ce document"}
                        
                        
                        else:
                                total_ko += 1
                                result = {"filename": filename, "success": "False", "message": "Pas de suspicion de fraude sur ce document"}
                                shutil.copy(file_path, no_suspicion)
                except Exception as e:
                    print(f"Erreur lors du traitement du fichier image : {e}")
                    total_ko += 1
                    result = {"filename": filename, "success": "False", "message": "Erreur lors du traitement de l'image"}

            results.append(result)

        except Exception as e:
            print(f"Erreur lors du traitement du fichier {filename} : {e}")
            total_ko += 1
            results.append({"filename": filename, "success": "False", "message": "Erreur lors du traitement du fichier"})

    return {"results": results}


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------print_statistics------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------

def print_statistics(signal, frame):
    print(f"Total factures traitées: {total_factures}")
    print(f"Total de facture suspicieuse: {total_ok}")
    print(f"Total de facture non suspicieuse: {total_ko}")
    #print(f"nombre de suspicion la différence prix/taux/total: {total_taux_compare}")
    #print(f"nombre de suspicion sur la date feriee: {total_dateferiee}")
    print(f"nombre de reference d'archivage suspicieuse: {total_refarchivesfaux}")
    #print(f"nombre de RO non soumis: {total_rononsoumis}")
    #print(f"nombre de finess suspicieux: {total_finessfaux}")
    #print(f"nombre de date de soins suspicieuse par rapport a la date de réglement: {total_datecompare}")
    #print(f"nombre de reference d'archivage supérieur a 17: {total_count_ref}")
    #print(f"nombre d'adherent suspicieux: {total_adherentssoussurveillance}")
    #print(f"nombre de montant superieur a 150 sur facture materiel: {total_medical_materiel}")
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
    uvicorn.run(app, host="0.0.0.0", port=8000)