(function () {
  const page = document.body.dataset.page;
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.dataset.page === page) a.setAttribute("aria-current", "page");
  });

  const ledger = document.querySelector("[data-ledger]");
  if (!ledger) return;

  const statusHost = document.querySelector("[data-status-filters]");
  const topicHost = document.querySelector("[data-topic-filters]");
  const search = document.querySelector("[data-ledger-search]");
  const count = document.querySelector("[data-ledger-count]");
  let findings = [];
  let status = "all";
  let topic = "all";
  let q = "";

  function button(host, value, label, pressed) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.setAttribute("aria-pressed", pressed ? "true" : "false");
    b.addEventListener("click", () => {
      host.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      if (host === statusHost) status = value;
      if (host === topicHost) topic = value;
      render();
    });
    host.appendChild(b);
  }

  function render() {
    const rows = findings.filter((f) => {
      if (status !== "all" && f.status !== status) return false;
      if (topic !== "all" && f.topic !== topic) return false;
      if (!q) return true;
      const blob = [f.id, f.claim, f.quote, f.why_it_matters, f.topic, f.status].join(" ").toLowerCase();
      return blob.includes(q);
    });
    count.textContent = rows.length + " of " + findings.length + " findings";
    ledger.innerHTML = rows.map((f) => {
      const src = window.TAX_SOURCES[f.source_id];
      const href = src ? src.url : "#";
      const title = src ? src.title : f.source_id;
      return `<article class="card" id="${f.id}">
        <p><span class="status status-${f.status}">${f.status}</span> <span class="mono">${f.id}</span> <span class="muted">${f.topic}</span></p>
        <h3>${escapeHtml(f.claim)}</h3>
        <blockquote><p>${escapeHtml(f.quote)}</p><cite><a href="${href}">${escapeHtml(title)}</a></cite></blockquote>
        <p>${escapeHtml(f.why_it_matters)}</p>
      </article>`;
    }).join("");
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  const scriptUrl = document.querySelector("script[src*='site.js']").src;
  const root = scriptUrl.replace(/assets\/site\.js(?:\?.*)?$/, "");
  Promise.all([
    fetch(root + "data/findings.json").then((r) => r.json()),
    fetch(root + "data/sources.json").then((r) => r.json())
  ]).then(([findingsFile, sourcesFile]) => {
    findings = findingsFile.findings;
    window.TAX_SOURCES = Object.fromEntries(sourcesFile.sources.map((s) => [s.id, s]));
    button(statusHost, "all", "All", true);
    ["settled", "open", "flag", "rejected", "supported"].forEach((s) => button(statusHost, s, s, false));
    const topics = Array.from(new Set(findings.map((f) => f.topic))).sort();
    button(topicHost, "all", "All topics", true);
    topics.forEach((t) => button(topicHost, t, t, false));
    search.addEventListener("input", () => { q = search.value.trim().toLowerCase(); render(); });
    render();
  }).catch(() => {
    ledger.innerHTML = "<p>The ledger file did not load. Open this page from the site root so <code>data/findings.json</code> can be fetched. The same findings are cited on the front page.</p>";
  });
})();
