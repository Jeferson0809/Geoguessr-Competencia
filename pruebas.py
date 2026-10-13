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
igual(p.unirse("c", "Ana")[1], "Ana (2)", "los nombres repetidos se numeran")
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

print("\nNombres: lo que se proyecta delante del salón")
for malo in ["puta", "PUTA", "p u t a", "pUt4", "m1erda", "marica", "HIJUEPUTA",
             "Juan malparido", "fuck", "putoooo", "gonorrea",
             # estas se colaron en la primera prueba de verdad, con un
             # estudiante (el autor) probando el filtro desde el celular
             "Mamada", "m4m4d4", "Culiao", "polla", "caca", "boobs"]:
    assert juego.nombre_ofensivo(malo), f"deberia bloquear {malo!r}"
print("  ok  bloquea groserias, mayusculas, espacios y numeros por letras")
for bueno in ["Jeferson", "María José", "Santi", "Andrés", "Ana-Lucía",
              "Nicolás", "Escultor", "Mamerto", "Claudia", "Luciano",
              "Picasso", "Mateo", "Ximena", "Max", "Christian"]:
    assert not juego.nombre_ofensivo(bueno), f"no deberia bloquear {bueno!r}"
print("  ok  deja pasar nombres normales")

print()
print("Nombres: tiene que ser un nombre de verdad")
for apodo in ["xXDarkXx", "Pepe123", "qwerty", "asdf", "test", "admin",
              "aaaaa", "x", "1234", "bot", "hola"]:
    assert juego.nombre_invalido(apodo), f"deberia rechazar {apodo!r}"
print("  ok  rechaza apodos, numeros y tecleos")
for real in ["Jeferson", "María José", "Luz Marina", "Ximena", "Max",
             "Christian", "Juan Pablo", "Ana-Lucía", "O'Brien"]:
    assert not juego.nombre_invalido(real), f"no deberia rechazar {real!r}"
print("  ok  deja pasar nombres y apellidos reales")

p2 = juego.Partida(segundos_por_ronda=30, rondas=5)
motivo, nom = p2.unirse("z", "marica")
assert motivo and nom is None, "al ofensivo no lo deja entrar"
print("  ok  al ofensivo no lo deja entrar:", motivo)
igual(len(p2.jugadores), 0, "y no queda en la sala")
motivo, nom = p2.unirse("z2", "Ana")
igual(motivo, None, "a un nombre normal si")

print("\nConfigurar la partida antes de empezar")
igual(p2.configurar(rondas=12), True, "se puede cambiar el numero de rondas")
igual(p2.rondas_totales, 12, "quedaron 12")
igual(p2.configurar(segundos=90), True, "y los segundos")
igual(p2.segundos_por_ronda, 90, "quedaron 90")
p2.configurar(rondas=9999)
igual(p2.rondas_totales, p2.max_rondas(), "no deja mas rondas que ubicaciones")
p2.unirse("w", "Ana María")
p2.configurar(rondas=2)
p2.empezar()
igual(p2.configurar(rondas=5), False, "ya empezada, no se puede reconfigurar")
igual(len(p2.orden), 2, "respeta las rondas configuradas")

print("\nDurante la ronda no se revelan puntos")
p3 = juego.Partida(segundos_por_ronda=30, rondas=2)
p3.unirse("a", "Ana"); p3.unirse("b", "Beto")
p3.empezar()
real = (p3.ubicacion["lat"], p3.ubicacion["lon"])
p3.responder("a", real[0], real[1])
h = p3.estado_host()
igual(h["ocultar_puntos"], True, "el tablero sabe que debe ocultarlos")
igual([f["puntaje"] for f in h["tabla"]], [0, 0], "la tabla va congelada en 0")
igual([f["nombre"] for f in h["tabla"] if f["respondio"]], ["Ana"], "pero si se ve quien respondio")
igual(p3.estado_jugador("a")["puntaje"], 0, "Ana tampoco ve su puntaje todavia")
p3.cerrar_ronda()
h = p3.estado_host()
igual(h["ocultar_puntos"], False, "al cerrar ya se pueden mostrar")
assert h["tabla"][0]["puntaje"] > 900, "y ahi si aparece el puntaje real"
print(f"  ok  al cerrar la ronda aparece: {h['tabla'][0]['puntaje']} puntos")
assert p3.estado_jugador("a")["puntaje"] > 900
print("  ok  el jugador tambien lo ve recien ahi")

print("\nCuántos caben")
igual(juego.MAX_JUGADORES, None, "por defecto no hay tope")
pm = juego.Partida()
for i in range(80):
    pm.unirse(f"j{i}", "Ana")
igual(len(pm.jugadores), 80, "entran 80 sin chistar")
juego.MAX_JUGADORES = 3          # por si alguna vez hace falta ponerle tope
pt = juego.Partida()
for i in range(3):
    pt.unirse(f"k{i}", "Ana")
motivo, _ = pt.unirse("extra", "Pedro")
assert motivo and "llena" in motivo, "con tope puesto, el que sobra recibe aviso"
print("  ok  con tope puesto avisa:", motivo)
juego.MAX_JUGADORES = None

print("\nSacar jugadores")
p4 = juego.Partida(segundos_por_ronda=30, rondas=2)
p4.unirse("m", "Pepe")
p4.unirse("n", "Ana")
igual(p4.expulsar("m"), "Pepe", "devuelve a quien saco")
igual(len(p4.jugadores), 1, "queda uno solo")
igual(p4.esta_expulsado("m"), True, "queda marcado para que no vuelva")
igual(p4.expulsar("nadie"), None, "sacar a alguien que no esta no revienta")
p4.empezar()
assert p4.expulsar("n") is not None, "tambien se puede sacar en plena ronda"
igual(len(p4.jugadores), 0, "y desaparece de la tabla")

print("\nTODAS LAS PRUEBAS PASARON")
