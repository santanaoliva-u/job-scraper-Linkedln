import re
from typing import List, Dict

def flt(jobs: List[Dict], keywords: List[str] = None, min_score: float = 0.7) -> List[Dict]:
    """Filtra empleos por relevancia en título."""
    if keywords is None:
        keywords = ["dev", "ingeniero", "ciberseguridad", "python"]
    def score(title: str) -> float:
        title = title.lower()
        return sum(1 for k in keywords if re.search(rf"\b{k}\b", title, re.IGNORECASE)) / len(keywords)
    return [job for job in jobs if score(job["t"]) >= min_score]
