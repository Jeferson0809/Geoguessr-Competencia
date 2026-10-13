# GeoGuessr Santander — Competencia

Versión **multijugador** del GeoGuessr aéreo de Bucaramanga, al estilo Kahoot:
el profesor proyecta un tablero, los estudiantes escanean un QR y compiten desde
el celular. Rondas con tiempo, puntaje por cercanía y rapidez, y podio al final.

El portátil del profesor es el servidor y los mapas viajan dentro del programa.
Hay **dos formas** de que entren los celulares, según lo que haya ese día:

| | Red local | Túnel |
|---|---|---|
| Comando | `python servidor.py` | `python servidor.py --tunel` |
| Los celulares entran por | el wifi del salón | internet (datos móviles o cualquier wifi) |
| Necesita internet | **No** | Sí, pero solo en el portátil |
| Cuándo usarlo | hay una wifi y todos caben en ella | a ti te dan la wifi de admin y los chicos andan con datos |

En los colegios suele pasar lo segundo: al profesor le dan la red de administración
y los estudiantes quedan con datos móviles. Ahí la red local **no sirve**: un celular
con datos no puede alcanzar la IP privada del portátil. Para eso está el túnel.

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
python servidor.py           # red local
python servidor.py --tunel   # con URL pública, para datos móviles
```

Imprime dos direcciones: la del **tablero** (se abre sola en el navegador) y la
de los **jugadores**, que es a la que apunta el QR.

El tablero vive en una URL con un código secreto (`/host/xxxxxxx`) que cambia en
cada arranque. Así un estudiante que escriba la dirección a mano cae en la pantalla
de jugador y no puede saltarse rondas. Esto importa más todavía con el túnel, donde
la dirección es pública.

### El túnel

`--tunel` usa [cloudflared](https://github.com/cloudflare/cloudflared) para darle al
servidor local una URL pública temporal. No pide cuenta ni tarjeta, no abre puertos
en el router, y la URL muere al cerrar el programa (es distinta cada vez, así que el
QR hay que proyectarlo en el momento).

Se consigue una sola vez:

```bash
python obtener_cloudflared.py
```

Si no está, el juego avisa y sigue funcionando en modo red local.

**Cuánto gastan de datos los estudiantes:** poco. El celular solo descarga el mapa
de calles, que son vectores — las fotos satelitales, que es lo pesado, se quedan en
el proyector. Un par de MB por teléfono.

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
| [`tunel.py`](tunel.py) · [`obtener_cloudflared.py`](obtener_cloudflared.py) | La URL pública para cuando los chicos están con datos. |
| [`pruebas_tunel.py`](pruebas_tunel.py) | Prueba el túnel con un cloudflared de mentira, sin descargar ni publicar nada. |
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
