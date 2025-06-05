import asyncio
import orjson
from pathlib import Path
from utils.scraper import Scraper, parse_time
from utils.filters import flt
from utils.telegram import snd, get_chat_id
from rich.console import Console
from rich.prompt import Prompt
import logging
import daemon
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

c = Console()

def logo():
    c.print("""
[bold cyan]
     ____  _          ____                                 
    | __ )| |__   ___| __ ) _ __ ___  ___ ___  ___  _ __  
    |  _ \\| '_ \\ / __|  _ \\| '__/ _ \\ \\ __/ __|/ _ \\| '_ \\ 
    | |_) | | | | (__| |_) | | |  __/\\__ \\__ \\ (_) | | | |
    |____/|_| |_|\\___|____/|_|  \\___||___/___/ \\___/|_| |_|[/]
[bold magenta]Scraper de Empleos LinkedIn por @santana[/]
[italic dim]GitHub: @santanaoliva_u | v2.3[/]
    """)

def load_cfg() -> dict:
    cfg_p = Path("config.json")
    if not cfg_p.exists():
        c.print("[bold red]¡Error! config.json no encontrado.[/]")
        sys.exit(1)
    with cfg_p.open("rb") as f:
        cfg = orjson.loads(f.read())
    required_keys = ["kw", "geo", "fresh", "loop_secs", "out"]
    missing = [k for k in required_keys if k not in cfg]
    if missing:
        c.print(f"[bold red]Error: Faltan claves en config.json: {missing}[/]")
        sys.exit(1)
    try:
        cfg["fresh"] = parse_time(cfg["fresh"])
        cfg["loop_secs"] = parse_time(cfg["loop_secs"])
    except ValueError as e:
        c.print(f"[bold red]Error en config.json: {e}[/]")
        sys.exit(1)
    return cfg

async def run_once(scraper: Scraper, cfg: dict):
    jbs = await scraper.run()
    fjbs = flt(jbs)
    if fjbs and cfg.get("tg_token") and cfg.get("tg_chat"):
        await snd(cfg["tg_token"], cfg["tg_chat"], fjbs)
    c.print(f"[bold green]Encontrados {len(fjbs)} empleos relevantes.[/]")

async def run_loop(scraper: Scraper, cfg: dict, secs: int):
    while True:
        try:
            jbs = await scraper.run()
            fjbs = flt(jbs)
            if fjbs and cfg.get("tg_token") and cfg.get("tg_chat"):
                await snd(cfg["tg_token"],["tg_chat"], fjbs)
            c.print(f"[bold green]Ciclo completado: {len(fjbs)} empleos.[/]")
            await asyncio.sleep(secs)
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
            await asyncio.sleep(secs)

async def main():
    logo()
    cfg = load_cfg()
    scraper = Scraper(cfg)  # Crear una sola instancia
    c.print("[bold yellow]📋 Menú Principal[/]")
    c.print("[1] Ejecutar una vez")
    c.print("[2] Ejecutar en bucle (cada {}s)".format(cfg["loop_secs"]))
    c.print("[3] Ejecutar en segundo plano")
    c.print("[4] Obtener chat_id de Telegram")
    c.print("[5] Salir")
    
    opt = Prompt.ask("[bold cyan]Selecciona una opción[/]", choices=["1", "2", "3", "4", "5"], default="1")
    
    try:
        if opt == "1":
            await run_once(scraper, cfg)
        elif opt == "2":
            await run_loop(scraper, cfg, cfg["loop_secs"])
        elif opt == "3":
            with daemon.DaemonContext():
                await run_loop(scraper, cfg, cfg["loop_secs"])
        elif opt == "4":
            if cfg.get("tg_token"):
                await get_chat_id(cfg["tg_token"])
            else:
                c.print("[bold red]Error: tg_token no configurado en config.json.[/]")
        else:
            c.print("[bold red]Saliendo...[/]")
            sys.exit(0)
    except Exception as e:
        c.print(f"[bold red]Error inesperado: {e}[/]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
