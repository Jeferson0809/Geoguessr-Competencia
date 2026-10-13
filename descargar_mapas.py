"""Descarga los mapas a tiles.db. Se corre UNA vez, con internet.

Son dos capas distintas:

  sat   foto satelital de Esri alrededor de cada ubicacion -> la pista
  vt    mapa vectorial de OpenStreetMap del area metropolitana -> para marcar

El vectorial solo hay que bajarlo una vez; ocupa 5 MB para toda el area y
MapLibre lo reescala a cualquier zoom. El satelital hay que ampliarlo cada vez
que se agrega una ubicacion nueva, y este script baja solo lo que falte.

    python descargar_mapas.py

Nota: NO se usan los tiles de imagen de OpenStreetMap. Su politica prohibe la
descarga masiva y el servidor responde "Access blocked" con codigo 200, asi que
el tile malo se cuela como bueno. Los datos vectoriales de OSM si son libres de
empaquetar, y de ahi sale el mapa de la fase de marcar.
"""
import gzip
import math
import os
import sqlite3
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from pmtiles.tile import deserialize_header, deserialize_directory, find_tile, zxy_to_tileid

import juego

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "tiles.db")
UA = "Geoguessr-Competencia/1.0 (uso educativo; copia local de un area chica)"

SAT_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
SAT_ZOOMS = [16, 17, 18, 19]     # Esri no tiene z20 en Bucaramanga
SAT_RADIO_X, SAT_RADIO_Y = 3, 2

BBOX = (7.020, -73.230, 7.200, -73.040)
VT_ZOOM_MAX = 15
HILOS = 4


def deg2tile(lat, lon, z):
    n = 2 ** z
    return (int((lon + 180.0) / 360.0 * n),
            int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n))


def abrir_db():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("CREATE TABLE IF NOT EXISTS tiles ("
                " layer TEXT, z INTEGER, x INTEGER, y INTEGER, data BLOB,"
                " PRIMARY KEY (layer, z, x, y))")
    return con


# --- satelite ---------------------------------------------------------------
def bajar_satelite(con):
    faltan = set()
    for loc in juego.cargar_ubicaciones():
        for z in SAT_ZOOMS:
            cx, cy = deg2tile(loc["lat"], loc["lon"], z)
            for dx in range(-SAT_RADIO_X, SAT_RADIO_X + 1):
                for dy in range(-SAT_RADIO_Y, SAT_RADIO_Y + 1):
                    faltan.add((z, cx + dx, cy + dy))
    ya = {t for t in con.execute("SELECT z,x,y FROM tiles WHERE layer='sat'")}
    trabajos = sorted(faltan - ya)
    print(f"Satelite: {len(trabajos)} tiles por bajar ({len(ya)} ya estaban)")
    if not trabajos:
        return

    def uno(t):
        z, x, y = t
        req = urllib.request.Request(SAT_URL.format(z=z, x=x, y=y), headers={"User-Agent": UA})
        for intento in range(3):
            try:
                return t, urllib.request.urlopen(req, timeout=30).read()
            except Exception:
                if intento == 2:
                    return t, None
                time.sleep(1.5 * (intento + 1))

    buf, ok, fallos = [], 0, 0
    with ThreadPoolExecutor(max_workers=HILOS) as pool:
        for i, (t, datos) in enumerate(pool.map(uno, trabajos), 1):
            if datos:
                buf.append(("sat", t[0], t[1], t[2], datos)); ok += 1
            else:
                fallos += 1
            if len(buf) >= 200:
                con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
                con.commit(); buf.clear()
            if i % 100 == 0 or i == len(trabajos):
                sys.stdout.write(f"\r  {i}/{len(trabajos)}  fallidos={fallos}   ")
                sys.stdout.flush()
    if buf:
        con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
        con.commit()
    print()


# --- vectorial --------------------------------------------------------------
def url_planet():
    import datetime
    hoy = datetime.date.today()
    for i in range(14):
        d = (hoy - datetime.timedelta(days=i)).strftime("%Y%m%d")
        u = f"https://build.protomaps.com/{d}.pmtiles"
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Range": "bytes=0-6"})
            if urllib.request.urlopen(req, timeout=45).read() == b"PMTiles":
                return u
        except Exception:
            continue
    raise SystemExit("No encontre ningun build de Protomaps disponible.")


def bajar_vectorial(con):
    ya = {t for t in con.execute("SELECT z,x,y FROM tiles WHERE layer='vt'")}
    lat_min, lon_min, lat_max, lon_max = BBOX
    faltan = []
    for z in range(0, VT_ZOOM_MAX + 1):
        x0, y0 = deg2tile(lat_max, lon_min, z)
        x1, y1 = deg2tile(lat_min, lon_max, z)
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                if (z, x, y) not in ya:
                    faltan.append((z, x, y))
    print(f"Vectorial: {len(faltan)} tiles por bajar ({len(ya)} ya estaban)")
    if not faltan:
        return

    url = url_planet()
    print("  fuente:", url)
    cache = {}

    def leer(offset, length):
        clave = (offset, length)
        if clave in cache:
            return cache[clave]
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Range": f"bytes={offset}-{offset+length-1}"})
        for intento in range(4):
            try:
                datos = urllib.request.urlopen(req, timeout=90).read()
                break
            except Exception:
                if intento == 3:
                    raise
                time.sleep(2 * (intento + 1))
        if length < 4_000_000:
            cache[clave] = datos
        return datos

    header = deserialize_header(leer(0, 127))

    def tile_de(z, x, y):
        tid = zxy_to_tileid(z, x, y)
        off, largo = header["root_offset"], header["root_length"]
        for _ in range(4):
            r = find_tile(deserialize_directory(leer(off, largo)), tid)
            if not r:
                return None
            if r.run_length == 0:
                off, largo = header["leaf_directory_offset"] + r.offset, r.length
            else:
                return leer(header["tile_data_offset"] + r.offset, r.length)

    buf = []
    for i, (z, x, y) in enumerate(faltan, 1):
        d = tile_de(z, x, y)
        if d:
            buf.append(("vt", z, x, y, d))
        if len(buf) >= 50:
            con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
            con.commit(); buf.clear()
        if i % 20 == 0 or i == len(faltan):
            sys.stdout.write(f"\r  {i}/{len(faltan)}   ")
            sys.stdout.flush()
    if buf:
        con.executemany("INSERT OR REPLACE INTO tiles VALUES (?,?,?,?,?)", buf)
        con.commit()
    print()


def verificar(con):
    """Avisa si un servidor devolvio imagenes de relleno ('sin datos', bloqueos).

    Llegan con codigo 200 y pasarian por buenas; se detectan porque el mismo
    contenido exacto se repite muchas veces dentro de un mismo zoom.
    """
    import hashlib
    from collections import defaultdict
    grupos = defaultdict(lambda: defaultdict(int))
    for layer, z, data in con.execute("SELECT layer, z, data FROM tiles"):
        grupos[(layer, z)][hashlib.md5(data).hexdigest()] += 1
    malos = [f"  {l} z{z}: {max(h.values())}/{sum(h.values())} identicos"
             for (l, z), h in sorted(grupos.items())
             if sum(h.values()) >= 20 and max(h.values()) > sum(h.values()) * 0.5]
    if malos:
        print("\nAVISO: parece que hay tiles de relleno en:")
        print("\n".join(malos))
    else:
        print("Verificacion: todos los zooms traen imagenes reales.")


def main():
    con = abrir_db()
    bajar_satelite(con)
    bajar_vectorial(con)
    verificar(con)
    for layer, n, mb in con.execute(
            "SELECT layer, COUNT(*), ROUND(SUM(LENGTH(data))/1e6,1) FROM tiles GROUP BY layer"):
        print(f"  {layer}: {n} tiles, {mb} MB")
    con.execute("VACUUM")
    con.close()
    print(f"tiles.db = {os.path.getsize(DB)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
