"""Arma la carpeta que se lleva al colegio, con el .exe adentro.

Requisitos (solo en la maquina donde compilas):
    pip install pyinstaller

Uso:
    python empaquetar.py

Resultado:
    dist/GeoGuessr-Competencia/        <- carpeta con el .exe
    dist/GeoGuessr-Competencia.zip

Se usa el modo CARPETA (--onedir) a proposito. El .exe de archivo unico se
auto-descomprime en memoria al arrancar, que es exactamente lo que hacen los
empaquetadores de malware, y los antivirus lo bloquean por heuristica aunque
este limpio. Esto ya paso con la version de un jugador: no cambiar a --onefile.
"""
import os
import shutil
import subprocess
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
NOMBRE = "GeoGuessr-Competencia"
DB = os.path.join(AQUI, "tiles.db")
DIST = os.path.join(AQUI, "dist")

LEEME = """GEOGUESSR SANTANDER - COMPETENCIA
=================================

PARA EL PROFESOR

1. Conecta el portatil a internet (la wifi del colegio o tus datos).
2. Doble clic en GeoGuessr-Competencia.exe
3. Espera unos 10 segundos: se abre una ventana negra y el navegador con
   el TABLERO.
4. Proyecta el tablero y ponlo en pantalla completa con F11.
5. Elige cuantas rondas y cuantos segundos en el menu de arriba.
6. Los estudiantes escanean el QR con la camara del celular, escriben su
   nombre y aparecen en la lista. Entran con datos moviles o con cualquier
   wifi; no tienen que estar en la misma red que tu.
7. Cuando esten todos, "Empezar competencia".

NO CIERRES la ventana negra mientras dure la competencia.

DURANTE LA PARTIDA
  - La X al lado de cada nombre saca a ese jugador (por si alguien se pone
    creativo con el nombre).
  - "Cerrar ronda ya" corta el tiempo si todos respondieron.

SI NO HAY INTERNET EN EL PORTATIL
  El programa avisa y sigue funcionando, pero ahi los celulares SI tienen
  que estar en el mismo wifi que el portatil.

IMPORTANTE
  Copia la carpeta COMPLETA. El .exe solo no sirve: al lado van los mapas,
  las librerias y cloudflared.

  La direccion del QR es distinta cada vez que abres el programa. Proyecta
  el QR en el momento; no sirve mandarlo antes por WhatsApp.

  Si Windows avisa "aplicacion desconocida" (SmartScreen), es porque el
  programa no esta firmado digitalmente:
    Mas informacion -> Ejecutar de todas formas

Mapas: satelite (c) Esri. Calles y nombres (c) colaboradores de OpenStreetMap.
Incluye cloudflared, de Cloudflare Inc., bajo licencia Apache 2.0.
"""


def main():
    if not os.path.exists(DB):
        sys.exit("Falta tiles.db. Ejecuta primero:  python descargar_mapas.py")

    sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", NOMBRE,
        "--add-data", f"{os.path.join(AQUI, 'web')}{sep}web",
        "--add-data", f"{DB}{sep}.",
        "--noconfirm", "--clean",
        os.path.join(AQUI, "servidor.py"),
    ]
    print(" ".join(cmd) + "\n")
    subprocess.check_call(cmd, cwd=AQUI)

    carpeta = os.path.join(DIST, NOMBRE)
    with open(os.path.join(carpeta, "LEEME.txt"), "w", encoding="utf-8") as fh:
        fh.write(LEEME)

    # cloudflared al lado del .exe: es lo que abre la direccion publica. Si no
    # viaja adentro, quien reciba el zip no tiene como conseguirlo (no tiene
    # Python para correr obtener_cloudflared.py) y se queda solo con red local.
    cf = shutil.which("cloudflared") or os.path.join(
        AQUI, "cloudflared.exe" if os.name == "nt" else "cloudflared")
    if cf and os.path.exists(cf):
        shutil.copy2(cf, os.path.join(carpeta, os.path.basename(cf)))
        print(f"  incluido cloudflared ({os.path.getsize(cf)/1e6:.0f} MB)")
    else:
        print("  AVISO: no encontre cloudflared, el paquete solo servira en red local.")
        print("         Consiguelo con: python obtener_cloudflared.py")

    zip_path = carpeta + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    print("\nComprimiendo...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for raiz, _, archivos in os.walk(carpeta):
            for a in archivos:
                completo = os.path.join(raiz, a)
                zf.write(completo, os.path.relpath(completo, DIST))

    total = sum(os.path.getsize(os.path.join(r, a))
                for r, _, ar in os.walk(carpeta) for a in ar)
    print(f"\nCarpeta: {carpeta}  ({total/1e6:.1f} MB)")
    print(f"Zip:     {zip_path}  ({os.path.getsize(zip_path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
