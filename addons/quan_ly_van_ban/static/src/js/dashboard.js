/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class VanBanDashboard extends Component {
  setup() {
    this.rpc = useService("rpc");
    this.state = useState({
      data: {},
      loading: true,
    });

    onWillStart(async () => {
      await this.loadDashboardData();
    });
  }

  async loadDashboardData() {
    try {
      const data = await this.rpc(
        "/web/dataset/call_kw/van.ban.dashboard/get_dashboard_data",
        {
          model: "van.ban.dashboard",
          method: "get_dashboard_data",
          args: [],
          kwargs: {},
        },
      );
      this.state.data = data;
      this.state.loading = false;
      this.renderCharts();
    } catch (error) {
      console.error("Error loading dashboard:", error);
      this.state.loading = false;
    }
  }

  renderCharts() {
    // This will be called after the component is mounted
    // You would need Chart.js or similar library
    console.log("Dashboard data:", this.state.data);
  }
}

VanBanDashboard.template = "quan_ly_van_ban.Dashboard";

registry.category("actions").add("quan_ly_van_ban.dashboard", VanBanDashboard);
