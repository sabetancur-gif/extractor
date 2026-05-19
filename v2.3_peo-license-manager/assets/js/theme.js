/* global PEO */
/* theme.js — manejo de tema claro / oscuro */
"use strict";

PEO.initTheme = function() {
  const saved = localStorage.getItem("peo-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  PEO.updateThemeIcon(saved);
};

PEO.toggleTheme = function() {
  const cur  = document.documentElement.getAttribute("data-theme") || "dark";
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("peo-theme", next);
  PEO.updateThemeIcon(next);
};

PEO.updateThemeIcon = function(theme) {
  const btn = document.getElementById("btnTheme");
  if (btn) btn.textContent = theme === "dark" ? "☀" : "🌙";
};
