"""Mete jugadores falsos a una partida, para probar sin tener 30 celulares.

Sirve para ver como se siente el tablero lleno: cuantos responden rapido,
como se mueve la tabla, si 60 segundos sobran o faltan. Vos entras con tu
celular de verdad y compites contra ellos.

    # en una ventana
    python servidor.py --tunel

    # en otra ventana, con el codigo que aparece en la URL del tablero
    python simular_jugadores.py 8 --token AbCdEfGh

Los falsos no hacen trampa en el sentido de ver la respuesta antes: usan la
misma pista que ve el tablero y le suman un error al azar, como un estudiante
que ubica mas o menos. Unos responden casi de una, otros se demoran, y alguno
no responde nunca, que tambien pasa.
"""
import argparse
import json
import math
import random
import sys
import threading
import time
import urllib.error
import urllib.request

NOMBRES = [
    "Valentina", "Santiago", "Mariana", "Sebastián", "Isabella", "Samuel",
    "Camila", "Nicolás", "Sofía", "Andrés", "Luciana", "Tomás",
    "Gabriela", "Emiliano", "Daniela", "Matías", "Antonella", "Julián",
    "Salomé", "Alejandro", "Manuela", "Felipe", "Juanita", "Martín",
]

# Que tan bueno es cada perfil ubicando, en km de error tipico, y cuanto se
# demora en decidirse, como fraccion de la ronda.
PERFILES = [
    ("crack",    0.3,  (0.05, 0.25)),
    ("bueno",    1.2,  (0.15, 0.45)),
    ("normal",   3.0,  (0.25, 0.70)),
    ("perdido",  7.0,  (0.40, 0.95)),
]
PESOS = [1, 3, 4, 2]


_aviso_dado = threading.Event()


def avisar_token_viejo():
    """Una sola vez, aunque los diez falsos lo detecten a la vez."""
    if not _aviso_dado.is_set():
        _aviso_dado.set()
        print()
        print("  El codigo del tablero cambio (reiniciaste el servidor).")
        print("  Los falsos siguen en la sala pero no van a responder.")
        print("  Corta esto (Ctrl+C) y relanzalo con el codigo nuevo.")
        print()


def pedir(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)


def enviar(url, datos):
    req = urllib.request.Request(url, data=json.dumps(datos).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def desplazar(lat, lon, km, rumbo_rad):
    """Mueve un punto km kilometros en una direccion."""
    dlat = (km * math.cos(rumbo_rad)) / 110.574
    dlon = (km * math.sin(rumbo_rad)) / (111.320 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


class Falso(threading.Thread):
    daemon = True

    def __init__(self, base, token, nombre):
        super().__init__()
        self.base, self.token, self.nombre = base, token, nombre
        perfil, self.error_km, self.rango = random.choices(PERFILES, PESOS)[0]
        self.perfil = perfil
        self.id = None
        self.ronda_hecha = None

    def entrar(self):
        r = enviar(self.base + "/api/unirse", {"nombre": self.nombre})
        self.id = r["id"]
        self.nombre = r["nombre"]

    def run(self):
        while True:
            try:
                est = pedir(f"{self.base}/api/jugador?id={self.id}")
                # Si reiniciaron la partida desde el tablero, el servidor ya no
                # nos conoce. Volvemos a entrar solos: probando uno se reinicia
                # muchas veces y no da tener que relanzar esto cada vez.
                if not est["unido"]:
                    self.entrar()
                    self.ronda_hecha = None
                elif est["fase"] == "ronda" and self.ronda_hecha != est["ronda"]:
                    self.jugar(est)
            except Exception:
                pass
            time.sleep(1)

    def jugar(self, est):
        self.ronda_hecha = est["ronda"]
        # 1 de cada 12 se queda mirando el techo y no responde
        if random.random() < 1 / 12:
            return
        espera = random.uniform(*self.rango) * est["segundos_ronda"]
        time.sleep(min(espera, max(0.0, est["restante"] - 0.5)))
        try:
            # La pista es la respuesta exacta, asi que solo la da el tablero.
            # Si reiniciaste el servidor, el codigo cambio y hay que relanzar
            # esto con el nuevo; sin eso los falsos entran pero nunca responden.
            try:
                h = pedir(f"{self.base}/api/host?token={self.token}")
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    avisar_token_viejo()
                return
            if h.get("fase") != "ronda" or not h.get("pista"):
                return
            km = abs(random.gauss(0, self.error_km)) + random.uniform(0, 0.1)
            lat, lon = desplazar(h["pista"]["lat"], h["pista"]["lon"], km,
                                 random.uniform(0, 2 * math.pi))
            enviar(self.base + "/api/responder", {"id": self.id, "lat": lat, "lon": lon})
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="Jugadores falsos para probar la competencia")
    ap.add_argument("cantidad", type=int, nargs="?", default=8)
    ap.add_argument("--url", default="http://127.0.0.1:8000",
                    help="direccion del servidor (por defecto, el de esta maquina)")
    ap.add_argument("--token", required=True,
                    help="el codigo que aparece en la URL del tablero, despues de /host/")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    try:
        pedir(f"{base}/api/host?token={args.token}")
    except Exception as e:
        sys.exit(f"No pude hablar con el tablero ({e}).\n"
                 f"Revisa que el servidor este corriendo y que el codigo sea el correcto.")

    nombres = random.sample(NOMBRES, min(args.cantidad, len(NOMBRES)))
    falsos = []
    for n in nombres:
        f = Falso(base, args.token, n)
        try:
            f.entrar()
        except Exception as e:
            sys.exit(f"No pude meter a {n}: {e}\n"
                     "Si la partida ya empezo, reiniciala desde el tablero.")
        falsos.append(f)
        f.start()
        print(f"  entro {f.nombre:<12} ({f.perfil})")

    print(f"\n{len(falsos)} jugadores falsos listos. Entra con tu celular y empieza "
          f"la competencia desde el tablero.")
    print("Ctrl+C para sacarlos.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListo.")


if __name__ == "__main__":
    main()
