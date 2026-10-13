/* Tablero del proyector. */

const TOKEN = location.pathname.split("/")[2] || "";
const api = (r) => r + (r.includes("?") ? "&" : "?") + "token=" + encodeURIComponent(TOKEN);

// La pista arranca muy cerca y se va abriendo sola a medida que corre el
// tiempo. Asi el que decide rapido ve menos y arriesga mas, que es lo que le
// da gracia a la competencia.
const ZOOMS = [19, 18, 17, 16];

let mapa = null, modoMapa = null, marcas = [], fase = null, ronda = null, zoomActual = null;

function $(id) { return document.getElementById(id); }

function limpiarMarcas() {
  marcas.forEach((m) => m.remove());
  marcas = [];
}

function destruirMapa() {
  limpiarMarcas();
  if (mapa) { mapa.remove(); mapa = null; }
  modoMapa = null;
  zoomActual = null;
}

function mmss(s) {
  s = Math.max(0, Math.round(s));
  return String(Math.floor(s / 60)) + ":" + String(s % 60).padStart(2, "0");
}

// --------------------------------------------------------------------------
function pintarQR(url) {
  const q = qrcode(0, "M");
  q.addData(url);
  q.make();
  $("qr").innerHTML = q.createImgTag(9, 0);
  $("url").textContent = url.replace(/^https?:\/\//, "");
}

function pintarTabla(tabla) {
  $("tabla").innerHTML = tabla.map((f) =>
    `<tr><td class="pos">${f.puesto}</td><td>${escapar(f.nombre)}</td>` +
    `<td class="pts">${f.puntaje}</td></tr>`
  ).join("") || '<tr><td style="opacity:.5">Sin jugadores</td></tr>';
}

function pintarPodio(tabla) {
  const medallas = ["🥇", "🥈", "🥉"];
  const altura = [0, 26, 44];
  $("podio").innerHTML = [1, 0, 2].map((i) => {
    const f = tabla[i];
    if (!f) return "";
    return `<div class="puesto" style="margin-bottom:${altura[i]}px">
        <div class="caja">
          <div class="medalla">${medallas[i]}</div>
          <div class="nom">${escapar(f.nombre)}</div>
          <div class="pts">${f.puntaje} puntos</div>
        </div></div>`;
  }).join("");
}

// --------------------------------------------------------------------------
function mapaPista(e) {
  const centro = [e.pista.lon, e.pista.lat];
  const transcurrido = 1 - e.restante / e.segundos_ronda;
  const z = ZOOMS[Math.min(ZOOMS.length - 1, Math.floor(transcurrido * ZOOMS.length))];

  if (modoMapa !== "sat" || ronda !== e.ronda) {
    destruirMapa();
    mapa = crearMapa("mapa", {
      style: estiloSatelite(), center: centro, zoom: z,
      interactive: false, attributionControl: { compact: true },
    });
    modoMapa = "sat";
    zoomActual = z;
  } else if (z !== zoomActual) {
    zoomActual = z;
    mapa.easeTo({ zoom: z, duration: 900 });
  }
  $("mira").style.display = "block";
}

function mapaSolucion(e) {
  destruirMapa();
  mapa = crearMapa("mapa", {
    style: estiloCalles(),
    center: [e.solucion.lon, e.solucion.lat], zoom: 14,
    minZoom: CALLES_MIN, maxZoom: CALLES_MAX,
    attributionControl: { compact: true },
  });
  modoMapa = "calles";
  $("mira").style.display = "none";

  mapa.on("load", () => {
    marcas.push(new maplibregl.Marker({ color: "#e53e3e" })
      .setLngLat([e.solucion.lon, e.solucion.lat])
      .setPopup(new maplibregl.Popup().setText(e.solucion.nombre))
      .addTo(mapa));

    const puntos = [[e.solucion.lon, e.solucion.lat]];
    (e.marcas || []).forEach((m) => {
      const el = document.createElement("div");
      el.textContent = m.nombre;
      el.style.cssText =
        "background:#2b6cb0;color:#fff;font-size:12px;font-weight:700;padding:3px 8px;" +
        "border-radius:999px;border:2px solid #fff;white-space:nowrap;box-shadow:0 2px 6px #0008";
      marcas.push(new maplibregl.Marker({ element: el }).setLngLat([m.lon, m.lat]).addTo(mapa));
      puntos.push([m.lon, m.lat]);
    });

    if (puntos.length > 1) {
      const lons = puntos.map((p) => p[0]), lats = puntos.map((p) => p[1]);
      mapa.fitBounds(
        [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]],
        { padding: 90, maxZoom: 16, duration: 0 }
      );
    }
  });
}

// --------------------------------------------------------------------------
function render(e, cambio) {
  // reloj y barra
  if (e.fase === "ronda") {
    $("reloj").textContent = mmss(e.restante);
    $("reloj").classList.toggle("poco", e.restante <= 10);
    $("cuenta").textContent = `${e.respondieron} de ${e.jugadores} respondieron`;
    $("barra").style.display = "block";
    $("barra").classList.toggle("poco", e.restante <= 10);
    $("barra").querySelector("i").style.width =
      Math.max(0, (e.restante / e.segundos_ronda) * 100) + "%";
  } else {
    $("reloj").textContent = "";
    $("cuenta").textContent = "";
    $("barra").style.display = "none";
  }

  if (e.fase !== "lobby") {
    $("sub").textContent = `Ronda ${e.ronda} de ${e.rondas_totales}`;
  }

  $("vLobby").style.display = e.fase === "lobby" ? "flex" : "none";
  $("vJuego").style.display = (e.fase === "ronda" || e.fase === "resultados") ? "flex" : "none";
  $("vFinal").style.display = e.fase === "final" ? "flex" : "none";

  if (e.fase === "lobby") {
    if (modoMapa) destruirMapa();
    $("nJug").textContent = e.jugadores;
    $("btnEmpezar").disabled = e.jugadores === 0;
    if (cambio) {
      $("chips").innerHTML = e.tabla.map((f) => `<div class="chip">${escapar(f.nombre)}</div>`).join("");
    }
  }

  if (e.fase === "ronda") {
    if (e.pista) mapaPista(e);
    $("cajaInfo").innerHTML =
      `<div style="font-size:22px;font-weight:700">¿Dónde es esto?</div>
       <div style="margin-top:8px;color:var(--texto2)">
         Marca en tu celular. Mientras más rápido, más puntos.<br>
         La foto se va alejando sola.
       </div>`;
    $("btnAccion").textContent = "Cerrar ronda ya";
    $("btnAccion").onclick = () => enviar(api("/api/cerrar"));
  }

  if (e.fase === "resultados" && (cambio || modoMapa !== "calles")) {
    mapaSolucion(e);
  }
  if (e.fase === "resultados") {
    const mejor = (e.marcas || []).slice().sort((a, b) => b.puntos - a.puntos)[0];
    $("cajaInfo").innerHTML =
      `<div style="font-size:15px;opacity:.7">Era</div>
       <div style="font-size:25px;font-weight:800;color:var(--verde)">${escapar(e.solucion.nombre)}</div>` +
      (mejor ? `<div style="margin-top:10px">Más cerca: <b>${escapar(mejor.nombre)}</b>
                 — ${textoDistancia(mejor.km)}</div>` : "") +
      `<div style="margin-top:6px;color:var(--texto2)">${(e.marcas || []).length} de ${e.jugadores} respondieron</div>`;
    $("btnAccion").textContent =
      e.ronda >= e.rondas_totales ? "Ver podio" : "Siguiente ronda";
    $("btnAccion").onclick = () => enviar(api("/api/siguiente"));
  }

  if (e.fase === "final" && cambio) {
    destruirMapa();
    pintarPodio(e.tabla);
  }

  if (e.fase !== "lobby") pintarTabla(e.tabla);
  ronda = e.ronda;
  fase = e.fase;
}

$("btnEmpezar").onclick = () => enviar(api("/api/empezar"));
$("btnOtra").onclick = () => enviar(api("/api/reiniciar"));

pedir(api("/api/host")).then((e) => {
  if (e.url_jugar) pintarQR(e.url_jugar);
  sondear(() => api("/api/host"), render);
});
