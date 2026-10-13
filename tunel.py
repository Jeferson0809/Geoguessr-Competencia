"""Publica el servidor local en una URL de internet, usando cloudflared.

Para que sirve: si los estudiantes estan con datos moviles (o en una wifi
distinta a la del profesor), no pueden alcanzar la IP privada del portatil.
Un tunel le da al mismo servidor una direccion publica temporal, y por ahi
entra cualquiera desde donde sea.

El portatil sigue siendo el servidor y los mapas siguen saliendo de tiles.db:
lo unico que cambia es por donde llegan los celulares.

Requiere cloudflared, que NO viene incluido. Se consigue con:

    python obtener_cloudflared.py

No necesita cuenta ni tarjeta: los "quick tunnels" de Cloudflare son anonimos
y la URL es distinta en cada arranque (dura lo que dure la partida).
"""
import os
import re
import shutil
import subprocess
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
PATRON_URL = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

# Sirve para probar el arranque sin bajar el binario real (ver pruebas_tunel.py)
EJECUTABLE_DE_PRUEBA = os.environ.get("CLOUDFLARED_FALSO")


def buscar_ejecutable():
    """cloudflared en el PATH, al lado del programa, o en ./bin."""
    if EJECUTABLE_DE_PRUEBA:
        return EJECUTABLE_DE_PRUEBA
    nombre = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    candidatos = [
        shutil.which("cloudflared"),
        os.path.join(AQUI, nombre),
        os.path.join(AQUI, "bin", nombre),
        os.path.join(os.path.dirname(sys.executable), nombre),
    ]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    return None


class Tunel:
    def __init__(self, puerto):
        self.puerto = puerto
        self.proceso = None
        self.url = None
        self._lineas = []

    def abrir(self, espera=40):
        """Lanza cloudflared y espera a que anuncie la URL. None si no se pudo."""
        exe = buscar_ejecutable()
        if not exe:
            return None

        cmd = [exe, "tunnel", "--url", f"http://127.0.0.1:{self.puerto}", "--no-autoupdate"]
        if EJECUTABLE_DE_PRUEBA:
            cmd = [sys.executable, exe, str(self.puerto)]

        self.proceso = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )

        def leer():
            # cloudflared anuncia la URL en un recuadro, por stderr. Se mezclan
            # las dos salidas y se busca el patron en cualquiera.
            for linea in self.proceso.stdout:
                self._lineas.append(linea.rstrip())
                m = PATRON_URL.search(linea)
                if m and not self.url:
                    self.url = m.group(0)

        threading.Thread(target=leer, daemon=True).start()

        limite = time.time() + espera
        while time.time() < limite:
            if self.url:
                return self.url
            if self.proceso.poll() is not None:
                return None
            time.sleep(0.3)
        return None

    def cerrar(self):
        if self.proceso and self.proceso.poll() is None:
            self.proceso.terminate()
            try:
                self.proceso.wait(timeout=5)
            except Exception:
                self.proceso.kill()

    def diagnostico(self):
        return "\n".join(self._lineas[-12:]) or "(cloudflared no escribió nada)"


AYUDA_SIN_CLOUDFLARED = """
  No encontre cloudflared, que es lo que hace el tunel.

  Consiguelo una sola vez con:
      python obtener_cloudflared.py

  Mientras tanto el juego sigue funcionando en modo red local: sirve si los
  celulares estan en el MISMO wifi que este portatil.
"""
