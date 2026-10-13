/* Pantalla del celular. */

// El id se guarda en el celular: si se recarga la pagina o se corta el wifi,
// el jugador vuelve a entrar con su mismo puntaje en vez de empezar de cero.
let miId = localStorage.getItem("geoId");
if (!miId) {
  miId = Math.random().toString(36).slice(2) + Date.now().toString(36);
  localStorage.setItem("geoId", miId);
}

let mapa = null, marca = null, miGuess = null, rondaActual = null, popDe = null;

function $(id) { return document.getElementById(id); }
function ver(id, mostrar, display) {
  $(id).style.display = mostrar ? (display || "flex") : "none";
}

function mmss(s) {
  s = Math.max(0, Math.round(s));
  return String(Math.floor(s / 60)) + ":" + String(s % 60).padStart(2, "0");
}

// --------------------------------------------------------------------------
function prepararMapa() {
  if (mapa) return;
  mapa = crearMapa("mapa", {
    style: estiloCalles(),
    center: [-73.123, 7.119], zoom: 12,
    minZoom: CALLES_MIN, maxZoom: CALLES_MAX,
    maxBounds: METRO,
    attributionControl: false,
  });
  mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  mapa.on("click", (ev) => {
    if ($("btnConfirmar").dataset.enviado === "1") return;
    miGuess = [ev.lngLat.lng, ev.lngLat.lat];
    if (marca) marca.remove();
    marca = new maplibregl.Marker({ color: "#2b6cb0", draggable: true })
      .setLngLat(miGuess).addTo(mapa);
    marca.on("dragend", () => {
      const p = marca.getLngLat();
      miGuess = [p.lng, p.lat];
    });
    $("btnConfirmar").disabled = false;
    $("aviso").textContent = "Puedes moverlo. Confirma cuando estés seguro";
  });
}

function nuevaRonda() {
  miGuess = null;
  if (marca) { marca.remove(); marca = null; }
  const b = $("btnConfirmar");
  b.disabled = true;
  b.dataset.enviado = "0";
  b.textContent = "Confirmar";
  $("aviso").style.display = "block";
  $("aviso").textContent = "Toca el mapa donde crees que es";
  if (mapa) mapa.easeTo({ center: [-73.123, 7.119], zoom: 12, duration: 400 });
}

async function confirmar() {
  if (!miGuess) return;
  const b = $("btnConfirmar");
  b.dataset.enviado = "1";
  b.disabled = true;
  b.textContent = "Enviado ✓";
  $("aviso").textContent = "Respuesta enviada. Espera a los demás…";
  if (marca) marca.setDraggable(false);
  await enviar("/api/responder", { id: miId, lat: miGuess[1], lon: miGuess[0] });
}

// --------------------------------------------------------------------------
function render(e, cambio) {
  if (!e.unido) {
    ver("vEntrar", true); ver("vEspera", false); ver("vJuego", false);
    ver("pieJuego", false, "block"); ver("vResultado", false); ver("vFinal", false);
    $("izq").textContent = "";
    $("reloj").textContent = "";
    $("barra").style.display = "none";
    return;
  }

  $("izq").innerHTML = (e.fase === "lobby")
    ? `${escapar(e.nombre)} · ${e.jugadores} conectados`
    : `${escapar(e.nombre)} · ${e.puntaje} pts · ronda ${e.ronda}/${e.rondas_totales}`;

  if (e.fase === "ronda") {
    $("reloj").textContent = mmss(e.restante);
    $("reloj").classList.toggle("poco", e.restante <= 10);
    $("barra").style.display = "block";
    $("barra").classList.toggle("poco", e.restante <= 10);
    $("barra").querySelector("i").style.width =
      Math.max(0, (e.restante / e.segundos_ronda) * 100) + "%";
  } else {
    $("reloj").textContent = "";
    $("barra").style.display = "none";
  }

  const jugando = e.fase === "ronda";
  ver("vEntrar", false);
  ver("vEspera", e.fase === "lobby");
  ver("vJuego", jugando);
  ver("pieJuego", jugando, "block");
  ver("vResultado", e.fase === "resultados");
  ver("vFinal", e.fase === "final");

  if (jugando) {
    prepararMapa();
    if (rondaActual !== e.ronda) {
      rondaActual = e.ronda;
      nuevaRonda();
      setTimeout(() => mapa && mapa.resize(), 60);
    }
    if (e.respondio && $("btnConfirmar").dataset.enviado !== "1") {
      $("btnConfirmar").dataset.enviado = "1";
      $("btnConfirmar").disabled = true;
      $("btnConfirmar").textContent = "Enviado ✓";
    }
  }

  if (e.fase === "resultados") {
    const r = e.mi_resultado;
    $("resuCaja").innerHTML = r
      ? `<div style="font-size:52px">${r.emoji}</div>
         <div class="grande" style="color:${r.color}">${escapar(r.frase)}</div>
         <div style="margin-top:10px"><b>${r.puntos}</b> puntos</div>
         <div class="chico">Te faltaron ${textoDistancia(r.km)} · respondiste en ${r.segundos}s</div>
         <div class="chico" style="margin-top:10px">Era: <b>${escapar(e.solucion.nombre)}</b></div>
         <div class="chico">Vas de ${e.mi_puesto}º con ${e.puntaje} puntos</div>`
      : `<div style="font-size:52px">⌛</div>
         <div class="grande">No alcanzaste a responder</div>
         <div class="chico" style="margin-top:10px">Era: <b>${escapar(e.solucion.nombre)}</b></div>`;
    $("tablaMini").innerHTML = (e.tabla || []).map((f) =>
      `<tr class="${f.nombre === e.nombre ? "yo" : ""}"><td class="pos">${f.puesto}</td>` +
      `<td>${escapar(f.nombre)}</td><td class="pts">${f.puntaje}</td></tr>`).join("");

    if (cambio && r && popDe !== e.ronda) {
      popDe = e.ronda;
      mostrarPop(r.emoji, r.frase, `${r.puntos} puntos · ${textoDistancia(r.km)}`, r.color);
      if (navigator.vibrate) navigator.vibrate(r.km <= 0.15 ? [40, 60, 120] : 40);
    }
  }

  if (e.fase === "final" && cambio) {
    const pos = e.mi_puesto;
    $("finMedalla").textContent = pos === 1 ? "🥇" : pos === 2 ? "🥈" : pos === 3 ? "🥉" : "🏁";
    $("finTexto").innerHTML =
      `Quedaste <b>${pos}º</b><br><span class="chico">${e.puntaje} puntos</span>`;
    $("tablaFinal").innerHTML = (e.tabla || []).map((f) =>
      `<tr class="${f.nombre === e.nombre ? "yo" : ""}"><td class="pos">${f.puesto}</td>` +
      `<td>${escapar(f.nombre)}</td><td class="pts">${f.puntaje}</td></tr>`).join("");
  }

  if (e.fase === "lobby") {
    $("miNombre").textContent = e.nombre;
    rondaActual = null;
  }
}

// --------------------------------------------------------------------------
async function entrar() {
  const nombre = $("nombre").value.trim();
  if (!nombre) { $("nombre").focus(); return; }
  $("btnEntrar").disabled = true;
  const r = await enviar("/api/unirse", { id: miId, nombre });
  $("btnEntrar").disabled = false;
  if (r.error) { $("errorEntrar").textContent = r.error; return; }
  localStorage.setItem("geoId", r.id);
  miId = r.id;
}

$("btnEntrar").onclick = entrar;
$("nombre").addEventListener("keydown", (ev) => { if (ev.key === "Enter") entrar(); });
$("btnConfirmar").onclick = confirmar;

sondear(() => "/api/jugador?id=" + encodeURIComponent(miId), render);
