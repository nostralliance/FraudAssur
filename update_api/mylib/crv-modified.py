import re 
import pandas as pd
from . import constants,paths
from datetime import date
from jours_feries_france import JoursFeries
from dateutil.relativedelta import relativedelta


def dateferiee(pngText):
    # condition pour exclure les cartes TP
    #pattern= r'[D|d][U|u] 01/01/(\d{4}) [A|a][u|U] (\d{2})/(\d{2})/(\d{4})'
    
    #regex_devis = r'([Dd][Ee][Vv][Ii][Ss]\ [Pp][Oo][Uu][Rr]\ [Ll][Ee][Ss]\ [Tt][Rr][Aa][Ii][Tt][Ee][Mm][Ee][Nn][Tt][Ss]\ [Ee][Tt]\ [Aa][Cc][Tt][Ee][Ss]\ [Bb][Uu][Cc][Cc][Oo]\-[Dd][Ee][Nn][Tt][Aa][Ii][Rr][Ee][Ss]|[Aa][Mm][Cc]|[Ee][Ff][Ff][Ee][Tt])'
    #dateListCarteTP = re.findall(pattern, pngText)
    pattern = r"[D|d][U|u]? ?(\d{2})/(\d{2})/(\d{4}) [0|A|a][u|U]? (\d{2})/(\d{2})/(\d{4})|[vV][aA][lL][aA][bB][lL][eE] ?[Jj][uU][sS][qQ][uU]'?[aA][uU] ?:? ?(\d{2})/(\d{2})/(\d{4})"
    regex_devis = r'([Dd][Ee][Vv][Ii][Ss]|[Aa][Mm][Cc]|[Ee][Ff][Ff][Ee][Tt])'
    dateListCarteTP = re.findall(pattern, pngText)
    dateListBucco = re.findall(regex_devis, str(pngText))
    
    result = False
    if len(dateListCarteTP)==0 and len(dateListBucco)==0:
        # On récupère la liste des dates dans le texte
        dateList = re.findall(r'([0-3]{1}[0-9]{1})[/-](1[0-2]{1}|0[1-9]{1})[/-]([0-9]{2,4})', pngText)
        dateList = list(dict.fromkeys(dateList))
        # On récupère la liste des indices sur Alsace-Moselle dans le texte
        cpList = re.findall(r'[5-6]7\d{3}', pngText)
        cityList = re.findall(r'[a|A]lsace|[m|M]oselle', pngText)

        # On initialise le résultat
        

        for dateSplit in dateList :
            dateFormat = date(int(dateSplit[2]), int(dateSplit[1]), int(dateSplit[0]))

            # Si la date est inférieure à la durée maximale de remboursement,        
            if relativedelta(date.today(), dateFormat).years < constants.MAX_REFUND_YEARS and relativedelta(date.today(), dateFormat).years >= 0:

                # Si on est en Alsace-Moselle
                if len(cpList) > 0 or len(cityList) > 0 :
                    if JoursFeries.is_bank_holiday(dateFormat, zone="Alsace-Moselle") :
                        result = True
                        break
                else :
                    # Si c'est un jour férié en Métropole, on suspecte une fraude
                    if JoursFeries.is_bank_holiday(dateFormat, zone="Métropole") :
                        result = True
                        break
        
    return result

def rononsoumis(pngText):
    # On récupère les indices relatifs au régime obligatoire
    regimeList = re.findall(r'[r|R][é|e]gime [o|O]bligatoire|[R|r][O|o]|REGIME OBLIGATOIRE', pngText)
    print(regimeList)
    # On recherche les indices relatifs aux prestations non soumis au Régime obligatoire
    sansRoList = re.findall("|".join(constants.NONRO_PRESTA), pngText)

    if "" in sansRoList:
        sansRoList=[]
    
    print(sansRoList)

    # Si l'on trouve
    if len(regimeList) > 0 and len(sansRoList) > 0 :
        return True
    else :
        return False
    

def finessfaux(society, pngText):
    # On récupère la liste des Numéros finess des adhérents suspects
    data = pd.read_excel(str(paths.rootPath) + '/' + society +'/depot/TMP/data/surveillance.xlsx', sheet_name="finess")
    finessList = data["NUMERO FINESS"].tolist()
    print(finessList)
    print("|".join(str(s) for s in finessList))
    # On recherche les indices relatifs à la présence d'un numéro finess dans la page
    resultList = re.findall(r"|".join(str(s) for s in finessList), pngText)
    
    print(resultList)
    if len(resultList) > 0 :
        return True
    else :
         return False



def adherentssuspicieux(society, pngText):
    # On récupère la liste des noms des adhérents suspects
    data = pd.read_excel(str(paths.rootPath) + '/' + society +'/depot/TMP/data/surveillance.xlsx', sheet_name="Adhérents")
    usersList = data["NOM Complet"].tolist()
    print(usersList)
    resultList = re.findall("|".join(usersList).upper(), pngText.upper())
    print(resultList)

    if len(resultList) > 0 :
        return True
    else :
         return False


def refarchivesfaux(pngText):
    #recherche de mots indiquant que c'est un decompte
    rechmot= re.findall(r'CPAM|ensemble|Agir', pngText)
    print(rechmot)
    if len(rechmot)>1:
        refList = re.findall(r'\d{4}[ ]?[  ]?[   ]?(\d{2})(\d{3})\d{8}', pngText)
        print(refList)
        # On récupère la liste des dates dans le texte
        dateList = re.findall(r'([0-3]{1}[0-9]{1})[/-](1[0-2]{1}|0[1-9]{1})[/-]([0-9]{2,4})', pngText)
        print(dateList)
        if not dateList:
            return False
        else:
            dateList = list(dict.fromkeys(dateList))
            print(dateList)
            # Pour chaque référence d'archivage, on vérifie qu'il y a au moins une date qui correspond à cette référence d'archivage
            for refSplit in refList :
                print(refSplit)
                currentResult = False
                # Pour chaque date récupérée
                for dateSplit in dateList :
                    dateFormat = date(int(dateSplit[2]), int(dateSplit[1]), int(dateSplit[0]))
                    print(dateFormat)
                    dateCompare = date(int(dateSplit[2]), 1, 1)
                    dateDelta = dateFormat - dateCompare
                    print(dateCompare)
                    print(dateDelta.days)
                    # On vérifie que l'année correspond
                    if dateSplit[2][-2:] == refSplit[0] :
                        # On vérifie que le nombre de jour correspond
                        if int(refSplit[1]) - constants.REF_AGE_DELTA <= int(dateDelta.days) <= int(refSplit[1]) + constants.REF_AGE_DELTA  :
                            currentResult = True
                            break
                
                if currentResult == False :
                    print("------Une fausse référence d'archivage à été trouvée !")
                    return True 
                
            return False
    else:
        return False
