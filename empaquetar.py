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

1. Conecta el portatil al wifi del salon (NO hace falta internet).
2. Doble clic en GeoGuessr-Competencia.exe
3. Se abre una ventana negra y el navegador con el TABLERO.
4. Proyecta el tablero. Los estudiantes escanean el QR con la camara.
5. Cuando todos esten conectados, "Empezar competencia".

NO CIERRES la ventana negra mientras dure la competencia.

IMPORTANTE
  Copia la carpeta COMPLETA. El .exe solo no sirve: al lado van los mapas
  y las librerias, en _internal/.

  Los celulares tienen que estar en el MISMO WIFI que el portatil. Si el
  colegio tiene varias redes, todos en la misma. Si el QR no carga, en la
  ventana negra aparecen otras direcciones para probar.

  Si Windows avisa "aplicacion desconocida" (SmartScreen), es porque el
  programa no esta firmado digitalmente:
    Mas informacion -> Ejecutar de todas formas

Mapas: satelite (c) Esri. Calles y nombres (c) colaboradores de OpenStreetMap.
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
