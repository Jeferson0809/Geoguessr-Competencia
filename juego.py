"""Logica de la competencia: jugadores, rondas, puntajes.

Va separada del servidor a proposito: asi se puede probar sin levantar nada ni
abrir un navegador (ver pruebas.py).

El estado vive en memoria. Es una partida de 20 minutos en un salon, no hace
falta base de datos; si se cae el servidor se vuelve a empezar y ya.
"""
import json
import math
import os
import random
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))

# --- parametros de la competencia -------------------------------------------
SEGUNDOS_POR_RONDA = 60
RONDAS_POR_PARTIDA = 5
MAX_PUNTOS = 1000

# Puntaje por distancia: mismo criterio que la version de un jugador. Hasta
# TOLERANCIA_KM son todos los puntos (si le diste al edificio no hace falta el
# pixel exacto); de ahi cae exponencial, que es lo unico que reparte bien los
# puntos en una ciudad de 15 km.
TOLERANCIA_KM = 0.15
ESCALA_KM = 4.0

# Factor por rapidez, estilo Kahoot: responder de una vale el doble que
# responder sobre la chicharra. Nunca baja de la mitad, para que el que piensa
# despacio pero ubica bien no quede humillado.
FACTOR_MINIMO = 0.5


def distancia_km(a, b):
    """a y b son (lat, lon)."""
    R = 6371.0088
    r = math.radians
    dlat, dlon = r(b[0] - a[0]), r(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def puntos_por_distancia(d_km):
    exceso = max(0.0, d_km - TOLERANCIA_KM)
    return MAX_PUNTOS * math.exp(-exceso / ESCALA_KM)


def factor_rapidez(segundos_usados, segundos_ronda):
    usado = min(max(segundos_usados, 0.0), segundos_ronda)
    return 1.0 - (1.0 - FACTOR_MINIMO) * (usado / segundos_ronda)


def calcular_puntaje(d_km, segundos_usados, segundos_ronda):
    return int(round(puntos_por_distancia(d_km) * factor_rapidez(segundos_usados, segundos_ronda)))


def veredicto(d_km):
    """(emoji, frase, color) segun que tan cerca estuvo."""
    if d_km <= TOLERANCIA_KM:
        return "🎯", "¡En el blanco!", "#32CD32"
    if d_km <= 0.5:
        return "🔥", "Muy cerca", "#5BD75B"
    if d_km <= 1.5:
        return "👍", "Cerca", "#4DA3FF"
    if d_km <= 4:
        return "🙂", "Te faltó", "#FFC107"
    return "😅", "Lejos", "#FF7043"


def cargar_ubicaciones():
    """locations.js es 'const LOCATIONS_DATA = {...};' -> se saca el JSON."""
    ruta = os.path.join(AQUI, "web", "locations.js")
    with open(ruta, encoding="utf-8") as fh:
        crudo = fh.read()
    crudo = crudo.split("=", 1)[1].rsplit(";", 1)[0]
    return json.loads(crudo)["locations"]


class Partida:
    """Una competencia. Toda interaccion pasa por aca, con un lock.

    Fases:
      lobby      -> los jugadores se van uniendo
      ronda      -> contador corriendo, se reciben respuestas
      resultados -> se muestra donde era y la tabla
      final      -> podio
    """

    def __init__(self, segundos_por_ronda=SEGUNDOS_POR_RONDA, rondas=RONDAS_POR_PARTIDA):
        self.lock = threading.RLock()
        self.segundos_por_ronda = segundos_por_ronda
        self.rondas_totales = rondas
        self.ubicaciones = cargar_ubicaciones()
        self.reiniciar()

    # -- helpers internos (asumen lock tomado) -------------------------------
    def _tocar(self):
        """Sube la version. El front sondea y se entera de que algo cambio."""
        self.version += 1

    def _orden_ubicaciones(self):
        fijas = [u for u in self.ubicaciones if u.get("pinned")]
        resto = [u for u in self.ubicaciones if not u.get("pinned")]
        random.shuffle(resto)
        return (fijas + resto)[: self.rondas_totales]

    # -- ciclo de vida -------------------------------------------------------
    def reiniciar(self):
        with self.lock:
            self.fase = "lobby"
            self.version = 0
            self.jugadores = {}        # id -> {nombre, puntaje, respuestas}
            self.ronda_num = 0
            self.ubicacion = None
            self.orden = []
            self.inicio_ronda = None
            self.respuestas = {}       # id -> {lat, lon, segundos, puntos, km}
            self._tocar()

    def unirse(self, jugador_id, nombre):
        with self.lock:
            nombre = (nombre or "").strip()[:20] or "Anónimo"
            # Nombre repetido: se le agrega un numero, si no la tabla confunde.
            usados = {j["nombre"] for i, j in self.jugadores.items() if i != jugador_id}
            base, n = nombre, 2
            while nombre in usados:
                nombre = f"{base} ({n})"
                n += 1
            if jugador_id in self.jugadores:
                self.jugadores[jugador_id]["nombre"] = nombre
            else:
                self.jugadores[jugador_id] = {"nombre": nombre, "puntaje": 0, "respuestas": 0}
            self._tocar()
            return nombre

    def empezar(self):
        with self.lock:
            if not self.jugadores:
                return False
            self.orden = self._orden_ubicaciones()
            self.ronda_num = 0
            for j in self.jugadores.values():
                j["puntaje"] = 0
                j["respuestas"] = 0
            self._siguiente_ronda()
            return True

    def _siguiente_ronda(self):
        self.ronda_num += 1
        self.ubicacion = self.orden[self.ronda_num - 1]
        self.inicio_ronda = time.time()
        self.respuestas = {}
        self.fase = "ronda"
        self._tocar()

    def siguiente(self):
        """Avanza: resultados -> ronda siguiente, o al podio si ya no quedan."""
        with self.lock:
            if self.fase != "resultados":
                return
            if self.ronda_num >= len(self.orden):
                self.fase = "final"
                self._tocar()
            else:
                self._siguiente_ronda()

    def cerrar_ronda(self):
        with self.lock:
            if self.fase == "ronda":
                self.fase = "resultados"
                self._tocar()

    def segundos_restantes(self):
        if self.fase != "ronda" or self.inicio_ronda is None:
            return 0.0
        return max(0.0, self.segundos_por_ronda - (time.time() - self.inicio_ronda))

    def revisar_tiempo(self):
        """La llama el servidor en cada consulta: cierra la ronda sola."""
        with self.lock:
            if self.fase == "ronda":
                todos = len(self.respuestas) >= len(self.jugadores) and self.jugadores
                if self.segundos_restantes() <= 0 or todos:
                    self.cerrar_ronda()

    # -- respuestas ----------------------------------------------------------
    def responder(self, jugador_id, lat, lon):
        with self.lock:
            if self.fase != "ronda" or jugador_id not in self.jugadores:
                return None
            if jugador_id in self.respuestas:
                return self.respuestas[jugador_id]      # una sola por ronda

            usados = self.segundos_por_ronda - self.segundos_restantes()
            real = (self.ubicacion["lat"], self.ubicacion["lon"])
            d = distancia_km((lat, lon), real)
            puntos = calcular_puntaje(d, usados, self.segundos_por_ronda)

            self.respuestas[jugador_id] = {
                "lat": lat, "lon": lon, "km": d, "puntos": puntos,
                "segundos": round(usados, 1),
            }
            self.jugadores[jugador_id]["puntaje"] += puntos
            self.jugadores[jugador_id]["respuestas"] += 1
            self._tocar()
            return self.respuestas[jugador_id]

    # -- vistas --------------------------------------------------------------
    def tabla(self):
        filas = [
            {"id": i, "nombre": j["nombre"], "puntaje": j["puntaje"], "respuestas": j["respuestas"]}
            for i, j in self.jugadores.items()
        ]
        filas.sort(key=lambda f: (-f["puntaje"], f["nombre"]))
        for pos, f in enumerate(filas, 1):
            f["puesto"] = pos
        return filas

    def estado_host(self):
        with self.lock:
            d = {
                "version": self.version,
                "fase": self.fase,
                "ronda": self.ronda_num,
                "rondas_totales": len(self.orden) or self.rondas_totales,
                "jugadores": len(self.jugadores),
                "respondieron": len(self.respuestas),
                "restante": round(self.segundos_restantes(), 1),
                "segundos_ronda": self.segundos_por_ronda,
                "tabla": self.tabla(),
            }
            if self.fase in ("ronda", "resultados") and self.ubicacion:
                d["pista"] = {"lat": self.ubicacion["lat"], "lon": self.ubicacion["lon"]}
            if self.fase in ("resultados", "final") and self.ubicacion:
                d["solucion"] = {
                    "nombre": self.ubicacion["name"],
                    "lat": self.ubicacion["lat"],
                    "lon": self.ubicacion["lon"],
                }
                d["marcas"] = [
                    {"nombre": self.jugadores[i]["nombre"], "lat": r["lat"], "lon": r["lon"],
                     "km": round(r["km"], 2), "puntos": r["puntos"]}
                    for i, r in self.respuestas.items()
                ]
            return d

    def estado_jugador(self, jugador_id):
        with self.lock:
            yo = self.jugadores.get(jugador_id)
            d = {
                "version": self.version,
                "fase": self.fase,
                "ronda": self.ronda_num,
                "rondas_totales": len(self.orden) or self.rondas_totales,
                "restante": round(self.segundos_restantes(), 1),
                "segundos_ronda": self.segundos_por_ronda,
                "jugadores": len(self.jugadores),
                "unido": yo is not None,
                "nombre": yo["nombre"] if yo else None,
                "puntaje": yo["puntaje"] if yo else 0,
                "respondio": jugador_id in self.respuestas,
            }
            if self.fase in ("resultados", "final"):
                r = self.respuestas.get(jugador_id)
                if r:
                    emoji, frase, color = veredicto(r["km"])
                    d["mi_resultado"] = {
                        "km": round(r["km"], 2), "puntos": r["puntos"],
                        "segundos": r["segundos"],
                        "emoji": emoji, "frase": frase, "color": color,
                    }
                if self.ubicacion:
                    d["solucion"] = {"nombre": self.ubicacion["name"]}
                tabla = self.tabla()
                d["tabla"] = tabla[:5]
                d["mi_puesto"] = next((f["puesto"] for f in tabla if f["id"] == jugador_id), None)
            return d
