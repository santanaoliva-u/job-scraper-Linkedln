import aiohttp
import asyncio
from bs4 import BeautifulSoup
import orjson
from pathlib import Path
from datetime import datetime
import re
import logging
from fake_useragent import UserAgent
import shelve
from typing import AsyncGenerator, List, Dict
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(msg)s")

def parse_time(t: str | int) -> int:
    """Convierte '1 hora', '5 días', '1 semana' o segundos a segundos."""
    if isinstance(t, int):
        return t
    t = t.lower().strip()
    m = re.match(r"(\d+)\s*(hora|minuto|segundo|día|semana)s?(s)?", t)
    if not m:
        raise ValueError(f"Tiempo inválido: {t}")
    n, u = int(m.group(1)), m.group(2)
    return n * {"hora": 3600, "minuto": 60, "segundo": 1, "día": 86400, "semana": 604800}[u]

class Scraper:
    def __init__(s, cfg: dict):
        s.c = cfg
        s.ua = UserAgent()
        s.h = {"User-Agent": s.ua.random, "Accept-Language": "es-ES,es;q=0.9"}
        s.d = Path(cfg["out"])
        s.d.mkdir(exist_ok=True)
        try:
            s.fresh = parse_time(cfg["fresh"])
        except (KeyError, ValueError) as e:
            logging.error(f"Error en 'fresh': {e}")
            raise
        s.geo = cfg["geo"] if isinstance(cfg["geo"], list) else [cfg["geo"]]
        s.pages = cfg.get("max_pages", 1)
        s.cache = None
        try:
            s.cache = shelve.open(str(s.d / "cache.db"))
        except Exception as e:
            logging.error(f"Error iniciando caché: {e}")
            raise

    async def _get(s, ses: aiohttp.ClientSession, url: str, retries: int = 3) -> str:
        for i in range(retries):
            try:
                async with ses.get(url, headers={**s.h, "User-Agent": s.ua.random}, timeout=15) as r:
                    if r.status == 200:
                        return await r.text()
                    logging.error(f"Error {r.status} en {url}")
                    await asyncio.sleep(2 ** i)
            except Exception as e:
                logging.error(f"Error en {url}: {e}")
                await asyncio.sleep(2 ** i)
        logging.warning(f"Falló {url} tras {retries} intentos")
        return ""

    def _url(s, kw: str, geo: str, page: int = 0) -> str:
        p = {"keywords": kw, "geoId": geo, "f_TPR": f"r{s.fresh}", "start": page * 25}
        return f"https://www.linkedin.com/jobs/search/?{urlencode(p)}"

    async def _ext(s, html: str) -> AsyncGenerator[Dict, None]:
        if not html:
            logging.warning("HTML vacío")
            return
        sp = BeautifulSoup(html, "lxml")
        for c in sp.select("li.jobs-search-results-list__list-item"):
            try:
                t = c.select_one(".job-card-list__title") or ""
                cmp = c.select_one(".job-card-container__company-name") or ""
                lnk = c.select_one("a.job-card-container__link") or {"href": ""}
                jid = lnk["href"].split("?")[0]
                if jid not in s.cache:
                    s.cache[jid] = True
                    yield {
                        "t": t.text.strip() if t else "",
                        "c": cmp.text.strip() if cmp else "",
                        "l": lnk["href"] if lnk else "",
                        "ts": datetime.now().isoformat()
                    }
            except Exception as e:
                logging.warning(f"Error en tarjeta: {e}")

    async def _scr(s, ses: aiohttp.ClientSession, kw: str, geo: str) -> List[Dict]:
        jbs = []
        for p in range(s.pages):
            html = await s._get(ses, s._url(kw, geo, p))
            async for j in s._ext(html):
                jbs.append(j)
            if not html or len(jbs) >= 50:
                break
        return jbs

    async def run(s) -> List[Dict]:
        async with aiohttp.ClientSession() as ses:
            t = [s._scr(ses, k, g) for k in s.c["kw"] for g in s.geo]
            r = await asyncio.gather(*t, return_exceptions=True)
            jbs = [j for r in r if isinstance(r, list) for j in r]
            if jbs:
                s._save(jbs)
            else:
                logging.warning("No se encontraron empleos para ninguna palabra clave")
            return jbs

    def _save(s, jbs: List[Dict]):
        fn = s.d / f"jbs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fn, "wb") as f:
            f.write(orjson.dumps(jbs, option=orjson.OPT_INDENT_2))
        logging.info(f"Guardados {len(jbs)} empleos en {fn}")

    def __del__(s):
        if hasattr(s, "cache") and s.cache is not None:
            s.cache.close()
