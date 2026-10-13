# GeoGuessr Santander — Competencia

Versión **multijugador** del GeoGuessr aéreo de Bucaramanga, al estilo Kahoot:
el profesor proyecta un tablero, los estudiantes escanean un QR y compiten desde
el celular. Rondas con tiempo, puntaje por cercanía y rapidez, y podio al final.

**Funciona sin internet.** El portátil del profesor es el servidor y los celulares
se conectan por el wifi del salón. Los mapas viajan dentro del programa.

> La versión de un jugador vive en otro repo:
> [Geoguessr-Santander](https://github.com/Jeferson0809/Geoguessr-Santander).

---

## Cómo se juega

**El profesor** abre el programa y proyecta el **tablero**. Ahí sale un QR.

**Los estudiantes** escanean el QR con la cámara, escriben su nombre y esperan.

Cada ronda:

1. El tablero muestra una **foto satelital** de un lugar de Bucaramanga.
   Empieza muy cerca y **se va alejando sola** a medida que corre el tiempo.
2. En el celular, cada uno **toca el mapa** donde cree que es y confirma.
3. La ronda cierra cuando se acaba el tiempo o cuando ya respondieron todos.
4. El tablero muestra dónde era, dónde marcó cada uno y la tabla de posiciones.

Al final, podio.

---

## Puntaje

Dos cosas se multiplican: qué tan cerca marcaste y qué tan rápido lo hiciste.

**Cercanía** — hasta 150 m del punto son 1000 puntos (si le diste al edificio no
hace falta el píxel exacto). De ahí cae exponencial:

| Error | 1 km | 2 km | 5 km | 10 km |
|---|---|---|---|---|
| Puntos | 809 | 630 | 297 | 85 |

**Rapidez** — responder de una vale el doble que responder sobre la chicharra,
y nunca baja del 50%, para que el que piensa despacio pero ubica bien no quede
humillado.

Por eso la foto se va alejando: arriesgar temprano con poca información vale más
que esperar a que el lugar sea obvio.

Los tres números se ajustan arriba de [`juego.py`](juego.py):
`SEGUNDOS_POR_RONDA`, `RONDAS_POR_PARTIDA`, `TOLERANCIA_KM`.

---

## Para correrlo

```bash
python servidor.py
```

Imprime dos direcciones: la del **tablero** (se abre sola en el navegador) y la
de los **jugadores**, que es a la que apunta el QR.

El tablero vive en una URL con un código secreto (`/host/xxxxxxx`) que cambia en
cada arranque. Así un estudiante que escriba la IP a mano cae en la pantalla de
jugador y no puede saltarse rondas.

### Empaquetado para llevar al colegio

```bash
pip install pyinstaller
python empaquetar.py
```

Deja `dist/GeoGuessr-Competencia/` con un `.exe` adentro: se copia la carpeta
completa al portátil y se abre con doble clic, sin instalar Python.

---

## Los mapas

No se suben a git (`tiles.db`, ~47 MB). Se regeneran con internet, una sola vez:

```bash
pip install pmtiles
python descargar_mapas.py
```

Baja dos capas distintas:

- **Satélite** (Esri) alrededor de cada ubicación, zoom 16–19. Es la pista.
- **Vectorial** de OpenStreetMap vía [Protomaps](https://protomaps.com), de toda
  el área metropolitana. Es el mapa donde se marca.

El vectorial pesa 5 MB para toda el área y se dibuja nítido a cualquier zoom. **No
se usan los tiles de imagen de OpenStreetMap**: su política prohíbe la descarga
masiva y el servidor responde *"Access blocked"* con código 200, así que el tile
malo se cuela como bueno. Los *datos* de OSM sí son libres de empaquetar.

Si agregas una ubicación nueva, corre `descargar_mapas.py` otra vez: baja solo
el satélite que falte.

---

## Ubicaciones

Se editan en [`web/locations.js`](web/locations.js). El que tiene `"pinned": true`
sale **siempre en la primera ronda** — pensado para el colegio que se visita ese día.

Están sincronizadas con las del repo de un jugador. Solo entran lugares que se
reconocen **desde el aire**: varios parques de Bucaramanga son plazoletas tapadas
de árboles y como pista aérea son injugables aunque todo el mundo los conozca.

---

## Qué hay adentro

| Archivo | Para qué |
|---|---|
| [`juego.py`](juego.py) | Las reglas: jugadores, rondas, puntajes. No sabe nada de HTTP. |
| [`servidor.py`](servidor.py) | HTTP + API + sirve los mapas desde `tiles.db`. Librería estándar, sin dependencias. |
| [`pruebas.py`](pruebas.py) | Pruebas de las reglas. `python pruebas.py`, no necesita servidor ni navegador. |
| [`web/host.html`](web/host.html) · `host.js` | El tablero del proyector. |
| [`web/jugador.html`](web/jugador.html) · `jugador.js` | La pantalla del celular. |
| [`descargar_mapas.py`](descargar_mapas.py) | Baja los mapas a `tiles.db`. |
| [`empaquetar.py`](empaquetar.py) | Arma el `.exe` con PyInstaller. |

El front pregunta el estado una vez por segundo en vez de usar websockets. Para
30 celulares en una red local no se nota la diferencia, y evita arrastrar un
stack de dependencias a un portátil prestado.

---

Mapas: satélite © Esri. Calles y nombres © colaboradores de OpenStreetMap (ODbL),
vía Protomaps.
