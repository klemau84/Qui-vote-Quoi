
"""
Import des votes et amendements de l'Assemblée nationale.

Source officielle:
https://data.assemblee-nationale.fr/travaux-parlementaires
"""
from pathlib import Path
import requests

VOTES_PAGE = "https://data.assemblee-nationale.fr/travaux-parlementaires/votes"

def download(url: str, destination: Path) -> Path:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination

def run():
    raise RuntimeError(
        "Le téléchargement direct doit recevoir l'URL précise de la ressource XML "
        "publiée sur la page officielle. Le parseur sera ajouté après validation du format."
    )
