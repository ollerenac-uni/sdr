// Mostrar el destino de enlaces que apuntan al interior de una nota desplegable.
function mostrarDestinoDesplegable() {
  let id;
  try {
    id = decodeURIComponent(window.location.hash.slice(1));
  } catch {
    return;
  }
  if (!id) return;

  const destino = document.getElementById(id);
  if (!destino || !destino.closest(".md-content")) return;

  let nota = destino.closest("details");
  let abierta = false;
  while (nota) {
    if (!nota.open) {
      nota.open = true;
      abierta = true;
    }
    nota = nota.parentElement.closest("details");
  }
  if (abierta) {
    window.requestAnimationFrame(() => destino.scrollIntoView({ block: "start" }));
  }
}

document$.subscribe(mostrarDestinoDesplegable);
window.addEventListener("hashchange", mostrarDestinoDesplegable);
