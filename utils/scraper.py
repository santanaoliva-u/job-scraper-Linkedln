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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.ua = UserAgent()
        self.headers = {"User-Agent": self.ua.random, "Accept-Language": "es-ES,es;q=0.9"}
        self.out_dir = Path(cfg["out"])
        self.out_dir.mkdir(exist_ok=True)
        self.debug_dir = self.out_dir / "debug"
        self.debug_dir.mkdir(exist_ok=True)
        try:
            self.fresh = parse_time(cfg["fresh"])
        except (KeyError, ValueError) as e:
            logging.error(f"Error en 'fresh': {e}")
            raise
        self.geo = cfg["geo"] if isinstance(cfg["geo"], list) else [cfg["geo"]]
        self.pages = cfg.get("max_pages", 1)
        self.proxy = cfg.get("proxy")
        self.cache = None
        try:
            self.cache = shelve.open(str(self.out_dir / "cache.db"))
        except Exception as e:
            logging.error(f"Error iniciando caché: {e}")
            raise
        self.sem = asyncio.Semaphore(3)  # Aumentado a 3 solicitudes simultáneas

    async def _get(self, ses: aiohttp.ClientSession, url: str, retries: int = 3) -> str:
        async with self.sem:
            for i in range(retries):
                try:
                    async with ses.get(url, headers={**self.headers, "User-Agent": self.ua.random}, timeout=15, proxy=self.proxy) as r:
                        if r.status == 200:
                            return await r.text()
                        elif r.status == 429:
                            logging.warning(f"Rate limit (429) en {url}, espera {8 * 2 ** i}s")
                            await asyncio.sleep(8 * 2 ** i)
                        else:
                            logging.error(f"Error {r.status} en {url}")
                            await asyncio.sleep(2 ** i)
                except Exception as e:
                    logging.error(f"Error en {url}: {e}")
                    await asyncio.sleep(2 ** i)
            logging.warning(f"Falló {url} tras {retries} intentos")
            return ""

    def _url(self, kw: str, geo: str, page: int = 0) -> str:
        params = {"keywords": kw, "geoId": geo, "f_TPR": f"r{self.fresh}", "start": page * 25}
        return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"

    async def _ext(self, html: str, url: str) -> AsyncGenerator[Dict, None]:
        if not html:
            logging.warning(f"HTML vacío para {url}")
            self._save_debug(html, url)
            return
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select("li.jobs-search-results__list-item")  # Selector más específico
        if not cards:
            logging.warning(f"No se encontraron tarjetas para {url}")
            self._save_debug(html, url)
        for card in cards:
            try:
                title = card.select_one(".job-card-list__title") or ""
                company = card.select_one(".job-card-container__company-name") or ""
                link = card.select_one("a.job-card-list__title[href*='/jobs/view/']") or {"href": ""}
                job_id = link["href"].split("?")[0]
                if job_id not in self.cache:
                    self.cache[job_id] = True
                    yield {
                        "t": title.text.strip() if title else "",
                        "c": company.text.strip() if company else "",
                        "l": link["href"] if link else "",
                        "ts": datetime.now().isoformat()
                    }
            except Exception as e:
                logging.warning(f"Error en tarjeta para {url}: {e}")
        await asyncio.sleep(0.5)

    def _save_debug(self, html: str, url: str):
        filename = self.debug_dir / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html or "<empty>")
        logging.info(f"HTML guardado en {filename} para depuración")

    async def _scr(self, ses: aiohttp.ClientSession, kw: str, geo: str) -> List[Dict]:
        jobs = []
        for page in range(self.pages):
            url = self._url(kw, geo, page)
            logging.info(f"Scrapeando {url}")
            html = await self._get(ses, url)
            async for job in self._ext(html, url):
                jobs.append(job)
            if not html or len(jobs) >= 50:
                logging.info(f"Parando en página {page + 1}: {'HTML vacío' if not html else 'límite alcanzado'}")
                break
            await asyncio.sleep(2)
        return jobs

    async def run(self) -> List[Dict]:
        async with aiohttp.ClientSession() as ses:
            tasks = [self._scr(ses, k, g) for k in self.cfg["kw"] for g in self.geo]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            jobs = [job for result in results if isinstance(result, list) for job in result]
            if jobs:
                self._save(jobs)
            else:
                logging.warning("No se encontraron empleos para ninguna palabra clave")
            return jobs

    def _save(self, jobs: List[Dict]):
        filename = self.out_dir / f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "wb") as f:
            f.write(orjson.dumps(jobs, option=orjson.OPT_INDENT_2))
        logging.info(f"Guardados {len(jobs)} empleos en {filename}")

    def __del__(self):
        if hasattr(self, "cache") and self.cache is not None:
            try:
                self.cache.close()
            except Exception as e:
                logging.error(f"Error cerrando caché: {e}")
