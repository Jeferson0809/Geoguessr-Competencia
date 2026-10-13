"""Pruebas de la logica del juego. No necesitan servidor ni navegador.

    python pruebas.py
"""
import time

import juego


def igual(a, b, msg):
    assert a == b, f"{msg}: esperaba {b}, llego {a}"
    print(f"  ok  {msg}")


def cerca(a, b, tol, msg):
    assert abs(a - b) <= tol, f"{msg}: esperaba ~{b}, llego {a}"
    print(f"  ok  {msg} ({a})")


print("Puntaje por distancia")
cerca(juego.puntos_por_distancia(0.0), 1000, 1, "en el punto exacto son 1000")
cerca(juego.puntos_por_distancia(0.15), 1000, 1, "dentro de la tolerancia tambien")
cerca(juego.puntos_por_distancia(1.0), 809, 2, "1 km")
cerca(juego.puntos_por_distancia(5.0), 297, 2, "5 km")

print("\nFactor de rapidez")
cerca(juego.factor_rapidez(0, 60), 1.0, 0.01, "responder de una vale el 100%")
cerca(juego.factor_rapidez(30, 60), 0.75, 0.01, "a mitad de tiempo, 75%")
cerca(juego.factor_rapidez(60, 60), 0.5, 0.01, "sobre la chicharra, 50%")
cerca(juego.factor_rapidez(999, 60), 0.5, 0.01, "nunca baja del 50%")

print("\nPartida completa")
p = juego.Partida(segundos_por_ronda=10, rondas=3)
igual(p.fase, "lobby", "arranca en lobby")
igual(p.empezar(), False, "sin jugadores no arranca")

p.unirse("a", "Ana")
p.unirse("b", "Luis")
igual(p.unirse("c", "Ana"), "Ana (2)", "los nombres repetidos se numeran")
igual(len(p.jugadores), 3, "tres jugadores")

igual(p.empezar(), True, "con jugadores si arranca")
igual(p.fase, "ronda", "pasa a ronda")
igual(p.ronda_num, 1, "va en la ronda 1")
igual(p.ubicacion["name"], p.orden[0]["name"], "la primera es la fijada")
assert p.orden[0].get("pinned"), "la ubicacion fijada debe salir primero"
print("  ok  la ubicacion 'pinned' sale en la ronda 1")

real = (p.ubicacion["lat"], p.ubicacion["lon"])
r = p.responder("a", real[0], real[1])
igual(r["puntos"], 1000, "clavarla apenas empieza da 1000")
igual(p.responder("a", 7.0, -73.0)["puntos"], 1000, "la segunda respuesta se ignora")

p.responder("b", real[0] + 0.05, real[1])            # ~5.5 km
assert p.jugadores["b"]["puntaje"] < 400, "fallar por 5 km debe costar caro"
print(f"  ok  errar ~5 km deja {p.jugadores['b']['puntaje']} puntos")

igual(p.fase, "ronda", "sigue en ronda: falta uno por responder")
p.responder("c", real[0], real[1])
p.revisar_tiempo()
igual(p.fase, "resultados", "cuando responden todos, la ronda cierra sola")

t = p.tabla()
igual(t[0]["puesto"], 1, "la tabla viene con puesto")
igual(t[-1]["nombre"], "Luis", "el que fallo queda ultimo")

p.siguiente()
igual(p.fase, "ronda", "arranca la ronda 2")
igual(p.ronda_num, 2, "ronda 2")
igual(len(p.respuestas), 0, "las respuestas se limpian")

print("\nCierre por tiempo")
q = juego.Partida(segundos_por_ronda=1, rondas=1)
q.unirse("x", "Pedro")
q.empezar()
time.sleep(1.1)
q.revisar_tiempo()
igual(q.fase, "resultados", "se acaba el tiempo y la ronda cierra")
igual(q.estado_jugador("x").get("mi_resultado"), None, "el que no respondio no suma")
q.siguiente()
igual(q.fase, "final", "despues de la ultima ronda, el podio")

print("\nEstados que consume el front")
e = p.estado_host()
for k in ("version", "fase", "ronda", "tabla", "restante"):
    assert k in e, f"al host le falta {k}"
print("  ok  estado del host completo")
e = p.estado_jugador("a")
for k in ("version", "fase", "unido", "nombre", "respondio"):
    assert k in e, f"al jugador le falta {k}"
print("  ok  estado del jugador completo")

print("\nTODAS LAS PRUEBAS PASARON")
