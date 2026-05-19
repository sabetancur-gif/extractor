/* global PEO */
/* canvas.js — animaciones de fondo (Conway's Game of Life) */
"use strict";

// Animación de pantalla de carga (canvas grande, celda 10px)
PEO.startLoadCA = function(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return () => {};

  let raf, running = true;
  const CELL = 10;

  function resize() {
    canvas.width  = canvas.offsetWidth  || window.innerWidth;
    canvas.height = canvas.offsetHeight || window.innerHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  const COLS = () => Math.floor(canvas.width  / CELL);
  const ROWS = () => Math.floor(canvas.height / CELL);

  let grid = [], age = [];

  function init() {
    const cols = COLS(), rows = ROWS();
    grid = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => Math.random() < 0.3 ? 1 : 0)
    );
    age = Array.from({ length: rows }, () => new Array(cols).fill(0));
  }
  init();

  function step() {
    const cols = COLS(), rows = ROWS();
    if (grid.length !== rows || (grid[0] && grid[0].length !== cols)) { init(); return; }
    const next    = Array.from({ length: rows }, () => new Array(cols).fill(0));
    const nextAge = Array.from({ length: rows }, () => new Array(cols).fill(0));
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        let n = 0;
        for (let dr = -1; dr <= 1; dr++) {
          for (let dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            n += grid[(r + dr + rows) % rows]?.[(c + dc + cols) % cols] ?? 0;
          }
        }
        const alive = grid[r][c];
        if (alive && (n === 2 || n === 3)) { next[r][c] = 1; nextAge[r][c] = (age[r][c] || 0) + 1; }
        else if (!alive && n === 3)        { next[r][c] = 1; nextAge[r][c] = 0; }
      }
    }
    const pop = next.flat().reduce((s, v) => s + v, 0);
    if (pop < COLS() * ROWS() * 0.02) init();
    else { grid = next; age = nextAge; }
  }

  const ctx = canvas.getContext("2d");
  let frame = 0;

  function draw() {
    if (!running) return;
    if (frame % 12 === 0) step();
    frame++;
    const dark = document.documentElement.getAttribute("data-theme") !== "light";
    const cols = COLS(), rows = ROWS();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = dark ? "#0d1117" : "#f0f2f5";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.globalAlpha = 0.07;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (!grid[r]?.[c]) continue;
        const a = age[r][c] || 0;
        const pct = Math.min(a / 40, 1);
        const hue = dark ? 200 + pct * 80 : 210 + pct * 60;
        const sat = dark ? 80 : 70;
        const lit = dark ? 55 + (1 - pct) * 20 : 45 + (1 - pct) * 15;
        ctx.fillStyle = `hsl(${hue},${sat}%,${lit}%)`;
        ctx.fillRect(c * CELL + 1, r * CELL + 1, CELL - 2, CELL - 2);
      }
    }
    ctx.globalAlpha = 1.0;
    raf = requestAnimationFrame(draw);
  }
  draw();
  return () => { running = false; cancelAnimationFrame(raf); };
};

// Animación del header (franja delgada, celda 5px)
PEO.startHeaderCA = function(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const CELL = 5;

  function resize() {
    const header  = canvas.closest(".site-header");
    canvas.width  = header ? header.offsetWidth  : window.innerWidth;
    canvas.height = header ? header.offsetHeight : 52;
  }
  resize();
  window.addEventListener("resize", resize);

  const COLS = () => Math.floor(canvas.width  / CELL);
  const ROWS = () => Math.max(1, Math.floor(canvas.height / CELL));

  let grid = [];
  function init() {
    grid = Array.from({ length: ROWS() }, () =>
      Array.from({ length: COLS() }, () => Math.random() < 0.25 ? 1 : 0)
    );
  }
  init();

  function step() {
    const cols = COLS(), rows = ROWS();
    const next = Array.from({ length: rows }, () => new Array(cols).fill(0));
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        let n = 0;
        for (let dr = -1; dr <= 1; dr++)
          for (let dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            n += grid[(r + dr + rows) % rows]?.[(c + dc + cols) % cols] ?? 0;
          }
        if (grid[r][c] && (n === 2 || n === 3)) next[r][c] = 1;
        else if (!grid[r][c] && n === 3)         next[r][c] = 1;
      }
    }
    const pop = next.flat().reduce((s, v) => s + v, 0);
    if (pop < COLS() * ROWS() * 0.05) init(); else grid = next;
  }

  const ctx = canvas.getContext("2d");
  let frame = 0;
  (function loop() {
    if (frame % 6 === 0) step(); frame++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const dark = document.documentElement.getAttribute("data-theme") !== "light";
    const rows = ROWS(), cols = COLS();
    for (let r = 0; r < rows; r++)
      for (let c = 0; c < cols; c++)
        if (grid[r]?.[c]) {
          ctx.fillStyle = dark ? "rgba(88,166,255,0.6)" : "rgba(26,111,191,0.35)";
          ctx.fillRect(c * CELL + 1, r * CELL + 1, CELL - 2, CELL - 2);
        }
    requestAnimationFrame(loop);
  })();
};
