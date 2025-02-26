import fitz, os 
import easyocr 
from typing import Tuple
from . import paths
from base64 import b64decode
import json
from PIL import Image 
import shutil
from typing import List, Dict
import re


# On instancie l'extracteur OCR
reader = easyocr.Reader(['en','fr'], gpu=False)

def extract_text_with_fitz(pdf_file: str) -> List[str]:
    pdf = fitz.open(pdf_file)
    text_list = [page.get_text() for page in pdf]
    pdf.close()
    return text_list


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
        os.remove(str(output_path))

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


def extract_dates_and_amounts(text: str) -> Dict[str, list]:
    date_pattern = r"\d{1,2}/\d{1,2}/\d{2,4}"
    montant_pattern_avant = r"(?:E\s*|€\s*|euro[(?s?)?]\s*)\s*\d+(?:[.,]\d{1,2})?"
    montant_pattern_apres = r"\d+(?:[.,]\d{1,2})?\s*(?:E|€|euro[(?s?)?])"
    code_pattern = r"[A-Za-z]\s?\d{5}\s*[A-Za-z]"
    
    dates = re.findall(date_pattern, text)
    amounts_avant = re.findall(montant_pattern_avant, text)
    amounts_apres = re.findall(montant_pattern_apres, text)
    codes = re.findall(code_pattern, text)
    
    return {"dates": dates, "amounts_avant": amounts_avant, "amounts_apres": amounts_apres, "codes": codes}

def detect_fraud(fitz_data: Dict[str, list], ocr_data: Dict[str, list]):
    # Vérification des dates
    if fitz_data['dates'] and ocr_data['dates'] and len(fitz_data['dates']) > len(ocr_data['dates']):
        resultat = True
    elif fitz_data['amounts_avant'] and ocr_data['amounts_avant'] and len(fitz_data['amounts_avant']) > len(ocr_data['amounts_avant']):
        resultat = True
    elif fitz_data['amounts_apres'] and ocr_data['amounts_apres'] and len(fitz_data['amounts_apres']) > len(ocr_data['amounts_apres']):
        resultat = True    
    elif fitz_data['codes'] and ocr_data['codes'] and len(fitz_data['codes']) > len(ocr_data['codes']):
        resultat = True
    else:
        resultat = False

    return resultat

def split_pdf_pages(pdf_path: str, output_dir: str) -> list:
    """
    Crée un dossier et enregistre chaque page du PDF comme un fichier PDF distinct.
    Retourne la liste des chemins des fichiers PDF extraits.
    """
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_document = fitz.open(pdf_path)
    extracted_files = []
    
    for page_num in range(pdf_document.page_count):
        output_pdf_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
        new_pdf = fitz.open()
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
        new_pdf.save(output_pdf_path)
        new_pdf.close()
        extracted_files.append(output_pdf_path)
    
    pdf_document.close()
    return extracted_files

def ajout_element(pdf_path: str):
    fitz_text = extract_text_with_fitz(pdf_path)

    images = pdf2img(pdf_path)

    ocr_text = "".join(img2text(image) for image in images)
    
    print("Extraction des dates et montants...")
    fitz_data, ocr_data = map(extract_dates_and_amounts, [" ".join(fitz_text), ocr_text])
    
    fraud_detected = detect_fraud(fitz_data, ocr_data)
    
    if fraud_detected:
        print("FRAUDE SUSPECTÉE !")
    else:
        print("Aucune fraude détectée.")
    
    return fraud_detected

