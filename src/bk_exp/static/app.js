const characterStyles = {
  basquiat: { color: "#f0bf5f", symbol: "B" },
  whitman: { color: "#7bc8a4", symbol: "W" },
  biggie: { color: "#ef7c86", symbol: "B" },
  rbg: { color: "#9da9ff", symbol: "R" },
};
const sessionId = crypto.randomUUID();
const status = document.querySelector("#status");
const offersElement = document.querySelector("#offers");
const routeStopsElement = document.querySelector("#route-stops");
const researchResultsElement = document.querySelector("#research-results");
const crewResultElement = document.querySelector("#crew-result");
const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.openfreemap.org/styles/liberty",
  center: [-73.97, 40.68],
  zoom: 12,
});
map.addControl(new maplibregl.NavigationControl(), "top-right");
let userMarker;
let pointMarkers = [];
let activeCharacter = "basquiat";
let latestPosition = { latitude: 40.6826, longitude: -73.9754 };

function avatar(character) {
  const style = characterStyles[character];
  return `<svg class="avatar" viewBox="0 0 48 48" aria-label="${character} tour marker" role="img">
    <circle cx="24" cy="24" r="21" fill="${style.color}" stroke="#17181b" stroke-width="3"/>
    <circle cx="17" cy="21" r="3" fill="#17181b"/><circle cx="31" cy="21" r="3" fill="#17181b"/>
    <path d="M16 31 Q24 36 32 31" fill="none" stroke="#17181b" stroke-width="3" stroke-linecap="round"/>
    <text x="24" y="28" text-anchor="middle" fill="#17181b" font-size="15" font-weight="800">${style.symbol}</text>
  </svg>`;
}

function setRoute(points) {
  const route = {
    type: "Feature",
    geometry: { type: "LineString", coordinates: points.map((point) => [point.longitude, point.latitude]) },
  };
  if (map.getSource("route")) {
    map.getSource("route").setData(route);
    return;
  }
  map.addSource("route", { type: "geojson", data: route });
  map.addLayer({ id: "route", type: "line", source: "route", paint: { "line-color": "#f0bf5f", "line-width": 5, "line-opacity": .8 } });
}

function showPoints(points) {
  pointMarkers.forEach((marker) => marker.remove());
  pointMarkers = points.map((point) => new maplibregl.Marker({ color: characterStyles[point.character].color })
    .setLngLat([point.longitude, point.latitude])
    .setPopup(new maplibregl.Popup().setHTML(
      `<strong>${point.name}</strong><p>${point.description}</p><a target="_blank" rel="noreferrer" href="${point.source_url}">Read: ${point.source_title}</a>`
    ))
    .addTo(map));
}

function showRouteStops(points) {
  routeStopsElement.replaceChildren();
  const totalMinutes = points.reduce((total, point) => total + point.estimated_minutes, 0);
  const summary = document.createElement("p");
  summary.textContent = `${points.length} stops · about ${totalMinutes} minutes at the sites`;
  routeStopsElement.append(summary);
  points.forEach((point, index) => {
    const stop = document.createElement("article");
    stop.className = "stop";
    const number = document.createElement("span");
    number.className = "stop-number";
    number.textContent = `STOP ${index + 1}`;
    const name = document.createElement("strong");
    name.textContent = point.name;
    const detail = document.createElement("span");
    detail.textContent = point.description;
    const source = document.createElement("a");
    source.href = point.source_url;
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = `Source: ${point.source_title}`;
    stop.append(number, name, detail, source);
    stop.onclick = () => map.flyTo({ center: [point.longitude, point.latitude], zoom: 16 });
    routeStopsElement.append(stop);
  });
}

async function loadTour() {
  activeCharacter = document.querySelector("#character").value;
  const response = await fetch(`/api/tours/${activeCharacter}`);
  if (!response.ok) throw new Error("The selected route could not be loaded.");
  const tour = await response.json();
  showPoints(tour.all_points);
  showRouteStops(tour.primary_route);
  map.once("load", () => setRoute(tour.primary_route));
  if (map.loaded()) setRoute(tour.primary_route);
  const bounds = new maplibregl.LngLatBounds();
  tour.primary_route.forEach((point) => bounds.extend([point.longitude, point.latitude]));
  map.fitBounds(bounds, { padding: 90, maxZoom: 15 });
  status.textContent = `${tour.primary_route.length}-stop route loaded. Select a stop to focus it, then allow location access to move your character on the map.`;
}

async function recordFeedback(character, feedbackType) {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, character, feedback_type: feedbackType }),
  });
  if (!response.ok) throw new Error("Feedback could not be saved.");
  return response.json();
}

async function refreshCrossovers() {
  const response = await fetch("/api/crossovers/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId, primary_character: activeCharacter, ...latestPosition,
      remaining_minutes: 90, remaining_budget_usd: 20,
    }),
  });
  if (!response.ok) throw new Error("Crossover suggestions could not be evaluated.");
  const { offers } = await response.json();
  offersElement.replaceChildren();
  if (!offers.length) {
    offersElement.textContent = "No nearby crossover fits the current time budget.";
    return;
  }
  offers.slice(0, 2).forEach((offer) => {
    const card = document.createElement("article");
    card.className = "offer";
    card.innerHTML = `<strong>${offer.point.name}</strong><p>${offer.distance_meters}m away · +${offer.added_minutes} minutes · preserves your original route</p>`;
    const accept = document.createElement("button");
    accept.textContent = "Add crossover";
    accept.onclick = async () => {
      await recordFeedback(offer.point.character, "accepted");
      status.textContent = `Crossover saved. Your ${activeCharacter} route remains available.`;
      await refreshCrossovers();
    };
    const decline = document.createElement("button");
    decline.className = "secondary";
    decline.textContent = "Keep original route";
    decline.onclick = async () => {
      await recordFeedback(offer.point.character, "keep_original");
      status.textContent = "Preference learned. Your original route is unchanged.";
      await refreshCrossovers();
    };
    card.append(accept, decline);
    offersElement.append(card);
  });
}

async function refreshResearch() {
  const response = await fetch(`/api/research/${activeCharacter}`);
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || "Live research could not be completed.");
  researchResultsElement.replaceChildren();
  const notice = document.createElement("p");
  notice.textContent = result.review_required
    ? "Live findings are discovery evidence and require curator review before becoming route stops."
    : "Research findings are ready.";
  researchResultsElement.append(notice);
  if (!result.citations.length) {
    const empty = document.createElement("p");
    empty.textContent = "No usable citations were returned. Your vetted route is unchanged.";
    researchResultsElement.append(empty);
    return;
  }
  result.citations.forEach((citation) => {
    const item = document.createElement("article");
    item.className = "research-citation";
    const title = document.createElement("strong");
    title.textContent = citation.title;
    const snippet = document.createElement("p");
    snippet.textContent = citation.snippet;
    const source = document.createElement("a");
    source.href = citation.url;
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = "Open source";
    item.append(title, snippet, source);
    researchResultsElement.append(item);
  });
}

function updatePosition(position) {
  latestPosition = { latitude: position.coords.latitude, longitude: position.coords.longitude };
  if (!userMarker) {
    const element = document.createElement("div");
    element.innerHTML = avatar(activeCharacter);
    userMarker = new maplibregl.Marker({ element }).setLngLat([latestPosition.longitude, latestPosition.latitude]).addTo(map);
  } else {
    userMarker.setLngLat([latestPosition.longitude, latestPosition.latitude]);
  }
  refreshCrossovers().catch((error) => { status.textContent = error.message; });
}

document.querySelector("#start-tour").onclick = () => {
  loadTour().then(() => {
    refreshResearch().catch((error) => {
      researchResultsElement.textContent = error.message;
    });
    if ("geolocation" in navigator) {
      navigator.geolocation.watchPosition(updatePosition, () => {
        status.textContent = "Location is unavailable; displaying the selected Brooklyn route.";
      }, { enableHighAccuracy: true, maximumAge: 10_000 });
    }
  }).catch((error) => { status.textContent = error.message; });
};

document.querySelector("#research-tour").onclick = () => {
  activeCharacter = document.querySelector("#character").value;
  researchResultsElement.textContent = "Searching You.com for source-attributed Brooklyn context...";
  refreshResearch().catch((error) => {
    researchResultsElement.textContent = error.message;
  });
};

document.querySelector("#run-crew").onclick = async () => {
  activeCharacter = document.querySelector("#character").value;
  crewResultElement.textContent = "The four agents are researching and reviewing this route...";
  try {
    const response = await fetch("/api/crew/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ character: activeCharacter, remaining_minutes: 90, remaining_budget_usd: 20 }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "The crew run could not be completed.");
    await pollCrewRun(result.kickoff_id, result.research.citations.length);
  } catch (error) {
    crewResultElement.textContent = error.message;
  }
};

async function pollCrewRun(kickoffId, citationCount) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const response = await fetch(`/api/crew/runs/${encodeURIComponent(kickoffId)}`);
    const run = await response.json();
    if (!response.ok) throw new Error(run.detail || "The crew status could not be retrieved.");
    crewResultElement.textContent = `Crew status: ${run.status}. Live citations supplied: ${citationCount}.`;
    if (["completed", "failed", "cancelled"].includes(run.status.toLowerCase())) {
      if (run.result !== null) {
        const output = document.createElement("pre");
        output.textContent = typeof run.result === "string" ? run.result : JSON.stringify(run.result, null, 2);
        crewResultElement.append(output);
      }
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }
  throw new Error("Crew review is still running. Please check its status again shortly.");
}
