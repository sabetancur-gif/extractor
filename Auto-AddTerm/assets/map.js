(() => {
  console.log("[MAP] map.js cargado");

  const mapContainer = document.getElementById("mapContainer");
  const estadoSelect = document.getElementById("estado");

  if (!mapContainer) {
    console.error("[MAP] No existe #mapContainer");
    return;
  }

  if (!estadoSelect) {
    console.error("[MAP] No existe #estado");
    return;
  }

  function norm(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "_")
      .replace(/\\/g, "/");
  }

  function getSvgRoot() {
    return mapContainer.querySelector("svg");
  }

  function clearHighlights(svgDoc) {
    svgDoc.querySelectorAll('[id^="state-"]').forEach((node) => {
      node.style.fill = "";
      node.style.stroke = "";
      node.style.strokeWidth = "";
    });
  }

  function findTarget(svgDoc, stateName) {
    const wanted = norm(stateName);

    const candidates = [
      `state-${wanted}`,
      `state-${wanted.replace(/_/g, "-")}`,
      `state-${wanted.replace(/_/g, "")}`
    ];

    for (const id of candidates) {
      const node = svgDoc.getElementById(id);
      if (node) return node;
    }

    const all = [...svgDoc.querySelectorAll('[id^="state-"]')];
    return all.find((node) => {
      const dataName = norm(node.getAttribute("data-name"));
      const idName = norm(node.id.replace(/^state-/, ""));
      return dataName === wanted || idName === wanted;
    }) || null;
  }

  function setSelectedState(name) {
    const wanted = norm(name);
    const options = [...estadoSelect.options];
    const found = options.find(
      (o) => norm(o.value) === wanted || norm(o.textContent) === wanted
    );

    if (found) {
      estadoSelect.value = found.value;
      estadoSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function activate() {
    const svgDoc = getSvgRoot();

    if (!svgDoc) {
      console.warn("[MAP] Todavía no existe el SVG inline");
      return;
    }

    console.log("[MAP] SVG listo");

    const root = svgDoc;
    const originalViewBox = root.getAttribute("viewBox");

    const fitAll = () => {
      if (originalViewBox) root.setAttribute("viewBox", originalViewBox);
    };

    const update = () => {
      const stateName = estadoSelect.value;
      clearHighlights(svgDoc);

      if (!stateName || norm(stateName) === "todos") {
        fitAll();
        return;
      }

      const target = findTarget(svgDoc, stateName);

      console.log("[MAP] update:", {
        stateName,
        targetId: target?.id || null
      });

      if (!target) {
        fitAll();
        return;
      }

      const bbox = target.getBBox();
      const margin = 10;

      root.setAttribute(
        "viewBox",
        `${bbox.x - margin} ${bbox.y - margin} ${bbox.width + margin * 2} ${bbox.height + margin * 2}`
      );

      target.style.fill = "#f59e0b";
      target.style.stroke = "#1f2937";
      target.style.strokeWidth = "1.5";
    };

    estadoSelect.addEventListener("change", () => {
      requestAnimationFrame(update);
    });

    svgDoc.querySelectorAll('[id^="state-"]').forEach((node) => {
      node.style.cursor = "pointer";
      node.addEventListener("click", () => {
        const realName = node.getAttribute("data-name") || node.id.replace("state-", "").replace(/_/g, " ");
        setSelectedState(realName);
      });
    });

    update();

    window.Auto1Map = {
      setSelectedState
    };
  }

  const timer = setInterval(() => {
    if (getSvgRoot()) {
      clearInterval(timer);
      activate();
    }
  }, 100);

  window.addEventListener("load", () => {
    activate();
  });
})();