from datetime import timedelta
import os

def format_time(seconds):
    """Convertit des secondes en format hh:mm:ss"""
    return str(timedelta(seconds=int(seconds)))

async def save_file_async(file, folder):
    """
    Sauvegarde un fichier UploadFile (FastAPI) dans le dossier donné.
    Crée le dossier s'il n'existe pas.
    Retourne le chemin complet du fichier sauvegardé.
    """
    os.makedirs(folder, exist_ok=True)
    # Pour éviter les problèmes de nom de fichier (espaces, caractères spéciaux), on peut nettoyer le nom :
    filename = os.path.basename(file.filename)
    path = os.path.join(folder, filename)

    # Ecriture asynchrone
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)

    return path
