// Ubicaciones de la competencia.
// Sincronizadas con la version de un jugador (demo.py del repo Geoguessr-Santander).
// Es un .js y no un .json para poder cargarlo con <script> sin fetch.
const LOCATIONS_DATA =
{
  "_comment": "Sincronizadas con demo.py del repo Geoguessr-Santander. El que tiene pinned=true sale en la PRIMERA ronda si su ciudad esta en juego.",
  "locations": [
    {
      "name": "Institución Educativa Comuneros - Bucaramanga",
      "lat": 7.136007,
      "lon": -73.129005,
      "ciudad": "Bucaramanga",
      "pinned": true
    },
    {
      "name": "Parque del Agua",
      "lat": 7.130071,
      "lon": -73.109332,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Biblioteca UIS",
      "lat": 7.140988,
      "lon": -73.120911,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Estadio Américo Montanini",
      "lat": 7.136685,
      "lon": -73.116535,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque San Pio",
      "lat": 7.118566,
      "lon": -73.110505,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque de los niños",
      "lat": 7.12514,
      "lon": -73.119015,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Aeropuerto Palonegro",
      "lat": 7.127934,
      "lon": -73.18315,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque La Flora",
      "lat": 7.10859,
      "lon": -73.107533,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Centro Comercial el Cacique",
      "lat": 7.09929,
      "lon": -73.107281,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Centro Comercial Sandresito La Isla",
      "lat": 7.108622,
      "lon": -73.117683,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque las cigarras",
      "lat": 7.103767,
      "lon": -73.121245,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque San Francisco",
      "lat": 7.131202,
      "lon": -73.125035,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Club Campestre",
      "lat": 7.064437,
      "lon": -73.115783,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Estadio 1º de Mayo (UIS)",
      "lat": 7.140848,
      "lon": -73.118518,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Centro Comercial Megamall",
      "lat": 7.130462,
      "lon": -73.111979,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Centro Comercial Único Outlet",
      "lat": 7.087529,
      "lon": -73.121435,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "CentroAbastos",
      "lat": 7.103192,
      "lon": -73.167965,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Patinódromo Roberto García Peña",
      "lat": 7.105119,
      "lon": -73.125111,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Terminal de Transportes",
      "lat": 7.088619,
      "lon": -73.129394,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Hospital Universitario de Santander",
      "lat": 7.128156,
      "lon": -73.114088,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Plaza de Mercado Central",
      "lat": 7.119941,
      "lon": -73.126714,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Universidad de Santander - UDES",
      "lat": 7.105239,
      "lon": -73.095104,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Universidad Autónoma de Bucaramanga - UNAB",
      "lat": 7.114879,
      "lon": -73.105254,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque Centenario",
      "lat": 7.12192,
      "lon": -73.12464,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque García Rovira",
      "lat": 7.116919,
      "lon": -73.130079,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Parque Metropolitano Bosque Encantado",
      "lat": 7.125085,
      "lon": -73.106955,
      "ciudad": "Bucaramanga"
    },
    {
      "name": "Refinería de Ecopetrol",
      "lat": 7.067004,
      "lon": -73.8787,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Estadio Daniel Villa Zapata",
      "lat": 7.073121,
      "lon": -73.864679,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Aeropuerto Yariguíes",
      "lat": 7.024453,
      "lon": -73.806945,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Estadio Villa Juventud",
      "lat": 7.07001,
      "lon": -73.839888,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Plaza de Mercado Central de Barrancabermeja",
      "lat": 7.06044,
      "lon": -73.870557,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Centro Comercial San Silvestre",
      "lat": 7.067349,
      "lon": -73.858099,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Hospital Regional del Magdalena Medio",
      "lat": 7.068023,
      "lon": -73.861331,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Parque Infantil",
      "lat": 7.058972,
      "lon": -73.860983,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Instituto Técnico Superior Industrial",
      "lat": 7.064227,
      "lon": -73.851174,
      "ciudad": "Barrancabermeja"
    },
    {
      "name": "Universidad Industrial de Santander - Sede Barrancabermeja",
      "lat": 7.069798,
      "lon": -73.851447,
      "ciudad": "Barrancabermeja"
    }
  ]
};
