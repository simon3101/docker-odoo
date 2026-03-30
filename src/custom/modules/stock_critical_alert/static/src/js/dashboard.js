/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

class StockCriticalDashboard extends Component {
    static template = "stock_critical_alert.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            products: [],
            loading: true,
        });
        onMounted(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            await this.loadProducts();
        });
    }

    async loadProducts() {
        const products = await this.orm.searchRead(
            "product.template",
            [["stock_alert_sent", "=", true]],
            ["name", "qty_available", "stock_min", "categ_id"],
        );
        this.state.products = products;
        this.state.loading = false;
        setTimeout(() => this.renderChart(), 200);
    }

    groupByCategory() {
        const groups = {};
        for (const p of this.state.products) {
            const cat = p.categ_id ? p.categ_id[1] : "Sin Categoría";
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(p);
        }
        return Object.entries(groups);
    }

    renderChart() {
        const canvas = document.getElementById("stock-critical-chart");
        if (!canvas || !window.Chart) return;
        if (canvas._chartInstance) {
            canvas._chartInstance.destroy();
        }
        const products = this.state.products;
        const labels = products.map(p => p.name);
        const available = products.map(p => p.qty_available);
        const minimum = products.map(p => p.stock_min);

        canvas._chartInstance = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Cantidad Disponible",
                        data: available,
                        backgroundColor: "#dc354588",
                        borderColor: "#dc3545",
                        borderWidth: 1,
                    },
                    {
                        label: "Stock Mínimo",
                        data: minimum,
                        backgroundColor: "#ffc10744",
                        borderColor: "#ffc107",
                        borderWidth: 2,
                        type: "line",
                        pointRadius: 5,
                        fill: false,
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "top" },
                    title: {
                        display: true,
                        text: "Cantidad Disponible vs Stock Mínimo",
                        font: { size: 14, weight: "bold" }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: "Unidades" }
                    },
                    x: {
                        title: { display: true, text: "Productos" }
                    }
                }
            }
        });
    }

    async verifyStock(productId) {
        await this.orm.call(
            "product.template",
            "action_check_critical_stock",
            [[productId]],
        );
        this.state.loading = true;
        await this.loadProducts();
    }

    openProduct(productId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "product.template",
            res_id: productId,
            views: [[false, "form"]],
        });
    }
}

registry.category("actions").add("stock_critical_alert.dashboard", StockCriticalDashboard);
