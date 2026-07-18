
"""
Import des scrutins publics du Sénat.
Les pages officielles contiennent résultats globaux et analyse par groupes.
"""
import re
import requests
from bs4 import BeautifulSoup

def parse_scrutin(url: str) -> dict:
    html = requests.get(url, timeout=60).text
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.stripped_strings)
    def number(label):
        match = re.search(rf"{label}\s*:?\s*(\d+)", text, re.I)
        return int(match.group(1)) if match else None
    return {
        "url": url,
        "votants": number("votants"),
        "exprimes": number("suffrages exprimés"),
        "pour": number("pour"),
        "contre": number("contre"),
        "abstention": number("abstention"),
    }
