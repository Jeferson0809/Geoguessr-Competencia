# GeoGuessr Santander — Competencia

Versión **multijugador** del GeoGuessr aéreo de Bucaramanga, al estilo Kahoot:
el profesor proyecta un tablero, los estudiantes escanean un QR y compiten desde
el celular. Rondas con tiempo, puntaje por cercanía y rapidez, y podio al final.

El portátil del profesor es el servidor y los mapas viajan dentro del programa.
Hay **dos formas** de que entren los celulares, según lo que haya ese día:

| | Normal | `--local` |
|---|---|---|
| Comando | `python servidor.py` | `python servidor.py --local` |
| Los celulares entran por | internet (datos o cualquier wifi) | el wifi del salón |
| Necesita internet | Sí, **solo en el portátil** | No |
| Cuándo | casi siempre | no hay internet en ningún lado |

Por defecto se abre una dirección pública temporal, así que los estudiantes entran
con datos móviles o con la wifi que sea. Esto importa: en los colegios al profesor le
dan la red de administración y los chicos quedan con sus datos, y ahí un celular **no
puede** alcanzar la IP privada del portátil.

Si el portátil se queda sin internet, el programa lo detecta y sigue en modo red
local automáticamente, avisando en la consola.

> La versión de un jugador vive en otro repo:
> [Geoguessr-Santander](https://github.com/Jeferson0809/Geoguessr-Santander).

---

## Para el que va a dirigir la competencia

**No hace falta clonar el repo ni saber de programación.** Hay dos caminos:

### Camino corto: descargar y abrir

1. Descarga **`GeoGuessr-Competencia.zip`** de la
   [página de descargas](https://github.com/Jeferson0809/Geoguessr-Competencia/releases/latest) (~73 MB).
2. Descomprímelo y copia la carpeta **completa** donde quieras (sirve un USB).
3. Doble clic en **`GeoGuessr-Competencia.exe`**.

Eso es todo. No necesita Python, ni git, ni instalar nada. Los mapas y el programa
que abre la dirección pública ya vienen adentro.

> El `.exe` solo no funciona: al lado van los mapas y las librerías, en `_internal/`.
> Si Windows muestra "aplicación desconocida" es porque el programa no está firmado:
> *Más información → Ejecutar de todas formas*.

### Camino largo: clonar el repo

Solo si vas a **cambiar** algo (ubicaciones, puntaje, tiempos):

```bash
git clone https://github.com/Jeferson0809/Geoguessr-Competencia.git
cd Geoguessr-Competencia
pip install pmtiles          # solo para bajar los mapas
python descargar_mapas.py    # ~10 min, una sola vez
python servidor.py
```

---

## El día de la competencia

1. **Conecta el portátil a internet.** La wifi del colegio o tus datos, da igual.
   Los estudiantes **no** tienen que estar en esa red.
2. Abre el programa y espera unos 10 segundos. Se abre solo el **tablero** en el
   navegador, con un QR.
3. **Proyecta el tablero** y ponlo en pantalla completa con `F11`.
4. En el menú elige **cuántas rondas** y **cuántos segundos**. Para un grupo nuevo:
   5 rondas de 60 segundos, unos 7 minutos.
5. Los estudiantes **escanean el QR** con la cámara, escriben su nombre y aparecen
   en la pantalla. Entran con datos móviles o con cualquier wifi.
6. Cuando estén todos, **"Empezar competencia"**.

**Durante la partida tienes dos controles**: la **✕** al lado de cada nombre para
sacar a alguien, y **"Cerrar ronda ya"** para no esperar el reloj si ya respondieron
todos.

**Tres cosas que conviene saber:**

- **No cierres la ventana negra.** Ahí vive el servidor.
- **La dirección del QR cambia cada vez** que abres el programa. Proyéctalo en el
  momento; no sirve mandarlo antes por WhatsApp.
- **Si el portátil se queda sin internet**, el programa avisa y sigue funcionando,
  pero ahí los celulares sí tendrían que estar en tu misma wifi.

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

Al final, podio al centro y la tabla completa al lado.

Durante la ronda el tablero muestra **quién ya respondió, pero no cuántos puntos**:
si los puntajes fueran apareciendo, el que todavía no responde vería quién acertó.
Se revelan al cerrar.

**Nombres:** se exige nombre real (solo letras, máximo tres palabras) y hay un filtro
de groserías en español e inglés. Como ningún filtro atrapa todo, el profesor tiene
una **✕ al lado de cada nombre** para sacar a quien se le cuele, en el lobby o en
plena partida.

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
python servidor.py           # normal: dirección pública
python servidor.py --local   # solo red local, sin internet
```

Imprime dos direcciones: la del **tablero** (se abre sola en el navegador) y la
de los **jugadores**, que es a la que apunta el QR.

El tablero vive en una URL con un código secreto (`/host/xxxxxxx`) que cambia en
cada arranque. Así un estudiante que escriba la dirección a mano cae en la pantalla
de jugador y no puede saltarse rondas. Esto importa más todavía con el túnel, donde
la dirección es pública.

### La dirección pública

El programa usa [cloudflared](https://github.com/cloudflare/cloudflared) para darle al
servidor local una URL pública temporal. No pide cuenta ni tarjeta, no abre puertos
en el router, y la URL muere al cerrar el programa (es distinta cada vez, así que el
QR hay que proyectarlo en el momento).

Se consigue una sola vez:

```bash
python obtener_cloudflared.py
```

Si no está, el juego avisa y sigue funcionando en modo red local.

**No hay tope de jugadores.** Pasados unos 50 la tabla del tablero se vuelve difícil
de leer desde el fondo del salón, pero eso es cosa de la pantalla, no una razón para
dejar a alguien afuera. Si alguna vez hace falta un límite, es `MAX_JUGADORES` en
[`juego.py`](juego.py).

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
| [`simular_jugadores.py`](simular_jugadores.py) | Jugadores falsos para probar sin tener 30 celulares. |
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
