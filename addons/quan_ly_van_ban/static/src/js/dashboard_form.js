/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("van_ban_dashboard_tour", {
  url: "/web#action=quan_ly_van_ban.action_van_ban_dashboard",
  steps: () => [
    {
      trigger: ".o_form_view",
      run: function () {
        // Load dashboard data when form is loaded
        loadDashboardData();
      },
    },
  ],
});

async function loadDashboardData() {
  try {
    const result = await fetch(
      "/web/dataset/call_kw/van.ban.dashboard/get_dashboard_data",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "van.ban.dashboard",
          method: "get_dashboard_data",
          args: [],
          kwargs: {},
        }),
      },
    );

    const data = await result.json();

    if (data.result) {
      // Update KPI counters
      document.getElementById("van_ban_den_count").textContent =
        data.result.van_ban_den_thang || 0;
      document.getElementById("van_ban_di_count").textContent =
        data.result.van_ban_di_thang || 0;
      document.getElementById("qua_han_count").textContent =
        data.result.van_ban_qua_han || 0;
      document.getElementById("cho_duyet_count").textContent =
        (data.result.hop_dong_cho_duyet || 0) +
        (data.result.bao_gia_cho_duyet || 0);

      // Update stats
      document.getElementById("ty_le_qua_han").textContent =
        (data.result.ty_le_qua_han || 0).toFixed(1) + "%";
      document.getElementById("thoi_gian_tb").textContent =
        data.result.thoi_gian_xu_ly_tb || 0 + " ngày";
    }
  } catch (error) {
    console.error("Error loading dashboard data:", error);
  }
}

// Auto-load data when page loads
document.addEventListener("DOMContentLoaded", function () {
  if (
    window.location.href.includes(
      "action=quan_ly_van_ban.action_van_ban_dashboard",
    )
  ) {
    loadDashboardData();
  }
});
