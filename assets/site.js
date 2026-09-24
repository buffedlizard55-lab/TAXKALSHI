(function () {
  const page = document.body.dataset.page;
  document.querySelectorAll(".nav a").forEach((a) => {
    if (a.dataset.page === page) a.setAttribute("aria-current", "page");
  });

  function siteRoot() {
    const script = document.querySelector("script[src*='site.js']");
    if (!script) return "";
    return script.src.replace(/assets\/site\.js(?:\?.*)?$/, "");
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>\"']/g, (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '\"': "&quot;",
      "'": "&#39;"
    }[character]));
  }

  function initLedger() {
    const ledger = document.querySelector("[data-ledger]");
    if (!ledger) return;

    const statusHost = document.querySelector("[data-status-filters]");
    const topicHost = document.querySelector("[data-topic-filters]");
    const search = document.querySelector("[data-ledger-search]");
    const count = document.querySelector("[data-ledger-count]");
    let findings = [];
    let status = "all";
    let topic = "all";
    let query = "";

    function button(host, value, label, pressed) {
      const buttonElement = document.createElement("button");
      buttonElement.type = "button";
      buttonElement.textContent = label;
      buttonElement.setAttribute("aria-pressed", pressed ? "true" : "false");
      buttonElement.addEventListener("click", () => {
        host.querySelectorAll("button").forEach((item) => item.setAttribute("aria-pressed", "false"));
        buttonElement.setAttribute("aria-pressed", "true");
        if (host === statusHost) status = value;
        if (host === topicHost) topic = value;
        render();
      });
      host.appendChild(buttonElement);
    }

    function render() {
      const rows = findings.filter((finding) => {
        if (status !== "all" && finding.status !== status) return false;
        if (topic !== "all" && finding.topic !== topic) return false;
        if (!query) return true;
        const searchable = [finding.id, finding.claim, finding.quote, finding.why_it_matters, finding.topic, finding.status]
          .join(" ").toLowerCase();
        return searchable.includes(query);
      });
      count.textContent = rows.length + " of " + findings.length + " findings";
      ledger.innerHTML = rows.map((finding) => {
        const source = window.TAX_SOURCES[finding.source_id];
        const href = source ? source.url : "#";
        const title = source ? source.title : finding.source_id;
        return `<article class="card" id="${escapeHtml(finding.id)}">
          <p><span class="status status-${escapeHtml(finding.status)}">${escapeHtml(finding.status)}</span> <span class="mono">${escapeHtml(finding.id)}</span> <span class="muted">${escapeHtml(finding.topic)}</span></p>
          <h3>${escapeHtml(finding.claim)}</h3>
          <blockquote><p>${escapeHtml(finding.quote)}</p><cite><a href="${escapeHtml(href)}">${escapeHtml(title)}</a></cite></blockquote>
          <p>${escapeHtml(finding.why_it_matters)}</p>
        </article>`;
      }).join("");
    }

    fetch(siteRoot() + "data/findings.json")
      .then((response) => {
        if (!response.ok) throw new Error("findings request failed");
        return response.json();
      })
      .then((findingsFile) => fetch(siteRoot() + "data/sources.json")
        .then((response) => {
          if (!response.ok) throw new Error("sources request failed");
          return response.json();
        })
        .then((sourcesFile) => [findingsFile, sourcesFile]))
      .then(([findingsFile, sourcesFile]) => {
        findings = findingsFile.findings;
        window.TAX_SOURCES = Object.fromEntries(sourcesFile.sources.map((source) => [source.id, source]));
        button(statusHost, "all", "All", true);
        ["settled", "open", "flag", "rejected", "supported"].forEach((value) => button(statusHost, value, value, false));
        const topics = Array.from(new Set(findings.map((finding) => finding.topic))).sort();
        button(topicHost, "all", "All topics", true);
        topics.forEach((value) => button(topicHost, value, value, false));
        search.addEventListener("input", () => {
          query = search.value.trim().toLowerCase();
          render();
        });
        render();
      })
      .catch(() => {
        ledger.innerHTML = "<p>The ledger file did not load. Open this page from the site root so <code>data/findings.json</code> can be fetched. The executive answer is on the summary page.</p>";
      });
  }

  function initCalculator() {
    const calculator = document.querySelector("[data-tax-calculator]");
    if (!calculator) return;

    const slider = calculator.querySelector("[data-amount-slider]");
    const selectedAmount = calculator.querySelector("[data-selected-amount]");
    const selectedLabel = calculator.querySelector("[data-selected-label]");
    const federalOutput = calculator.querySelector("[data-federal-tax]");
    const californiaOutput = calculator.querySelector("[data-california-tax]");
    const combinedOutput = calculator.querySelector("[data-combined-tax]");
    const effectiveOutput = calculator.querySelector("[data-effective-rate]");
    const afterTaxOutput = calculator.querySelector("[data-after-tax]");
    const stepOutput = calculator.querySelector("[data-step-cost]");
    const status = calculator.querySelector("[data-calculator-status]");
    const table = document.querySelector("[data-tax-table]");
    const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

    function taxAt(amount, bands) {
      const band = bands.find((item) => item.up_to === null || amount <= item.up_to);
      if (!band) return 0;
      return band.base + (amount - band.from) * band.rate;
    }

    function money(amount) {
      return currency.format(Math.max(0, amount));
    }

    function renderTable(model) {
      const rows = [];
      let previousAmount = 0;
      for (let amount = model.step; amount <= model.maximum; amount += model.step) {
        const federal = taxAt(amount, model.federal_bands);
        const california = taxAt(amount, model.california_bands);
        const combined = federal + california;
        const previous = taxAt(previousAmount, model.federal_bands) + taxAt(previousAmount, model.california_bands);
        rows.push(`<tr data-amount-row data-amount="${amount}"><th scope="row">${money(amount)}</th><td>${money(federal)}</td><td>${money(california)}</td><td><strong>${money(combined)}</strong></td><td>${(combined / amount * 100).toFixed(2)}%</td><td>${money(combined - previous)}</td></tr>`);
        previousAmount = amount;
      }
      table.innerHTML = rows.join("");
    }

    function renderSelected(model) {
      const amount = Number(slider.value) * model.step;
      const federal = taxAt(amount, model.federal_bands);
      const california = taxAt(amount, model.california_bands);
      const combined = federal + california;
      const previous = taxAt(amount - model.step, model.federal_bands) + taxAt(amount - model.step, model.california_bands);
      const label = money(amount);
      selectedAmount.textContent = label;
      selectedLabel.textContent = label;
      federalOutput.textContent = money(federal);
      californiaOutput.textContent = money(california);
      combinedOutput.textContent = money(combined);
      effectiveOutput.textContent = (combined / amount * 100).toFixed(2) + "%";
      afterTaxOutput.textContent = money(amount - combined);
      stepOutput.textContent = money(combined - previous);
      document.querySelectorAll("[data-amount-row]").forEach((row) => {
        row.classList.toggle("is-selected", Number(row.dataset.amount) === amount);
      });
    }

    fetch(siteRoot() + "data/calculator.json")
      .then((response) => {
        if (!response.ok) throw new Error("calculator request failed");
        return response.json();
      })
      .then((model) => {
        slider.max = String(model.maximum / model.step);
        renderTable(model);
        renderSelected(model);
        slider.addEventListener("input", () => renderSelected(model));
        status.innerHTML = `Loaded from <code>data/calculator.json</code>. Federal ${model.model.federal_year}; California ${model.model.california_year}.`;
      })
      .catch(() => {
        status.textContent = "The interactive rate model did not load; the complete precomputed table remains available below.";
      });
  }

  initLedger();
  initCalculator();
})();
