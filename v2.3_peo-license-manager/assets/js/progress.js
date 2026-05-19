/* global PEO */
/* progress.js — overlay de progreso durante generación batch */
"use strict";

PEO.showProgress = function(title, total) {
  const ov = document.getElementById("progressOverlay");
  document.getElementById("progressTitle").textContent = title;
  document.getElementById("progressSub").textContent   = "Please wait…";
  document.getElementById("progressFill").style.width  = "0%";
  document.getElementById("progressCount").textContent = `0 / ${total}`;
  if (ov) ov.classList.add("open");
};

PEO.updateProgress = function(done, total, sub) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  document.getElementById("progressFill").style.width  = pct + "%";
  document.getElementById("progressCount").textContent = `${done} / ${total}`;
  if (sub) document.getElementById("progressSub").textContent = sub;
};

PEO.hideProgress = function() {
  const ov = document.getElementById("progressOverlay");
  if (ov) ov.classList.remove("open");
};
