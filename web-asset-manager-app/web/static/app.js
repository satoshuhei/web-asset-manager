document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-filter-target]").forEach((input) => {
    input.addEventListener("input", () => {
      const targetId = input.getAttribute("data-filter-target");
      const table = document.getElementById(targetId);
      if (!table) return;
      const query = input.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  });

  const dragItems = document.querySelectorAll(".draggable-asset");
  dragItems.forEach((item) => {
    item.addEventListener("dragstart", (event) => {
      const payload = {
        asset_type: item.dataset.assetType,
        asset_id: Number(item.dataset.assetId),
        source_config_id: item.dataset.sourceConfigId
          ? Number(item.dataset.sourceConfigId)
          : null,
      };
      event.dataTransfer.setData("application/json", JSON.stringify(payload));
      event.dataTransfer.effectAllowed = "move";
    });
  });

  const dropZones = document.querySelectorAll(".drop-zone");
  dropZones.forEach((zone) => {
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("drag-over");
      event.dataTransfer.dropEffect = "move";
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
    zone.addEventListener("drop", async (event) => {
      event.preventDefault();
      zone.classList.remove("drag-over");
      const raw = event.dataTransfer.getData("application/json");
      if (!raw) return;
      const payload = JSON.parse(raw);
      const configId = Number(zone.dataset.configId);
      const response = await fetch(`/api/configs/${configId}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        window.location.reload();
        return;
      }
      const data = await response.json();
      alert(data.detail || "Assign failed");
    });
  });

  const canvas = document.getElementById("config-canvas");
  if (canvas) {
    let activeCard = null;
    let offsetX = 0;
    let offsetY = 0;

    canvas.addEventListener("pointerdown", (event) => {
      const handle = event.target.closest(".drag-handle");
      if (!handle) return;
      const card = handle.closest(".config-card");
      if (!card) return;
      activeCard = card;
      const rect = card.getBoundingClientRect();
      offsetX = event.clientX - rect.left;
      offsetY = event.clientY - rect.top;
      card.setPointerCapture(event.pointerId);
      card.style.cursor = "grabbing";
    });

    canvas.addEventListener("pointermove", (event) => {
      if (!activeCard) return;
      const canvasRect = canvas.getBoundingClientRect();
      const x = event.clientX - canvasRect.left - offsetX;
      const y = event.clientY - canvasRect.top - offsetY;
      activeCard.style.left = `${Math.max(0, x)}px`;
      activeCard.style.top = `${Math.max(0, y)}px`;
    });

    canvas.addEventListener("pointerup", async (event) => {
      if (!activeCard) return;
      const card = activeCard;
      activeCard = null;
      card.style.cursor = "grab";
      const configId = card.dataset.configId;
      const x = parseFloat(card.style.left || "0");
      const y = parseFloat(card.style.top || "0");
      await fetch(`/api/configs/${configId}/position`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x, y }),
      });
    });
  }
});
