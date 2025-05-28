import re
from typing import List, Dict

def flt(jbs: List[Dict], min_s: float = 0.7) -> List[Dict]:
    """Filtra empleos por relevancia en título."""
    kws = ["dev", "ingeniero", "ciberseguridad", "python"]
    def scr(t: str) -> float:
        t = t.lower()
        return sum(1 for k in kws if re.search(rf"\b{k}\b", t, re.IGNORECASE)) / len(kws)
    return [j for j in jbs if scr(j["t"]) >= min_s]
