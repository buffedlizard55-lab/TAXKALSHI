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
    const status = calculator.querySelector("[data-calculator-status]");
    const cards = document.querySelector("[data-scenario-cards]");
    const spread = document.querySelector("[data-scenario-spread]");
    const tableHead = document.querySelector("[data-tax-table-head]");
    const tableBody = document.querySelector("[data-tax-table]");
    const viewButtons = document.querySelectorAll("[data-table-view]");
    const viewLabel = document.querySelector("[data-table-view-label]");
    const stepButtons = calculator.querySelectorAll("[data-step-button]");
    const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
    let view = "combined";

    // --- Rate arithmetic. Mirrors scripts/taxmodel.py line for line. ---
    function taxAt(amount, bands) {
      const band = bands.find((item) => item.up_to === null || amount <= item.up_to);
      if (!band) return 0;
      return band.base + (amount - band.from) * band.rate;
    }

    // Section 1(h)(1) with the section 1(j)(5) dollar breakpoints (F47, F48).
    function stackedFederal(model, ordinaryPart, longTermPart) {
      const breaks = model.long_term_breakpoints_2026;
      const ordinaryTax = taxAt(ordinaryPart, model.federal_bands);
      const zeroSlice = Math.max(0, Math.min(longTermPart, breaks.maximum_zero_rate_amount - ordinaryPart));
      const remaining = longTermPart - zeroSlice;
      const fifteenSlice = Math.max(0, Math.min(remaining, breaks.maximum_15_percent_rate_amount - (ordinaryPart + zeroSlice)));
      const twentySlice = remaining - fifteenSlice;
      return ordinaryTax + 0.15 * fifteenSlice + breaks.rate_above_15_percent_amount * twentySlice;
    }

    function federalFor(model, scenario, amount) {
      if (scenario.federal_method === "stacked") {
        const share = Number(scenario.long_term_share);
        return stackedFederal(model, amount * (1 - share), amount * share);
      }
      return taxAt(amount, model.federal_bands);
    }

    function compute(model, scenario, amount) {
      const federal = federalFor(model, scenario, amount);
      const california = taxAt(amount, model.california_bands);
      return { amount, federal, california, combined: federal + california };
    }

    function money(amount) {
      return currency.format(Math.max(0, Math.round(amount * 100) / 100));
    }

    function signedMoney(amount) {
      const rounded = Math.round(amount * 100) / 100;
      if (Math.abs(rounded) < 0.005) return "same as ordinary";
      return (rounded < 0 ? "−" : "+") + currency.format(Math.abs(rounded)) + " vs. ordinary";
    }

    function percent(part, whole) {
      return whole ? (part / whole * 100).toFixed(2) + "%" : "0.00%";
    }

    function baselineOf(model) {
      return model.scenarios.find((scenario) => scenario.baseline) || model.scenarios[0];
    }

    function currentAmount(model) {
      return Number(slider.value) * model.step;
    }

    // --- Rendering. Every scenario moves together from the one slider. ---
    function renderCards(model) {
      const amount = currentAmount(model);
      const base = compute(model, baselineOf(model), amount);
      const previousAmount = amount - model.step;
      cards.innerHTML = model.scenarios.map((scenario) => {
        const now = compute(model, scenario, amount);
        const before = previousAmount > 0 ? compute(model, scenario, previousAmount) : { combined: 0 };
        const diff = now.combined - base.combined;
        // Every scenario is an open candidate, so every card carries the neutral
        // "open" tint. Only the difference line is colored; green here would read
        // as "settled" elsewhere on the site.
        return `<article class="card scenario-card card-open${scenario.baseline ? " is-baseline" : ""}" data-scenario-card="${escapeHtml(scenario.id)}">
          <p class="eyebrow">${scenario.baseline ? "Baseline" : "Compared with the baseline"}</p>
          <h3>${escapeHtml(scenario.label)}</h3>
          <dl class="scenario-figures">
            <div><dt>Federal 2026</dt><dd>${money(now.federal)}</dd></div>
            <div><dt>California 2025 sched.</dt><dd>${money(now.california)}</dd></div>
            <div class="scenario-combined"><dt>Combined</dt><dd>${money(now.combined)}</dd></div>
            <div><dt>Effective rate</dt><dd>${percent(now.combined, amount)}</dd></div>
            <div><dt>Left after model</dt><dd>${money(amount - now.combined)}</dd></div>
            <div><dt>Cost of this $10k step</dt><dd>${money(now.combined - before.combined)}</dd></div>
          </dl>
          <p class="scenario-diff ${diff < -0.005 ? "is-lower" : (diff > 0.005 ? "is-higher" : "is-same")}">${escapeHtml(signedMoney(diff))}</p>
          <p class="small muted">${escapeHtml(scenario.federal_note)}</p>
        </article>`;
      }).join("");

      const values = model.scenarios.map((scenario) => compute(model, scenario, amount).combined);
      const high = Math.max(...values);
      const low = Math.min(...values);
      if (spread) {
        spread.innerHTML = `At <strong>${money(amount)}</strong> of modeled taxable income the character question is worth <strong>${money(high - low)}</strong> in this model: from ${money(low)} (lowest scenario) to ${money(high)} (highest). The California share is <strong>${money(base.california)}</strong> in every scenario.`;
      }
    }

    function renderTable(model) {
      const columns = model.scenarios;
      if (tableHead) {
        tableHead.innerHTML = `<tr><th scope="col">Modeled taxable income</th>${columns.map((scenario) => `<th scope="col">${escapeHtml(scenario.short)}</th>`).join("")}</tr>`;
      }
      const rows = [];
      for (let amount = model.step; amount <= model.maximum; amount += model.step) {
        const cells = columns.map((scenario) => {
          const now = compute(model, scenario, amount);
          if (view === "step") {
            const before = amount > model.step ? compute(model, scenario, amount - model.step).combined : 0;
            return `<td>${money(now.combined - before)}</td>`;
          }
          if (view === "difference") {
            const base = compute(model, baselineOf(model), amount).combined;
            const diff = now.combined - base;
            return `<td>${Math.abs(diff) < 0.005 ? "—" : (diff < 0 ? "−" : "+") + money(Math.abs(diff))}</td>`;
          }
          if (view === "rate") return `<td>${percent(now.combined, amount)}</td>`;
          return `<td>${money(now[view])}</td>`;
        });
        rows.push(`<tr data-amount-row data-amount="${amount}"><th scope="row">${money(amount)}</th>${cells.join("")}</tr>`);
      }
      tableBody.innerHTML = rows.join("");
      highlightRow(model);
    }

    function highlightRow(model) {
      const amount = currentAmount(model);
      document.querySelectorAll("[data-amount-row]").forEach((row) => {
        row.classList.toggle("is-selected", Number(row.dataset.amount) === amount);
      });
    }

    function renderSelected(model) {
      const label = money(currentAmount(model));
      selectedAmount.textContent = label;
      selectedLabel.textContent = label;
      renderCards(model);
      highlightRow(model);
    }

    const viewLabels = {
      combined: "Combined federal + California",
      federal: "Federal only",
      california: "California only",
      difference: "Difference from the ordinary baseline",
      rate: "Effective combined rate",
      step: "Cost of each $10,000 step"
    };

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
        stepButtons.forEach((button) => {
          button.addEventListener("click", () => {
            const next = Number(slider.value) + Number(button.dataset.stepButton);
            if (next < Number(slider.min) || next > Number(slider.max)) return;
            slider.value = String(next);
            renderSelected(model);
          });
        });
        viewButtons.forEach((button) => {
          button.addEventListener("click", () => {
            view = button.dataset.tableView;
            viewButtons.forEach((item) => item.setAttribute("aria-pressed", item === button ? "true" : "false"));
            if (viewLabel) viewLabel.textContent = viewLabels[view] || view;
            renderTable(model);
          });
        });
        // Delegated, so rows re-rendered by a view change stay clickable.
        tableBody.addEventListener("click", (event) => {
          const row = event.target.closest("[data-amount-row]");
          if (!row) return;
          slider.value = String(Number(row.dataset.amount) / model.step);
          renderSelected(model);
        });
        status.innerHTML = `Loaded from <code>data/calculator.json</code>, record date ${escapeHtml(model.record_date)}. Federal ${model.model.federal_year}; California ${model.model.california_year} Schedule X; long-term breakpoints ${money(model.long_term_breakpoints_2026.maximum_zero_rate_amount)} and ${money(model.long_term_breakpoints_2026.maximum_15_percent_rate_amount)}.`;
      })
      .catch(() => {
        status.textContent = "The interactive model did not load; the complete precomputed combined table remains available below.";
      });
  }

  initLedger();
  initCalculator();
})();
