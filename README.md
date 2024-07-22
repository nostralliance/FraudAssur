## api_document 
l'api document contient les endpoints /plusieurs_documents, /plusieurs_lien_fichiers

## api_2jsonV2
Cette api permet de requeter et de recevoir les requetes émanant de postman et seulement postman

pré-requis :
- mettre la méthode POST puis rentrez l'url
- dans le "Header" rentrez dans la première colonne Authorization puis dans value "Bearer apin@fraude.fr"
- se rendre ensuite dans l'onglet "Body" --> raw et saisir le json a envoyer a l'API sécurisée

## api_2jsonV3
Cette api permet de requeter avec postman ou une autre api et d'envoyer la réponse a l'api externe 

pré-requis :
- mettre la méthode POST puis rentrez l'url
- dans le "Header" rentrez dans la première colonne Authorization puis dans value "Bearer apin@fraude.fr"
- se rendre ensuite dans l'onglet "Body" --> raw et saisir le json a envoyer a l'API sécurisée

## fichier requirement.txt
J'ai ajouter a l'intérieur les librairies :
- pydantic pour les classe utilisateurs de la base de donnée
- requests pour requeter sur l'api externe
- hashlib et hmac pour hacher les mots de passes