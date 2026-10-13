"""Servidor de la competencia. Se ejecuta en el portatil del profesor.

    python servidor.py

Imprime en consola la direccion del tablero (para el proyector) y la de los
jugadores (la del QR). Los celulares se conectan por el wifi del colegio; no
hace falta internet: los mapas salen de tiles.db, que viaja con el programa.

Sin dependencias: solo la libreria estandar. El front pregunta por el estado
una vez por segundo, que para 30 celulares en una red local sobra y evita
arrastrar un stack de websockets a una maquina prestada.
"""
import http.server
import json
import os
import secrets
import socket
import socketserver
import sqlite3
import sys
import threading
import webbrowser

import juego
import tunel as mod_tunel

AQUI = os.path.dirname(os.path.abspath(__file__))


def base_dir():
    """Dentro del .exe los datos quedan en _MEIPASS; sueltos, al lado del .py."""
    return getattr(sys, "_MEIPASS", AQUI)


BASE = base_dir()
WEB = os.path.join(BASE, "web")
DB = os.path.join(BASE, "tiles.db")
PUERTO = 8000

partida = juego.Partida()
TOKEN_HOST = secrets.token_urlsafe(6)

_db = sqlite3.connect(DB, check_same_thread=False)
_db_lock = threading.Lock()

URL_JUGAR = ""          # se llenan en main(), las usa el tablero para el QR
URLS_ALTERNAS = []


def tile(layer, z, x, y):
    with _db_lock:
        fila = _db.execute(
            "SELECT data FROM tiles WHERE layer=? AND z=? AND x=? AND y=?", (layer, z, x, y)
        ).fetchone()
    return fila[0] if fila else None


def ips_locales():
    """Direcciones por las que los celulares pueden llegar a esta maquina."""
    candidatas = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))        # no envia nada: solo mira la ruta
        candidatas.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidatas.append(info[4][0])
    except Exception:
        pass
    vistas, limpio = set(), []
    for ip in candidatas:
        if ip.startswith("127.") or ip in vistas:
            continue
        vistas.add(ip)
        limpio.append(ip)
    return limpio or ["127.0.0.1"]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    # -- utilidades ----------------------------------------------------------
    def responder_json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def leer_json(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def consulta(self):
        from urllib.parse import parse_qs, urlparse
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    def es_host(self):
        return self.consulta().get("token") == TOKEN_HOST

    # -- rutas ---------------------------------------------------------------
    def do_GET(self):
        ruta = self.path.split("?")[0]
        partes = ruta.strip("/").split("/")

        if ruta == "/":
            self.send_response(302)
            self.send_header("Location", "/jugar")
            self.end_headers()
            return

        if ruta == "/jugar":
            return self.archivo("jugador.html")

        if len(partes) == 2 and partes[0] == "host":
            if partes[1] != TOKEN_HOST:
                self.send_error(404)
                return
            return self.archivo("host.html")

        if len(partes) == 5 and partes[0] == "tiles":
            return self.servir_tile(partes[1:])

        if ruta == "/api/host":
            if not self.es_host():
                return self.responder_json({"error": "token"}, 403)
            partida.revisar_tiempo()
            estado = partida.estado_host()
            # El tablero se abre en 127.0.0.1, pero el QR tiene que apuntar a la
            # IP de esta maquina en el wifi: es la unica que ven los celulares.
            estado["url_jugar"] = URL_JUGAR
            estado["urls_alternas"] = URLS_ALTERNAS
            # El tablero cambia las instrucciones segun el modo: con tunel no
            # hay que pedirles que se conecten a ninguna wifi.
            estado["modo"] = "tunel" if URL_JUGAR.startswith("https://") else "local"
            estado["max_jugadores"] = juego.MAX_JUGADORES
            return self.responder_json(estado)

        if ruta == "/api/jugador":
            partida.revisar_tiempo()
            return self.responder_json(partida.estado_jugador(self.consulta().get("id", "")))

        super().do_GET()

    def do_POST(self):
        ruta = self.path.split("?")[0]
        datos = self.leer_json()

        if ruta == "/api/unirse":
            if partida.fase != "lobby":
                return self.responder_json({"error": "la partida ya empezó"}, 409)
            jid = datos.get("id") or secrets.token_urlsafe(8)
            if partida.esta_expulsado(jid):
                return self.responder_json(
                    {"error": "El profesor te sacó de la partida."}, 403)
            motivo, nombre = partida.unirse(jid, datos.get("nombre", ""))
            if motivo:
                return self.responder_json({"error": motivo}, 400)
            return self.responder_json({"id": jid, "nombre": nombre})

        if ruta == "/api/responder":
            r = partida.responder(datos.get("id", ""), float(datos["lat"]), float(datos["lon"]))
            return self.responder_json({"ok": r is not None})

        # De aca para abajo, solo el que tiene el token (el profesor)
        if not self.es_host():
            return self.responder_json({"error": "token"}, 403)
        if ruta == "/api/expulsar":
            return self.responder_json({"nombre": partida.expulsar(datos.get("id", ""))})
        if ruta == "/api/config":
            ok = partida.configurar(datos.get("rondas"), datos.get("segundos"))
            return self.responder_json({"ok": ok})
        if ruta == "/api/empezar":
            return self.responder_json({"ok": partida.empezar()})
        if ruta == "/api/siguiente":
            partida.siguiente()
            return self.responder_json({"ok": True})
        if ruta == "/api/cerrar":
            partida.cerrar_ronda()
            return self.responder_json({"ok": True})
        if ruta == "/api/reiniciar":
            partida.reiniciar()
            return self.responder_json({"ok": True})
        self.send_error(404)

    def archivo(self, nombre):
        ruta = os.path.join(WEB, nombre)
        with open(ruta, "rb") as fh:
            cuerpo = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def servir_tile(self, partes):
        layer, z, x, y = partes
        y = y.split(".")[0]
        try:
            datos = tile(layer, int(z), int(x), int(y))
        except ValueError:
            datos = None
        if datos is None:
            self.send_error(404)
            return
        self.send_response(200)
        if layer == "vt":
            self.send_header("Content-Type", "application/x-protobuf")
            if datos[:2] == b"\x1f\x8b":
                self.send_header("Content-Encoding", "gzip")
        else:
            self.send_header(
                "Content-Type", "image/png" if datos[:4] == b"\x89PNG" else "image/jpeg"
            )
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "max-age=86400")
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *a):
        pass


class Servidor(socketserver.ThreadingTCPServer):
    daemon_threads = True
    # OJO: en Windows, allow_reuse_address deja que DOS procesos se peguen al
    # mismo puerto, y las conexiones caen en cualquiera de los dos. Si alguien
    # abre el programa dos veces, la mitad de los celulares termina hablando
    # con una partida y la otra mitad con otra. Mejor fallar de entrada.
    allow_reuse_address = False


def puerto_ocupado(puerto):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def main():
    if not os.path.exists(DB):
        sys.exit("Falta tiles.db (los mapas). Ver el README.")

    if puerto_ocupado(PUERTO):
        sys.exit(
            "\n".join([
                "",
                f"  El puerto {PUERTO} ya esta ocupado.",
                "",
                "  Seguro dejaste otra ventana de este programa abierta. Cerrala y",
                "  vuelve a intentar: si quedan dos, los celulares se reparten",
                "  entre las dos partidas y el puntaje queda partido a la mitad.",
                "",
            ])
        )

    global URL_JUGAR, URLS_ALTERNAS
    ips = ips_locales()
    ip = ips[0]
    url_jugar = URL_JUGAR = f"http://{ip}:{PUERTO}/jugar"
    URLS_ALTERNAS = [f"http://{o}:{PUERTO}/jugar" for o in ips[1:]]
    url_host = f"http://127.0.0.1:{PUERTO}/host/{TOKEN_HOST}"

    # El tunel es lo normal: los estudiantes entran por internet, con datos o
    # con la wifi que sea. Solo hace falta que ESTE portatil tenga internet.
    # Con --local se fuerza el modo red local (todos en la misma wifi).
    t = None
    if "--local" not in sys.argv:
        print("Abriendo la dirección pública (unos segundos)...")
        t = mod_tunel.Tunel(PUERTO)
        publica = t.abrir()
        if publica:
            URLS_ALTERNAS = [url_jugar] + URLS_ALTERNAS
            url_jugar = URL_JUGAR = publica + "/jugar"
        elif mod_tunel.buscar_ejecutable() is None:
            print(mod_tunel.AYUDA_SIN_CLOUDFLARED)
        else:
            print("  No pude abrir el túnel. Sigo en modo red local.")
            print("  Lo que dijo cloudflared:")
            for linea in t.diagnostico().splitlines():
                print("     ", linea)
            t.cerrar()
            t = None

    print("=" * 66)
    print("  GEOGUESSR SANTANDER - COMPETENCIA")
    print("=" * 66)
    print()
    print("  TABLERO (proyecta esta pantalla):")
    print(f"    {url_host}")
    print()
    print("  JUGADORES (el QR del tablero lleva aca):")
    print(f"    {url_jugar}")
    if URLS_ALTERNAS:
        print("    otras direcciones, por si esa no sirve:")
        for otra in URLS_ALTERNAS:
            print(f"      {otra}")
    print()
    if t:
        print("  Modo TUNEL: los celulares entran por internet, con datos")
        print("  moviles o con cualquier wifi. Este portatil si necesita internet.")
    else:
        print("  Modo RED LOCAL: los celulares tienen que estar en el MISMO WIFI")
        print("  que este portatil. No hace falta internet.")
    print()
    print("  >> NO CIERRES ESTA VENTANA mientras dure la competencia <<")
    print("=" * 66)

    with Servidor(("0.0.0.0", PUERTO), Handler) as httpd:
        # Importado arriba a proposito: con __import__ dentro del lambda,
        # PyInstaller no lo detecta y el .exe se queda sin abrir el navegador.
        threading.Timer(0.8, lambda: webbrowser.open(url_host)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nListo, hasta luego.")
        finally:
            if t:
                t.cerrar()      # si queda vivo, el tunel sigue publicando el servidor


if __name__ == "__main__":
    main()
