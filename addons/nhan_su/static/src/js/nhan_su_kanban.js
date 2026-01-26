(function () {
  "use strict";

  // Runs on DOM change and initial load to add header level badges and filtering per department group
  function updateDepartmentHeaders() {
    document
      .querySelectorAll(".nhan_vien_kanban_rows .o_kanban_group")
      .forEach(function (group) {
        try {
          // ensure header exists
          var header = group.querySelector(".o_kanban_header");
          if (!header) return;

          // if this group contains any level-1 records, hide department header info and skip filters
          var hasLevel1 =
            group.querySelector('.o_kanban_record[data-level="1"]') !== null;
          if (hasLevel1) {
            // keep department title visible, hide only the counter and filter UI
            var titleEl = header.querySelector(".o_kanban_header_title");
            if (titleEl) titleEl.style.display = "";
            var counterEl = header.querySelector(".o_kanban_counter");
            if (counterEl) counterEl.style.display = "none";
            // remove any existing filter UI
            var existing = header.querySelector(".dept-level-filters");
            if (existing) existing.remove();
            return;
          }

          var filterBox = header.querySelector(".dept-level-filters");
          if (!filterBox) {
            filterBox = document.createElement("div");
            filterBox.className = "dept-level-filters";
            filterBox.style.marginLeft = "12px";
            filterBox.style.display = "flex";
            filterBox.style.gap = "8px";
            header.appendChild(filterBox);
          }

          // configuration: label and level value
          var levels = [
            { label: "Trưởng phòng", level: 4 },
            { label: "Phó phòng", level: 5 },
            { label: "Nhân viên", level: 6 },
            { label: "Thực tập", level: 7 },
          ];

          // compute counts
          levels.forEach(function (lv) {
            var count = group.querySelectorAll(
              '.o_kanban_record[data-level="' + lv.level + '"]',
            ).length;
            var btn = filterBox.querySelector(".lvl-btn-" + lv.level);
            if (!btn) {
              btn = document.createElement("button");
              btn.type = "button";
              btn.className = "btn btn-sm btn-light lvl-btn-" + lv.level;
              btn.dataset.level = lv.level;
              btn.style.display = "inline-flex";
              btn.style.alignItems = "center";
              btn.style.gap = "6px";
              btn.style.padding = "4px 8px";
              btn.style.borderRadius = "12px";
              btn.style.cursor = "pointer";
              btn.title = "Lọc " + lv.label;

              var spanLabel = document.createElement("span");
              spanLabel.className = "lvl-label";
              spanLabel.textContent = lv.label;
              spanLabel.style.fontSize = "12px";
              spanLabel.style.fontWeight = "600";

              var spanCount = document.createElement("span");
              spanCount.className = "lvl-count";
              spanCount.textContent = "(" + count + ")";
              spanCount.style.fontSize = "12px";
              spanCount.style.opacity = "0.8";

              btn.appendChild(spanLabel);
              btn.appendChild(spanCount);

              btn.addEventListener("click", function (ev) {
                ev.preventDefault();
                var lvl = this.dataset.level;
                // toggle filter state on group
                var active = group.classList.contains("filter-level-" + lvl);
                // remove any active level filters
                group.classList.forEach(function (c) {
                  if (c.indexOf("filter-level-") === 0)
                    group.classList.remove(c);
                });
                if (!active) {
                  group.classList.add("filter-level-" + lvl);
                }
              });

              filterBox.appendChild(btn);
            }
            // update count text
            var span = btn.querySelector(".lvl-count");
            if (span) span.textContent = "(" + count + ")";
          });

          // NOTE: removed the global 'Hiện tất cả' clear button per request.
        } catch (e) {
          console.error("nhan_su kanban header update error", e);
        }
      });
  }

  // observe DOM changes for kanban groups because Odoo may rerender
  var observer = new MutationObserver(function (mutations) {
    // throttle a bit
    window.requestAnimationFrame(updateDepartmentHeaders);
  });

  function startObserver() {
    var root = document.querySelector(".nhan_vien_kanban_rows");
    if (!root) return;
    observer.disconnect();
    observer.observe(root, { childList: true, subtree: true });
    updateDepartmentHeaders();
  }

  // init when page ready
  document.addEventListener("DOMContentLoaded", function () {
    startObserver();
  });

  // also try when Odoo widgets load (in case DOMContentLoaded already fired)
  setTimeout(startObserver, 1500);
})();
