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
  $("qr").innerHTML = q.createImgTag(8, 0);
  $("url").textContent = url.replace(/^https?:\/\//, "");
}

/* Con tunel entran por internet desde donde sea, asi que pedirles que se
   conecten a una wifi sobra y encima confunde. */
function pintarPasos(modo) {
  const pasos = modo === "tunel"
    ? ["Abre la cámara del celular",
       "Apunta al <b>código QR</b>",
       "Escribe tu nombre y espera"]
    : ["Conéctate al <b>wifi del salón</b>",
       "Apunta la cámara al <b>código QR</b>",
       "Escribe tu nombre y espera"];
  $("pasos").innerHTML = pasos.map((t, i) => `${i + 1}. ${t}`).join("<br />");
}

/* Durante la ronda no se muestran puntos: solo quien ya respondio. Si fueran
   apareciendo, el que todavia no responde ve quien acerto. */
function pintarTabla(destino, tabla, ocultarPuntos, conExpulsar) {
  $(destino).innerHTML = tabla.map((f) =>
    `<tr><td class="pos">${f.puesto}</td><td>${escapar(f.nombre)}</td>` +
    `<td class="pts">${ocultarPuntos
        ? (f.respondio ? '<span style="color:var(--verde)">✓</span>'
                       : '<span style="opacity:.35">…</span>')
        : f.puntaje}</td>` +
    (conExpulsar ? `<td class="quitar"><button class="equis" data-id="${f.id}"
         title="Sacar a ${escapar(f.nombre)}">✕</button></td>` : "") +
    `</tr>`
  ).join("") || '<tr><td style="opacity:.5">Sin jugadores</td></tr>';
  if (conExpulsar) cablearExpulsar($(destino));
}

/* Ningun filtro de nombres atrapa todo, asi que el profesor tiene que poder
   sacar a alguien en el momento. */
function cablearExpulsar(raiz) {
  raiz.querySelectorAll("button.equis").forEach((b) => {
    b.onclick = () => enviar(api("/api/expulsar"), { id: b.dataset.id });
  });
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
    prepararAjustes(e);
    if (cambio) {
      $("chips").innerHTML = e.tabla.map((f) =>
        `<div class="chip">${escapar(f.nombre)}` +
        `<button class="equis" data-id="${f.id}" title="Sacar a ${escapar(f.nombre)}">✕</button>` +
        `</div>`).join("");
      cablearExpulsar($("chips"));
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
    pintarTabla("tablaFinal", e.tabla, false);
  }

  if (e.fase === "ronda" || e.fase === "resultados") {
    pintarTabla("tabla", e.tabla, !!e.ocultar_puntos, true);
  }
  ronda = e.ronda;
  fase = e.fase;
}

/* Ajustes de la partida. Van en el tablero y no en el celular a proposito:
   esta pantalla vive en una URL con codigo, asi que solo la ve el profesor. */
let ajustesListos = false;

function prepararAjustes(e) {
  const sr = $("selRondas"), ss = $("selSegundos");
  if (!ajustesListos && e.max_rondas) {
    const opciones = [3, 5, 8, 10, 12, 15, 20, e.max_rondas]
      .filter((n, i, a) => n <= e.max_rondas && a.indexOf(n) === i)
      .sort((a, b) => a - b);
    sr.innerHTML = opciones.map((n) =>
      `<option value="${n}">${n} rondas${n === e.max_rondas ? " (todas)" : ""}</option>`).join("");
    sr.value = String(e.rondas_totales);
    ss.value = String(e.segundos_ronda);
    const guardar = () => enviar(api("/api/config"),
      { rondas: +sr.value, segundos: +ss.value });
    sr.onchange = guardar;
    ss.onchange = guardar;
    ajustesListos = true;
  }
  const mins = Math.round((+$("selRondas").value * (+$("selSegundos").value + 20)) / 60);
  $("notaRondas").textContent =
    `Máximo ${e.max_rondas} rondas: no se repite lugar. ` +
    `Esta partida dura unos ${mins} minutos contando los resultados.`;
}

$("btnEmpezar").onclick = () => enviar(api("/api/empezar"));
$("btnOtra").onclick = () => enviar(api("/api/reiniciar"));

pedir(api("/api/host")).then((e) => {
  if (e.url_jugar) pintarQR(e.url_jugar);
  pintarPasos(e.modo);
  sondear(() => api("/api/host"), render);
});
