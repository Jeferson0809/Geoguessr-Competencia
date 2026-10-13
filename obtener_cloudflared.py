"""Descarga cloudflared, el programa que arma el tunel. Se corre UNA vez.

    python obtener_cloudflared.py

Lo baja del repositorio oficial de Cloudflare en GitHub y lo deja al lado de
este archivo. No pide cuenta ni tarjeta.

Que es: un cliente que abre una conexion de salida hacia Cloudflare y les deja
reenviar el trafico de una URL publica hacia este portatil. No abre puertos en
el router ni cambia nada de la red; cuando se cierra el programa, la URL muere.
"""
import os
import platform
import stat
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download/"

ARCHIVOS = {
    ("Windows", "AMD64"): "cloudflared-windows-amd64.exe",
    ("Windows", "ARM64"): "cloudflared-windows-arm64.exe",
    ("Linux", "x86_64"): "cloudflared-linux-amd64",
    ("Linux", "aarch64"): "cloudflared-linux-arm64",
    ("Darwin", "x86_64"): "cloudflared-darwin-amd64.tgz",
    ("Darwin", "arm64"): "cloudflared-darwin-arm64.tgz",
}


def main():
    sistema = platform.system()
    arq = platform.machine()
    archivo = ARCHIVOS.get((sistema, arq))
    if not archivo:
        sys.exit(f"No tengo una descarga para {sistema}/{arq}.\n"
                 f"Bajalo a mano de https://github.com/cloudflare/cloudflared/releases "
                 f"y dejalo en:\n  {AQUI}")

    destino = os.path.join(AQUI, "cloudflared.exe" if sistema == "Windows" else "cloudflared")
    if os.path.exists(destino):
        print("Ya estaba:", destino)
        return

    url = BASE + archivo
    print("Bajando de:", url)
    if archivo.endswith(".tgz"):
        sys.exit("En macOS bajalo a mano (viene comprimido):\n  " + url)

    def progreso(bloques, tam, total):
        if total > 0:
            pct = min(100, bloques * tam * 100 // total)
            sys.stdout.write(f"\r  {pct}%   ")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, destino, progreso)
    print()
    if sistema != "Windows":
        os.chmod(destino, os.stat(destino).st_mode | stat.S_IEXEC)

    print(f"Listo: {destino}  ({os.path.getsize(destino)/1e6:.1f} MB)")
    print("\nAhora ya podes usar:  python servidor.py --tunel")


if __name__ == "__main__":
    main()
