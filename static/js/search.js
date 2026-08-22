/* Client-side filter over the full registration index.
 *
 * Progressive enhancement. The page ships a static, paginated, crawlable table;
 * this script only adds a search box on top of it. If the script never runs, or
 * the index fetch fails, the static table stays exactly as served -- which is
 * also what Google Scholar's crawler sees, since it does not reliably execute
 * JavaScript.
 *
 * The index (~400 KB gzipped for ~10k rows) is fetched lazily on first use, not
 * on page load, so landing on the site costs nothing extra.
 */
(function () {
  "use strict";

  var MAX_RESULTS = 200;

  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }

  function escapeHTML(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function formatId(number) {
    // Trial numbers render as zero-padded AEARCTR ids; the index stores the
    // bare number so the payload stays small.
    return "AEARCTR-" + String(number).padStart(7, "0");
  }

  ready(function () {
    var roots = document.querySelectorAll(".trial-search");
    Array.prototype.forEach.call(roots, function (root) {
      var form = root.querySelector(".trial-search-form");
      var input = root.querySelector("#trial-q, input[type=search]");
      var status = root.querySelector(".trial-search-status");
      var results = root.querySelector(".trial-search-results");
      // The static table and pager this filter temporarily replaces.
      var browse = document.querySelector(".trial-browse");
      if (!form || !input || !results) { return; }

      var indexURL = root.getAttribute("data-index-url");
      var trialBase = root.getAttribute("data-trial-base") || "/trials/";
      var data = null;
      var loading = null;
      var timer = null;

      // Only now is the control usable, so only now does it become visible.
      form.hidden = false;

      function load() {
        if (data) { return Promise.resolve(data); }
        if (loading) { return loading; }
        status.textContent = "Loading index…";
        loading = fetch(indexURL, { credentials: "same-origin" })
          .then(function (r) {
            if (!r.ok) { throw new Error("HTTP " + r.status); }
            return r.json();
          })
          .then(function (json) { data = json; status.textContent = ""; return data; })
          .catch(function (err) {
            loading = null;
            status.textContent = "Search is unavailable (" + err.message +
              "). The full list is still browsable below.";
            throw err;
          });
        return loading;
      }

      function render(matches, query) {
        if (!matches.length) {
          results.innerHTML = "<p>No registrations match “" +
            escapeHTML(query) + "”.</p>";
          return;
        }
        var rows = matches.slice(0, MAX_RESULTS).map(function (row) {
          var href = trialBase + encodeURIComponent(row.n) + "/";
          return "<tr><td><a href=\"" + href + "\">" + escapeHTML(formatId(row.n)) +
            "</a></td><td><a href=\"" + href + "\">" + escapeHTML(row.t) +
            "</a></td><td>" + escapeHTML(row.a) +
            "</td><td><time datetime=\"" + escapeHTML(row.d) + "\">" +
            escapeHTML(row.d) + "</time></td></tr>";
        }).join("");
        results.innerHTML =
          "<table class=\"trials\"><thead><tr><th scope=\"col\">Registry ID</th>" +
          "<th scope=\"col\">Title</th><th scope=\"col\">Primary investigator</th>" +
          "<th scope=\"col\">First registered</th></tr></thead><tbody>" + rows +
          "</tbody></table>";
      }

      function search(query) {
        var needle = query.trim().toLowerCase();
        if (!needle) { return; }
        // Match on title, lead investigator, and both the bare and padded id.
        var matches = data.filter(function (row) {
          return (row.t && row.t.toLowerCase().indexOf(needle) !== -1) ||
                 (row.a && row.a.toLowerCase().indexOf(needle) !== -1) ||
                 String(row.n) === needle ||
                 formatId(row.n).toLowerCase().indexOf(needle) !== -1;
        });
        var shown = Math.min(matches.length, MAX_RESULTS);
        status.textContent = matches.length + " match" +
          (matches.length === 1 ? "" : "es") +
          (matches.length > shown ? " (showing first " + shown + ")" : "");
        render(matches, query);
      }

      function restore() {
        results.hidden = true;
        results.innerHTML = "";
        status.textContent = "";
        if (browse) { browse.hidden = false; }
      }

      function onInput() {
        var query = input.value;
        if (!query.trim()) { restore(); return; }
        load().then(function () {
          // The value may have changed while the index was in flight.
          if (!input.value.trim()) { restore(); return; }
          if (browse) { browse.hidden = true; }
          results.hidden = false;
          search(input.value);
        }).catch(function () { /* status already explains the failure */ });
      }

      input.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(onInput, 150);
      });
    });
  });
})();
