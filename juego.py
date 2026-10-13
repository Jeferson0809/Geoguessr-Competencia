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

# Sin tope de jugadores. Pasados unos 50 la tabla del tablero se vuelve dificil
# de leer desde el fondo del salon, pero eso es cosa de la pantalla y no una
# razon para dejar a alguien afuera. Poner un numero aqui lo vuelve a activar.
MAX_JUGADORES = None
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


# --- nombres -----------------------------------------------------------------
# Se proyecta en el tablero delante de todo el salon, asi que no puede entrar
# cualquier cosa. La lista es corta a proposito: no busca atrapar todo, busca
# atrapar lo que un estudiante escribe en diez segundos para hacer reir.
PALABROTAS = {
    # --- insultos, español ---
    "puta", "puto", "putita", "putear", "puteria", "mierda", "mierdero",
    "verga", "vergazo", "pirobo", "piroba", "gonorrea", "malparido",
    "malparida", "hijueputa", "jueputa", "hpta", "huevon", "huevona",
    "guevon", "guevona", "marica", "maricon", "marikon", "maricona",
    "gamin", "zorra", "cabron", "cabrona", "pendejo", "pendeja", "imbecil",
    "estupido", "estupida", "idiota", "tarado", "tarada", "gilipollas",
    "capullo", "cono", "chimba", "cojones", "joder", "jodido", "chucha",
    "pelotudo", "boludo", "chingar", "chinga", "pinche", "escoria",
    # --- cuerpo y sexo ---
    "pene", "pito", "pipi", "polla", "pinga", "picha", "chota", "pija",
    "culo", "culia", "culiar", "culear", "culito", "culon", "culona",
    "nalga", "teta", "tetona", "vagina", "vulva", "clitoris", "testiculo",
    "semen", "esperma", "orgasmo", "masturba", "pajero", "pajera",
    "mamada", "mamar", "mamon", "mamona", "mamaguevo", "mamahuevo",
    "mamapinga", "chupapolla", "chupamela", "chupame", "follar", "coger",
    "sexo", "sexual", "sexy", "porno", "pornhub", "xxx", "dildo",
    "prostitu", "virgen",
    # --- baño ---
    "caca", "cagada", "cagar", "cagon", "popo", "pedorro", "orina", "mear",
    # --- cosas que no queremos proyectadas en un colegio ---
    "nazi", "hitler", "violador", "violacion", "violar", "pedofil",
    "suicid", "cocaina", "marihuana", "droga", "bazuco", "heroina",
    "porro", "tusi", "perico",
    # --- ingles ---
    "fuck", "fuk", "fck", "shit", "bitch", "biatch", "dick", "cock",
    "pussy", "cunt", "twat", "asshole", "arsehole", "bastard", "whore",
    "slut", "boobs", "tits", "penis", "nigga", "nigger", "nigg", "faggot",
    "retard", "porn", "sexi", "horny", "jerkoff", "wanker", "bollocks",
    "bloody", "damn", "crap", "turd", "douche", "pimp", "stripper",
}

# Nombres legitimos que contienen una palabrota como pedazo. Sin esto, alguien
# que se llame asi no puede entrar y queda en ridiculo delante del salon.
# Cosas que son solo letras y parecen nombre, pero no lo son.
NO_SON_NOMBRES = {
    "qwerty", "asdf", "asdfgh", "zxcv", "test", "prueba", "admin", "profe",
    "profesor", "nadie", "anonimo", "ninguno", "nombre", "jugador", "player",
    "usuario", "user", "hola", "none", "null", "undefined", "bot",
}

PERMITIDOS = {"culotta", "escultor", "pitagorico", "reputacion", "cogerman",
              "esculapio", "pitonisa", "cocacola"}

_EQUIVALENCIAS = str.maketrans({
    "4": "a", "@": "a", "3": "e", "1": "i", "!": "i", "0": "o",
    "5": "s", "$": "s", "7": "t", "8": "b",
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
})


def _normalizar(texto):
    """Minusculas sin tildes, sin leet y sin nada que no sea letra o numero.

    'P.U.T.4' y 'pUt@a' terminan los dos en 'puta'.
    """
    t = texto.lower().translate(_EQUIVALENCIAS)
    return "".join(c for c in t if c.isalnum())


def _aplastar(texto):
    """Ademas junta letras repetidas: 'putooooo' -> 'puto'.

    Se compara aparte y NO se le aplica a la lista negra: si se aplastara
    'xxx' quedaria en 'x', y entonces Max, Alex o Ximena quedarian vetados.
    """
    salida = []
    for c in texto:
        if not salida or salida[-1] != c:
            salida.append(c)
    return "".join(salida)


def nombre_invalido(nombre):
    """Motivo por el que no sirve como nombre real, o None si esta bien.

    Se pide nombre de verdad y no apodo de videojuego: la gracia es que el
    salon vea quien va ganando. Ademas, exigir solo letras tumba de una los
    'xXDarkXx' y los '1234' sin tener que listarlos uno por uno.
    """
    n = (nombre or "").strip()
    if len(n) < 2:
        return "Escribe tu nombre (al menos 2 letras)."
    if len(n) > 20:
        return "Muy largo: máximo 20 letras."
    if any(c.isdigit() for c in n):
        return "Solo letras, sin números. Pon tu nombre real."
    if not all(c.isalpha() or c in " '-." for c in n):
        return "Solo letras. Pon tu nombre real."
    if sum(c.isalpha() for c in n) < 2:
        return "Escribe tu nombre."
    if len(n.split()) > 3:
        return "Tu nombre y tu apellido, nada más."
    if _normalizar(n) in NO_SON_NOMBRES:
        return "Pon tu nombre de verdad."

    # Hasta aca pasan cosas como 'xXDarkXx', que son solo letras pero no son
    # un nombre. Dos señales que lo delatan sin tener que listarlos:
    plano = _normalizar(n)
    for letra in set(plano):
        if plano.count(letra) > 3:
            return "Eso no parece un nombre. Pon el tuyo."
    vocales = set("aeiouy")
    for palabra in plano_palabras(n):
        if not (set(palabra) & vocales):
            return "Eso no parece un nombre. Pon el tuyo."
        seguidas = 0
        for c in palabra:
            seguidas = 0 if c in vocales else seguidas + 1
            if seguidas >= 5:
                return "Eso no parece un nombre. Pon el tuyo."
    return None


def plano_palabras(nombre):
    return [_normalizar(p) for p in nombre.split() if _normalizar(p)]


def nombre_ofensivo(nombre):
    plano = _normalizar(nombre)
    if not plano or plano in {_normalizar(x) for x in PERMITIDOS}:
        return False
    aplastado = _aplastar(plano)
    return any(w in plano or w in aplastado
               for w in (_normalizar(p) for p in PALABROTAS))


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
            self.expulsados = set()    # ids sacados por el profesor
            self.ronda_num = 0
            self.ubicacion = None
            self.orden = []
            self.inicio_ronda = None
            self.respuestas = {}       # id -> {lat, lon, segundos, puntos, km}
            self.puntajes_congelados = {}
            self._tocar()

    def expulsar(self, jugador_id):
        """Saca a alguien de la partida. Ningun filtro de nombres es perfecto,
        asi que el profesor tiene que poder sacar a quien se le cuele."""
        with self.lock:
            if jugador_id not in self.jugadores:
                return None
            nombre = self.jugadores.pop(jugador_id)["nombre"]
            self.respuestas.pop(jugador_id, None)
            self.puntajes_congelados.pop(jugador_id, None)
            self.expulsados.add(jugador_id)
            self._tocar()
            return nombre

    def esta_expulsado(self, jugador_id):
        with self.lock:
            return jugador_id in self.expulsados

    def configurar(self, rondas=None, segundos=None):
        """Solo desde el lobby: cambiar largo de la partida antes de empezar."""
        with self.lock:
            if self.fase != "lobby":
                return False
            if rondas is not None:
                self.rondas_totales = max(1, min(int(rondas), self.max_rondas()))
            if segundos is not None:
                self.segundos_por_ronda = max(10, min(int(segundos), 300))
            self._tocar()
            return True

    def max_rondas(self):
        """No se puede repetir lugar, asi que el tope son las ubicaciones."""
        return len(self.ubicaciones)

    def unirse(self, jugador_id, nombre):
        """Devuelve (motivo_del_rechazo, nombre_final). Uno de los dos es None."""
        with self.lock:
            nombre = (nombre or "").strip()
            if (MAX_JUGADORES and jugador_id not in self.jugadores
                    and len(self.jugadores) >= MAX_JUGADORES):
                return f"La sala está llena ({MAX_JUGADORES} jugadores).", None
            motivo = nombre_invalido(nombre)
            if motivo:
                return motivo, None    # el servidor lo manda tal cual al celular
            if nombre_ofensivo(nombre):
                return "Ese nombre no se puede: se proyecta en el tablero.", None
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
            return None, nombre

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
        # Foto de la tabla al arrancar la ronda. Durante la ronda se muestra
        # esta y no la viva: si el tablero fuera sumando los puntos a medida
        # que responden, el que todavia no respondio ve quien acerto y se
        # delata solo el nivel de la respuesta. Se revela al cerrar.
        self.puntajes_congelados = {i: j["puntaje"] for i, j in self.jugadores.items()}
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
    def tabla(self, congelada=False):
        """congelada: puntajes como estaban al empezar la ronda (ver _siguiente_ronda)."""
        filas = []
        for i, j in self.jugadores.items():
            puntaje = self.puntajes_congelados.get(i, 0) if congelada else j["puntaje"]
            filas.append({
                "id": i, "nombre": j["nombre"], "puntaje": puntaje,
                "respuestas": j["respuestas"], "respondio": i in self.respuestas,
            })
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
                "max_rondas": self.max_rondas(),
                # Durante la ronda la tabla va congelada y sin revelar puntos.
                "tabla": self.tabla(congelada=self.fase == "ronda"),
                "ocultar_puntos": self.fase == "ronda",
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
                # Durante la ronda, su puntaje de antes de responder: si no,
                # sabe como le fue antes de que termine.
                "puntaje": (self.puntajes_congelados.get(jugador_id, 0)
                            if self.fase == "ronda" and yo
                            else (yo["puntaje"] if yo else 0)),
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
