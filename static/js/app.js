const TMDB_IMG = "https://image.tmdb.org/t/p/w300";
const searchInput = document.getElementById("search-input");
const dropdown = document.getElementById("search-dropdown");

const SLIDERS = ["mood", "energy", "tension", "weight"];
let currentMovieId = null;
let currentMovieTitle = "";
let debounceTimer;
let mixerTimer;
let lastRelatedMovies = [];

function trackEvent(name) {
  if (window.goatcounter) goatcounter.count({ path: name, title: name, event: true });
}

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
  currentMovieTitle = movie.title;

  // Hide subtitle when movie selected
  document.querySelector("#hero p").classList.add("d-none");

  // Show source movie banner
  const src = document.getElementById("source-movie");
  src.classList.remove("d-none");
  document.getElementById("source-poster").src = movie.poster_path ? TMDB_IMG + movie.poster_path : "";
  document.getElementById("source-title").textContent = movie.title;
  document.getElementById("source-genres").textContent = movie.genres || "";

  // Reset sliders so fetchRelated uses source movie defaults
  SLIDERS.forEach(name => {
    document.getElementById(`mixer-${name}`).disabled = true;
  });

  document.getElementById("results").classList.remove("d-none");
  trackEvent("search-select");
  await fetchRelated();
}

// --- Mixer ---

SLIDERS.forEach(name => {
  const slider = document.getElementById(`mixer-${name}`);
  const valueEl = document.getElementById(`mixer-${name}-value`);
  slider.addEventListener("input", () => {
    valueEl.textContent = slider.value;
    clearTimeout(mixerTimer);
    mixerTimer = setTimeout(() => { trackEvent("mixer-use"); fetchRelated(); }, 400);
  });
});

document.getElementById("exclude-title").addEventListener("change", () => renderFiltered());
document.getElementById("year-from").addEventListener("input", () => renderFiltered());
document.getElementById("year-to").addEventListener("input", () => renderFiltered());

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
  document.getElementById("exclude-title").disabled = false;
  document.getElementById("year-from").disabled = false;
  document.getElementById("year-to").disabled = false;
}

// --- Fetch related ---

async function fetchRelated() {
  if (!currentMovieId) return;
  const grid = document.getElementById("related-grid");
  grid.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-secondary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
  document.getElementById("no-related").classList.add("d-none");

  const params = getMixerParams();
  const url = `/api/related/${currentMovieId}${params ? "?" + params : ""}`;
  const res = await fetch(url);
  const data = await res.json();

  // Set sliders to source profile on first load (when sliders are still disabled)
  if (data.source_emotions && document.getElementById("mixer-mood").disabled) {
    setSliders(data.source_emotions);
  }

  lastRelatedMovies = data.related || [];
  renderFiltered();
}

function renderFiltered() {
  let filtered = lastRelatedMovies;

  if (document.getElementById("exclude-title").checked) {
    const stopWords = new Set(["the","a","an","and","or","of","in","on","at","to","for","is","it","by","from","with","as","but","not","no","be","was","are","were","been","do","does","did","has","have","had","this","that","its","into","than","up","out","all","one","two"]);
    const words = currentMovieTitle.toLowerCase().split(/\s+/).filter(w => w.length > 2 && !stopWords.has(w));
    filtered = filtered.filter(m => {
      const t = m.title.toLowerCase();
      return !words.some(w => t.includes(w));
    });
  }

  const yearFrom = parseInt(document.getElementById("year-from").value);
  const yearTo = parseInt(document.getElementById("year-to").value);
  if (yearFrom || yearTo) {
    filtered = filtered.filter(m => {
      const year = m.release_date ? parseInt(m.release_date.substring(0, 4)) : null;
      if (!year) return false;
      if (yearFrom && year < yearFrom) return false;
      if (yearTo && year > yearTo) return false;
      return true;
    });
  }

  renderRelated(filtered);
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
    const col = document.createElement("div");
    col.className = "col-6 col-sm-4 col-lg-3";
    col.innerHTML = `
      <div class="movie-card h-100">
        ${m.poster_path ? `<img src="${TMDB_IMG}${m.poster_path}" alt="${m.title}">` : '<div class="no-poster d-flex align-items-center justify-content-center"><svg width="40" height="40" fill="#555" viewBox="0 0 16 16"><path d="M0 1a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H1a1 1 0 0 1-1-1V1zm4 0v6l2-1 2 1V1H4z"/></svg></div>'}
        <div class="card-body">
          <div class="card-title">${m.title} ${year ? `<small class="text-secondary">(${year})</small>` : ""}</div>
        </div>
      </div>`;
    col.querySelector(".movie-card").addEventListener("click", () => openDetail(m));
    grid.appendChild(col);
  });
}

// --- Detail modal ---

async function openDetail(movie) {
  const res = await fetch(`/api/movies/${movie.id}`);
  const detail = await res.json();

  const year = detail.release_date ? detail.release_date.substring(0, 4) : "";
  const genres = (detail.genres || "").split(",").filter(Boolean);
  const rating = detail.vote_average ? Number(detail.vote_average).toFixed(1) : null;

  document.getElementById("detail-poster").src = detail.poster_path ? TMDB_IMG + detail.poster_path : "";
  document.getElementById("detail-title").textContent = detail.title + (year ? ` (${year})` : "");
  document.getElementById("detail-rating").innerHTML = rating ? `★ ${rating}` : "";
  document.getElementById("detail-genres").innerHTML = genres.map(g => `<span class="badge bg-secondary me-1">${g.trim()}</span>`).join("");
  document.getElementById("detail-directors").textContent = detail.directors || "";
  document.getElementById("detail-actors").textContent = detail.actors || "";
  document.getElementById("detail-directors-row").classList.toggle("d-none", !detail.directors);
  document.getElementById("detail-actors-row").classList.toggle("d-none", !detail.actors);
  document.getElementById("detail-description").textContent = detail.description || "";

  const btn = document.getElementById("detail-find-similar");
  btn.onclick = () => {
    trackEvent("find-similar");
    bootstrap.Modal.getInstance(document.getElementById("detailModal")).hide();
    selectMovie(detail);
  };

  new bootstrap.Modal(document.getElementById("detailModal")).show();
}

// --- Reset ---

function resetSearch() {
  searchInput.value = "";
  currentMovieId = null;
  document.querySelector("#hero p").classList.remove("d-none");
  document.getElementById("source-movie").classList.add("d-none");
  document.getElementById("results").classList.add("d-none");
  document.getElementById("related-grid").innerHTML = "";
  SLIDERS.forEach(name => {
    const slider = document.getElementById(`mixer-${name}`);
    slider.value = 50;
    slider.disabled = true;
    document.getElementById(`mixer-${name}-value`).textContent = "50";
  });
  const excludeCheck = document.getElementById("exclude-title");
  excludeCheck.checked = false;
  excludeCheck.disabled = true;
  const yearFrom = document.getElementById("year-from");
  const yearTo = document.getElementById("year-to");
  yearFrom.value = "";
  yearTo.value = "";
  yearFrom.disabled = true;
  yearTo.disabled = true;
  lastRelatedMovies = [];
  searchInput.focus();
}

// Close dropdown on outside click
document.addEventListener("click", e => {
  if (!e.target.closest(".search-wrapper")) dropdown.classList.remove("show");
});
