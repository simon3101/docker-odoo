/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

class FinancialHealthDashboard extends Component {
    static template = "finances_indexes.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            kpis: [],
            loading: true,
        });
        onMounted(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            await this.loadKpis();
        });
    }

    async loadKpis() {
        const kpis = await this.orm.searchRead(
            "account.financial.kpi",
            [["active", "=", true]],
            ["name", "value", "status", "threshold_warning", "threshold_critical", "formula"],
        );
        // Traducir etiqueta de fórmula
        const formulaLabels = {
            gross_margin: "Margen Bruto",
            current_ratio: "Liquidez Corriente",
            receivables_turnover: "Rotación de CxC",
        };
        for (const kpi of kpis) {
            kpi.formula_label = formulaLabels[kpi.formula] || kpi.formula;
        }
        // Cargar datos mensuales para cada KPI
        for (const kpi of kpis) {
            kpi.monthly_data = await this.orm.call(
                "account.financial.kpi",
                "get_monthly_data",
                [kpi.id],
            );
        }

        this.state.kpis = kpis;
        this.state.loading = false;

        // Renderizar gráficas después de que el DOM esté listo
        setTimeout(() => this.renderCharts(), 100);
    }

    renderCharts() {
        for (const kpi of this.state.kpis) {
            const canvas = document.getElementById(`chart-${kpi.id}`);
            if (!canvas) continue;
            const labels = kpi.monthly_data.map(d => d.label);
            const values = kpi.monthly_data.map(d => d.value);
            const color = this.getStatusColor(kpi.status);
            new Chart(canvas, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: kpi.name,
                        data: values,
                        borderColor: color,
                        backgroundColor: color + '33',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: false },
                        x: { ticks: { font: { size: 10 } } }
                    }
                }
            });
        }
    }

    getStatusColor(status) {
        return { green: "#28a745", yellow: "#ffc107", red: "#dc3545" }[status] || "#6c757d";
    }

    getStatusLabel(status) {
        return { green: "● Saludable", yellow: "● Advertencia", red: "● Crítico" }[status] || "● Sin datos";
    }

    openConfig() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Indicadores Financieros",
            res_model: "account.financial.kpi",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
        });
    }
}

registry.category("actions").add("finances_indexes.dashboard", FinancialHealthDashboard);
