// ---------------------------------------------------------------------
// Live retrieval search — calls the Flask /api/search endpoint
// ---------------------------------------------------------------------
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const chips = document.querySelectorAll(".chip");

async function runSearch(query) {
  if (!query.trim()) return;

  searchResults.innerHTML = `<p class="search-placeholder mono">// retrieving...</p>`;

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    renderResults(data.results);
  } catch (err) {
    searchResults.innerHTML = `<p class="search-placeholder mono">// couldn't reach the search endpoint — is app.py running?</p>`;
  }
}

function renderResults(results) {
  if (!results || results.length === 0) {
    searchResults.innerHTML = `<p class="search-placeholder mono">// no matches — try a different keyword</p>`;
    return;
  }

  searchResults.innerHTML = results
    .map(
      (r) => `
      <div class="result-chunk">
        <div class="result-head">
          <span class="result-title">${escapeHtml(r.title)}</span>
          <span class="result-score">score ${r.relevance.toFixed(2)}</span>
        </div>
        <span class="result-source mono">${escapeHtml(r.source)}</span>
        <p class="result-snippet">${escapeHtml(r.snippet)}</p>
      </div>`
    )
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

if (searchForm) {
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    runSearch(searchInput.value);
  });
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const q = chip.dataset.q;
    searchInput.value = q;
    runSearch(q);
  });
});

// ---------------------------------------------------------------------
// Contact form — posts to Flask /api/contact
// ---------------------------------------------------------------------
const contactForm = document.getElementById("contact-form");
const contactStatus = document.getElementById("contact-status");

if (contactForm) {
  contactForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById("name").value,
      email: document.getElementById("email").value,
      message: document.getElementById("message").value,
    };

    contactStatus.textContent = "sending...";
    contactStatus.classList.remove("error");

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok) {
        contactStatus.textContent = "✓ " + data.message;
        contactForm.reset();
      } else {
        contactStatus.textContent = "✗ " + data.message;
        contactStatus.classList.add("error");
      }
    } catch (err) {
      contactStatus.textContent = "✗ couldn't reach the server — is app.py running?";
      contactStatus.classList.add("error");
    }
  });
}
