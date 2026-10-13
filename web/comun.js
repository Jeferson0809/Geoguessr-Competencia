/* Cosas que usan tanto el tablero como el celular. */

const BASE = location.origin + "/";

// Tiene que coincidir con lo que haya en tiles.db
const SAT_MIN = 16, SAT_MAX = 19;
const VT_MAX = 15;                 // de ahi para arriba MapLibre reescala
const CALLES_MIN = 11, CALLES_MAX = 18;
const METRO = [[-73.230, 7.020], [-73.040, 7.200]];

function estiloSatelite() {
  return {
    version: 8,
    sources: {
      sat: {
        type: "raster",
        tiles: [BASE + "tiles/sat/{z}/{x}/{y}.jpg"],
        tileSize: 256, minzoom: SAT_MIN, maxzoom: SAT_MAX,
        attribution: "Imágenes &copy; Esri (copia local)",
      },
    },
    layers: [{ id: "sat", type: "raster", source: "sat" }],
  };
}

function estiloCalles() {
  return {
    version: 8,
    glyphs: BASE + "vendor/fonts/{fontstack}/{range}.pbf",
    sprite: BASE + "vendor/sprites/light",
    sources: {
      protomaps: {
        type: "vector",
        tiles: [BASE + "tiles/vt/{z}/{x}/{y}.mvt"],
        minzoom: 0, maxzoom: VT_MAX,
        attribution: "&copy; OpenStreetMap (copia local)",
      },
    },
    // Ojo: el 2do argumento es el OBJETO del tema, no su nombre; con la cadena
    // "light" devuelve colores undefined y MapLibre descarta el estilo entero.
    layers: protomaps_themes_base.layers(
      "protomaps", protomaps_themes_base.namedTheme("light"), { lang: "es" }
    ),
  };
}

/* MapLibre fija el tamaño del canvas al construirse: si el navegador todavía no
   terminó el layout, el mapa queda recortado en una esquina. En el celular pasa
   seguido porque la barra del navegador cambia de alto. */
function crearMapa(contenedor, opciones) {
  const m = new maplibregl.Map(Object.assign({ container: contenedor }, opciones));
  m.resize();
  if (window.ResizeObserver) {
    new ResizeObserver(() => m.resize()).observe(document.getElementById(contenedor));
  }
  m.once("load", () => m.resize());
  window.addEventListener("orientationchange", () => setTimeout(() => m.resize(), 300));
  return m;
}

async function pedir(url) {
  const r = await fetch(url, { cache: "no-store" });
  return r.json();
}

async function enviar(url, datos) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos || {}),
  });
  return r.json();
}

function textoDistancia(km) {
  return km < 1 ? Math.round(km * 1000) + " m" : km.toFixed(2) + " km";
}

function escapar(t) {
  return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* Tarjeta central que aparece y se va sola. */
function mostrarPop(emoji, frase, detalle, color) {
  const d = document.createElement("div");
  d.className = "pop";
  d.style.border = "2px solid " + color;
  d.style.boxShadow = `0 0 40px ${color}55, 0 18px 50px rgba(0,0,0,.55)`;
  d.innerHTML = `<div class="emo">${emoji}</div>
                 <div class="frase" style="color:${color}">${escapar(frase)}</div>
                 <div class="det">${escapar(detalle)}</div>`;
  document.body.appendChild(d);
  setTimeout(() => d.remove(), 2800);
}

/* Sondeo: le pide el estado al servidor una vez por segundo y avisa cuando
   cambia la version. Un websocket seria mas fino, pero esto no necesita
   dependencias y en una red local no se nota la diferencia. */
function sondear(url, alCambiar, cada = 1000) {
  let ultima = -1;
  async function tic() {
    try {
      const e = await pedir(typeof url === "function" ? url() : url);
      if (e && e.version !== undefined && e.version !== ultima) {
        ultima = e.version;
        alCambiar(e, true);
      } else if (e) {
        alCambiar(e, false);
      }
    } catch (err) {
      /* el wifi se cayo un segundo: se reintenta en el proximo tic */
    }
    setTimeout(tic, cada);
  }
  tic();
}
