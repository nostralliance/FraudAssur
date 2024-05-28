import fitz, os 
import easyocr 
from typing import Tuple
from . import paths
from base64 import b64decode
import json
from PIL import Image 



# On instancie l'extracteur OCR
reader = easyocr.Reader(['en','fr'], gpu=False)



# def base64_to_pdf(fichier_json):
def base64topdf():
    with open(r"C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\Fraude\code_Tom\base64_to_pdf\api\base64.json", 'r') as f:
        json_data = json.load(f)
        base = json_data.get("base64")
        result = b64decode(base, validate=True)
    return result

def pdf2img(pdfFile: str ,pages: Tuple = None):
    # On charge le document
    pdf = fitz.open(pdfFile)
    # On détermine la liste des fichiers générés
    pngFiles = []
    # Pour chaque page du pdf
    for pageId in range(pdf.page_count):

        if str(pages) != str(None):
            if str(pageId) not in str(pages):
                continue

        # On récupère la page courante
        page = pdf[pageId]
        # On convertit la page courante
        pageMatrix = fitz.Matrix(2, 2)
        pagePix = page.get_pixmap(matrix=pageMatrix, alpha=False)
        # On exporte la page générée
        pngPath = r'C:\Users\pierrontl\OneDrive - GIE SIMA\Documents\GitHub\Fraude\code_Tom\docker\v2\app2\images'+ '/' + str(paths.rootPath) + paths.tmpDir + os.path.basename(pdfFile) +'/'
        # Si le répertoire dédié au pdf n'existe pas encore, on le crée
        if not os.path.exists(pngPath):
            os.makedirs(pngPath)

        pngFile = pngPath + f"page{pageId+1}.png"
        pagePix.save(pngFile)
        pngFiles.append(pngFile)

    pdf.close()
    # On retourne la liste des pngs générés
    return pngFiles


def nbrpix(pngFile):
    # Ouvrir l'image
    image = Image.open(pngFile)

    # Obtenir les dimensions de l'image (largeur x hauteur)
    width, height = image.size

    # Obtenir le mode de l'image (par exemple, 'RGB' pour une image couleur)
    mode = image.mode

    # Calculer le nombre total de pixels
    pixel_count = width * height

    # Afficher les informations
    print(f"Dimensions de l'image : {width} x {height}")
    print(f"Mode de l'image : {mode}")
    print(f"Nombre total de pixels : {pixel_count}")
    




def img2text(pngFile) :
    # On récupère le texte contenu dans l'image par extraction OCR
    detection_result = reader.detect(pngFile, width_ths=0.7, mag_ratio=1.5)
    recognition_results = reader.recognize(pngFile, horizontal_list = detection_result[0][0], free_list=[])

    textList = []
    for result in recognition_results:
        textList.append((result[1]))
    # On retourne la liste des textes extraits de l'image
    return "".join(textList)



def img2textlist(pngFile):
    # On récupère le texte contenu dans l'image par extraction OCR
    detection_result = reader.detect(pngFile, width_ths=0.6, mag_ratio=1.5)
    recognition_results = reader.recognize(pngFile, horizontal_list = detection_result[0][0], free_list=[])

    textList = []
    for result in recognition_results:
        textList.append((result[1]))
    # print("le text list est :\n",textList)
    # On retourne la liste des textes extraits de l'image
    return textList