import fitz, os 
import easyocr 
from typing import Tuple
from . import paths
from base64 import b64decode
import json
from PIL import Image 



# On instancie l'extracteur OCR
reader = easyocr.Reader(['en','fr'], gpu=False)

import shutil

def pdf2img(pdfFile: str, pages: Tuple = None):
    # On charge le document
    pdf = fitz.open(pdfFile)
    # On détermine la liste des fichiers générés
    pngFiles = []
    # Pour chaque page du pdf
    pngPath = str(paths.rootPath_img) + str(paths.tmpDirImg) + os.path.basename(str(pdfFile).split('.')[0])
    
    try:
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

            # Si le répertoire dédié au pdf n'existe pas encore, on le crée
            if not os.path.exists(pngPath):
                os.makedirs(pngPath)

            pngFile = pngPath + "_" + f"page{pageId+1}.png"
            pagePix.save(pngFile)
            pngFiles.append(pngFile)

        pdf.close()

        # On retourne la liste des pngs générés
        return pngFiles

    finally:
        # On supprime le répertoire et son contenu après le traitement
        if os.path.exists(pngPath):
            shutil.rmtree(pngPath)

def convert_to_png(input_path, output_path):
    try:
        img = Image.open(input_path)
        output_file = os.path.join(output_path, os.path.basename(str(input_path).split('.')[0]) + '.png')
        img.save(output_file, 'PNG')
        return output_file  # Retourne le chemin complet du fichier PNG créé
    except Exception as e:
        print(f"An error occurred during image conversion: {str(e)}")
        raise



def img2text(pngFile) :
    try:
        textList = []
        # On récupère le texte contenu dans l'image par extraction OCR
        detection_result = reader.detect(pngFile, width_ths=0.7, mag_ratio=1.5)
        recognition_results = reader.recognize(pngFile, horizontal_list = detection_result[0][0], free_list=[])
        #print(recognition_results)

        for result in recognition_results:
            textList.append((result[1]))
    # On retourne la liste des textes extraits de l'image

    except:
        output_path = str(paths.rootPath) + paths.tmpDirImg + os.path.basename(str(pngFile).split('.')[0])

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        #convertir jpg en png
        new_png_file = convert_to_png(pngFile, output_path)

        # print(f'image bien convertie, avec comme nom{new_png_file}')
        detection_result = reader.detect(new_png_file, width_ths=0.7, mag_ratio=1.5)
        # print("detection result :",detection_result)
        recognition_results = reader.recognize(new_png_file, horizontal_list = detection_result[0][0], free_list=[])
        # print("recognition result :",recognition_results)
        for result in recognition_results:
            textList.append((result[1]))
        # On retourne la liste des textes extraits de l'image
    
    return "".join(textList)



def img2textlist(pngFile):
    try:
        textList = []
        # On récupère le texte contenu dans l'image par extraction OCR
        detection_result = reader.detect(pngFile, width_ths=0.7, mag_ratio=1.5)
        recognition_results = reader.recognize(pngFile, horizontal_list = detection_result[0][0], free_list=[])

        for result in recognition_results:
            textList.append((result[1]))
    # On retourne la liste des textes extraits de l'image

    except:
        output_path = str(paths.rootPath) + paths.tmpDirImg + os.path.basename(str(pngFile).split('.')[0])
        #print(output_path)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        #convertir jpg en png
        new_png_file = convert_to_png(pngFile, output_path)
        #print(new_png_file)

        # print(f'image bien convertie, avec comme nom{new_png_file}')
        detection_result = reader.detect(new_png_file, width_ths=0.7, mag_ratio=1.5)
        # print("detection result :",detection_result)
        recognition_results = reader.recognize(new_png_file, horizontal_list = detection_result[0][0], free_list=[])
        # print("recognition result :",recognition_results)
        for result in recognition_results:
            textList.append((result[1]))
        # On retourne la liste des textes extraits de l'image
    
    return textList