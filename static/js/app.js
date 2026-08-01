const TMDB_IMG = "https://image.tmdb.org/t/p/w300";
const searchInput = document.getElementById("search-input");
const dropdown = document.getElementById("search-dropdown");

const SLIDERS = ["mood", "energy", "tension", "weight"];
let currentMovieId = null;
let debounceTimer;
let mixerTimer;

// --- Search ---

searchInput.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const q = searchInput.value.trim();
  if (q.length < 2) { dropdown.classList.remove("show"); return; }
  debounceTimer = setTimeout(() => searchMovies(q), 300);
});

async function searchMovies(q) {
  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
  const movies = await res.json();
  dropdown.innerHTML = "";
  if (!movies.length) {
    dropdown.innerHTML = '<div class="dropdown-item text-secondary">No results</div>';
    dropdown.classList.add("show");
    return;
  }
  movies.forEach(m => {
    const item = document.createElement("a");
    item.className = "dropdown-item d-flex align-items-center gap-2 py-2";
    item.href = "#";
    const year = m.release_date ? m.release_date.substring(0, 4) : "";
    item.innerHTML = `
      ${m.poster_path ? `<img src="${TMDB_IMG}${m.poster_path}" style="width:32px;border-radius:3px">` : ""}
      <div>
        <div>${m.title} ${year ? `<small class="text-secondary">(${year})</small>` : ""}</div>
        <small class="text-secondary">${m.genres || ""}</small>
      </div>`;
    item.addEventListener("click", e => { e.preventDefault(); selectMovie(m); });
    dropdown.appendChild(item);
  });
  dropdown.classList.add("show");
}

// --- Movie selection ---

async function selectMovie(movie) {
  dropdown.classList.remove("show");
  searchInput.value = movie.title;
  currentMovieId = movie.id;

  // Shrink hero
  document.getElementById("hero").style.minHeight = "auto";
  document.getElementById("hero").classList.remove("justify-content-center");
  document.getElementById("hero").classList.add("pt-4", "pb-3");

  // Show source movie banner
  const src = document.getElementById("source-movie");
  src.classList.remove("d-none");
  document.getElementById("source-poster").src = movie.poster_path ? TMDB_IMG + movie.poster_path : "";
  document.getElementById("source-title").textContent = movie.title;
  document.getElementById("source-genres").textContent = movie.genres || "";

  // Fetch related (no mixer params = use source movie defaults)
  document.getElementById("results").classList.remove("d-none");
  await fetchRelated();
}

// --- Mixer ---

SLIDERS.forEach(name => {
  const slider = document.getElementById(`mixer-${name}`);
  const valueEl = document.getElementById(`mixer-${name}-value`);
  slider.addEventListener("input", () => {
    valueEl.textContent = slider.value;
    clearTimeout(mixerTimer);
    mixerTimer = setTimeout(() => fetchRelated(), 400);
  });
});

function getMixerParams() {
  const params = new URLSearchParams();
  SLIDERS.forEach(name => {
    const slider = document.getElementById(`mixer-${name}`);
    if (!slider.disabled) {
      params.set(name, slider.value);
    }
  });
  return params.toString();
}

function setSliders(profile) {
  SLIDERS.forEach(name => {
    const slider = document.getElementById(`mixer-${name}`);
    const valueEl = document.getElementById(`mixer-${name}-value`);
    slider.value = profile[name];
    slider.disabled = false;
    valueEl.textContent = profile[name];
  });
}

// --- Fetch related ---

async function fetchRelated() {
  if (!currentMovieId) return;
  const params = getMixerParams();
  const url = `/api/related/${currentMovieId}${params ? "?" + params : ""}`;
  const res = await fetch(url);
  const data = await res.json();

  // Set sliders to source profile on first load (when sliders are still disabled)
  if (data.source_emotions && document.getElementById("mixer-mood").disabled) {
    setSliders(data.source_emotions);
  }

  renderRelated(data.related || []);
}

// --- Render ---

function renderRelated(movies) {
  const grid = document.getElementById("related-grid");
  const noMsg = document.getElementById("no-related");
  grid.innerHTML = "";
  if (!movies.length) { noMsg.classList.remove("d-none"); return; }
  noMsg.classList.add("d-none");
  movies.forEach(m => {
    const year = m.release_date ? m.release_date.substring(0, 4) : "";
    const genres = (m.genres || "").split(",").filter(Boolean);
    const col = document.createElement("div");
    col.className = "col-6 col-md-3 col-lg-2";
    col.innerHTML = `
      <div class="movie-card h-100">
        ${m.poster_path ? `<img src="${TMDB_IMG}${m.poster_path}" alt="${m.title}">` : '<div style="height:280px;background:#0f3460"></div>'}
        <div class="card-body">
          <div class="card-title">${m.title} ${year ? `<small class="text-secondary">(${year})</small>` : ""}</div>
          <div>${genres.map(g => `<span class="badge bg-secondary me-1">${g.trim()}</span>`).join("")}</div>
          ${m.vote_average ? `<small class="text-warning">${Number(m.vote_average).toFixed(1)}</small>` : ""}
        </div>
      </div>`;
    col.querySelector(".movie-card").addEventListener("click", () => selectMovie(m));
    grid.appendChild(col);
  });
}

// --- Reset ---

function resetSearch() {
  searchInput.value = "";
  currentMovieId = null;
  document.getElementById("hero").style.minHeight = "60vh";
  document.getElementById("hero").classList.add("justify-content-center");
  document.getElementById("hero").classList.remove("pt-4", "pb-3");
  document.getElementById("source-movie").classList.add("d-none");
  document.getElementById("results").classList.add("d-none");
  document.getElementById("related-grid").innerHTML = "";
  SLIDERS.forEach(name => {
    const slider = document.getElementById(`mixer-${name}`);
    slider.value = 50;
    slider.disabled = true;
    document.getElementById(`mixer-${name}-value`).textContent = "50";
  });
  searchInput.focus();
}

// Close dropdown on outside click
document.addEventListener("click", e => {
  if (!e.target.closest(".search-wrapper")) dropdown.classList.remove("show");
});
