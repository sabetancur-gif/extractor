/* global PEO */
/* config.js — constantes de la aplicación */
"use strict";

window.PEO = window.PEO || {};

PEO.VERSION   = "v2.2";
PEO.DATA_SHEET = "Data";

PEO.DATE_CANDIDATES = [
  "4._date_of_change_or_termination", "effective_date", "date_of_change",
  "termination_date", "change_date", "date",
];

// Posición [fila, columna] de cada estado en el tile-grid (0-based)
PEO.TILE_GRID = {
  ME:[0,10], WA:[1,0], MT:[1,1], ND:[1,2], MN:[1,3], VT:[1,9],  NH:[1,10],
  OR:[2,0],  ID:[2,1], WY:[2,2], SD:[2,3], WI:[2,4], MI:[2,7],  NY:[2,8],  MA:[2,10],
  CA:[3,0],  NV:[3,1], UT:[3,2], CO:[3,3], NE:[3,4], IA:[3,5],  IL:[3,6],  IN:[3,7],  OH:[3,8], PA:[3,9], NJ:[3,10],
  AZ:[4,1],  NM:[4,2], KS:[4,3], MO:[4,4], KY:[4,5], WV:[4,6],  VA:[4,7],  MD:[4,8],  DE:[4,9], CT:[4,10],
  TX:[5,2],  OK:[5,3], AR:[5,4], TN:[5,5], NC:[5,6], SC:[5,7],  RI:[5,10],
  HI:[6,0],  LA:[6,3], MS:[6,4], AL:[6,5], GA:[6,6],
  AK:[7,0],  FL:[7,6],
};

PEO.ABBR_TO_NAME = {
  ME:"Maine",       WA:"Washington",    MT:"Montana",     ND:"North Dakota", MN:"Minnesota",
  VT:"Vermont",     NH:"New Hampshire", OR:"Oregon",      ID:"Idaho",        WY:"Wyoming",
  SD:"South Dakota",WI:"Wisconsin",     MI:"Michigan",    NY:"New York",     MA:"Massachusetts",
  CA:"California",  NV:"Nevada",        UT:"Utah",        CO:"Colorado",     NE:"Nebraska",
  IA:"Iowa",        IL:"Illinois",      IN:"Indiana",     OH:"Ohio",         PA:"Pennsylvania",
  NJ:"New Jersey",  AZ:"Arizona",       NM:"New Mexico",  KS:"Kansas",       MO:"Missouri",
  KY:"Kentucky",    WV:"West Virginia", VA:"Virginia",    MD:"Maryland",     DE:"Delaware",
  CT:"Connecticut", TX:"Texas",         OK:"Oklahoma",    AR:"Arkansas",     TN:"Tennessee",
  NC:"North Carolina", SC:"South Carolina", RI:"Rhode Island", HI:"Hawaii", LA:"Louisiana",
  MS:"Mississippi", AL:"Alabama",       GA:"Georgia",     AK:"Alaska",       FL:"Florida",
};

PEO.NAME_TO_ABBR = Object.fromEntries(
  Object.entries(PEO.ABBR_TO_NAME).map(([a, n]) => [n.toLowerCase(), a])
);

// ──── Lista de operadores ──── agrega o quita nombres aquí ────────────────────
// El carrusel siempre muestra 4 a la vez y rota circularmente.
PEO.OPERATORS = [
  "Mateo Bedoya",
  "Isabella Cano",
  "Paulina Montes",
  "Santiago Betancur"
]
