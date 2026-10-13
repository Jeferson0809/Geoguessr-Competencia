"""Prueba el modo tunel SIN descargar cloudflared.

Usa un cloudflared de mentira que imita la salida del real: el recuadro con la
URL que imprime por stderr. Asi se verifica lo que de verdad puede fallar -- que
lo lancemos bien, que leamos su salida y que saquemos la URL -- sin depender de
tener el binario ni de abrir nada hacia internet.

    python pruebas_tunel.py
"""
import os
import sys
import textwrap

AQUI = os.path.dirname(os.path.abspath(__file__))
FALSO = os.path.join(AQUI, "_cloudflared_falso.py")

# Imita la salida real de `cloudflared tunnel --url ...`
GUION = textwrap.dedent('''
    import sys, time
    print("2026-10-13T18:00:00Z INF Thank you for trying Cloudflare Tunnel.", file=sys.stderr)
    print("2026-10-13T18:00:00Z INF Requesting new quick Tunnel...", file=sys.stderr)
    time.sleep(0.4)
    print("+----------------------------------------------------------+", file=sys.stderr)
    print("|  Your quick Tunnel has been created! Visit it at:         |", file=sys.stderr)
    print("|  https://pruebas-geoguessr-salon.trycloudflare.com        |", file=sys.stderr)
    print("+----------------------------------------------------------+", file=sys.stderr)
    sys.stderr.flush()
    time.sleep(30)
''')

with open(FALSO, "w", encoding="utf-8") as fh:
    fh.write(GUION)
os.environ["CLOUDFLARED_FALSO"] = FALSO

import tunel  # noqa: E402  (despues de poner la variable de entorno)

print("1) encuentra el ejecutable")
assert tunel.buscar_ejecutable() == FALSO
print("   ok")

print("2) abre el tunel y saca la URL de la salida")
t = tunel.Tunel(8000)
url = t.abrir(espera=15)
assert url == "https://pruebas-geoguessr-salon.trycloudflare.com", f"llego {url!r}"
print("   ok:", url)

print("3) al cerrar, el proceso muere (si no, la URL seguiria publicada)")
t.cerrar()
assert t.proceso.poll() is not None
print("   ok")

print("4) si cloudflared no esta, devuelve None y no revienta")
os.environ.pop("CLOUDFLARED_FALSO")
tunel.EJECUTABLE_DE_PRUEBA = None
import shutil
real = shutil.which("cloudflared")
if real:
    print("   (salteada: hay un cloudflared de verdad instalado)")
else:
    t2 = tunel.Tunel(8000)
    assert t2.abrir(espera=2) is None
    assert tunel.buscar_ejecutable() is None
    print("   ok")

os.remove(FALSO)
print("\nTODAS LAS PRUEBAS DEL TUNEL PASARON")
