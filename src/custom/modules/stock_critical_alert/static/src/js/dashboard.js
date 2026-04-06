/** @odoo-module **/
/**
 * @module stock_critical_alert.dashboard
 * @description Componente OWL para el tablero de Stock Crítico.
 *
 * Muestra los productos con stock_alert_sent=True agrupados por categoría
 * en formato kanban, junto con una gráfica de barras (Chart.js) que compara
 * la cantidad disponible vs el stock mínimo configurado de cada producto.
 *
 * El componente se registra como client action bajo el tag
 * 'stock_critical_alert.dashboard', vinculado desde el XML de vistas.
 *
 * Dependencias externas:
 *  - Chart.js 4.4.0 (cargado dinámicamente desde cdnjs.cloudflare.com)
 *
 * Servicios Odoo utilizados:
 *  - orm: para consultas al backend via RPC
 *  - action: para abrir el formulario del producto al hacer clic en una tarjeta
 */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

class StockCriticalDashboard extends Component {
    static template = "stock_critical_alert.Dashboard";
    /**
     * setup() — Hook de inicialización del componente OWL.
     *
     * Se ejecuta una sola vez al crear el componente, antes del primer render.
     * Aquí se inicializan los servicios y el estado reactivo.
     *
     * Estado reactivo (useState):
     *  - products: lista de productos con stock crítico activo
     *  - loading: controla el spinner de carga en el template
     *
     * onMounted: se ejecuta después del primer render cuando el DOM ya existe.
     * Es necesario esperar al DOM para poder renderizar el canvas de Chart.js.
     */
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            products: [],
            loading: true,
        });
        onMounted(async () => {
            // Chart.js se carga de forma dinámica para no bloquear el bundle
            // principal. loadJS() retorna una Promise que resuelve cuando el
            // script está disponible en window.Chart
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            await this.loadProducts();
        });
    }

    /**
     * loadProducts() — Carga los productos en estado crítico desde el backend.
     *
     * Filtra por stock_alert_sent=True para mostrar solo los productos que
     * tienen una alerta activa. Cuando termina de cargar, llama a renderChart()
     * con un pequeño delay (200ms) para asegurarse de que el DOM del canvas
     * ya está disponible después del re-render de OWL.
     *
     * Campos recuperados:
     *  - name: para mostrar en las tarjetas y en el eje X de la gráfica
     *  - qty_available: cantidad actual en stock
     *  - stock_min: umbral mínimo configurado
     *  - categ_id: para agrupar por categoría en el kanban
     */
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
    /**
     * groupByCategory() — Agrupa los productos por categoría para el kanban.
     *
     * Retorna un array de pares [nombreCategoria, [productos]] que el template
     * itera con t-foreach para renderizar las columnas del kanban.
     *
     * Los productos sin categoría se agrupan bajo "Sin Categoría".
     *
     * @returns {Array} Array de [string, product[]] ordenado por orden de aparición
     */
    groupByCategory() {
        const groups = {};
        for (const p of this.state.products) {
            const cat = p.categ_id ? p.categ_id[1] : "Sin Categoría";
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(p);
        }
        return Object.entries(groups);
    }
    /**
     * renderChart() — Inicializa o reinicializa la gráfica de barras con Chart.js.
     *
     * Antes de crear una nueva instancia, destruye la anterior si existe
     * (canvas._chartInstance) para evitar memory leaks y el error
     * "Canvas is already in use" al recargar el tablero.
     *
     * Datasets:
     *  - Barras rojas: cantidad disponible actual de cada producto
     *  - Línea amarilla: stock mínimo configurado de cada producto
     *
     * La combinación barra + línea permite ver visualmente qué productos
     * están por debajo del umbral mínimo de un solo vistazo.
     */
    renderChart() {
        const canvas = document.getElementById("stock-critical-chart");
        // Salir si el canvas no existe o Chart.js no cargó correctamente
        if (!canvas || !window.Chart) return;
        // Destruir instancia anterior para evitar memory leaks
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
    /**
     * verifyStock(productId) — Ejecuta la verificación manual de stock para un producto.
     *
     * Llamado desde el botón "Verificar Stock" en cada tarjeta del kanban.
     * Invoca action_check_critical_stock() en el backend via ORM RPC.
     *
     * Si el stock del producto se recuperó por encima del mínimo,
     * el backend resetea stock_alert_sent=False y el producto desaparece
     * automáticamente del tablero al recargar la lista.
     *
     * Después de la llamada al backend, activa el estado de carga y recarga
     * todos los productos para reflejar el nuevo estado del tablero.
     *
     * @param {number} productId - ID del product.template a verificar
     */
    async verifyStock(productId) {
        await this.orm.call(
            "product.template",
            "action_check_critical_stock",
            [[productId]],
        );
        this.state.loading = true;
        await this.loadProducts();
    }
    /**
     * openProduct(productId) — Abre el formulario del producto en una vista form.
     *
     * Llamado al hacer clic en el nombre del producto en la tarjeta kanban.
     * Usa el servicio action de Odoo para navegar al formulario sin recargar
     * la página, manteniendo la navegación SPA (Single Page Application).
     *
     * @param {number} productId - ID del product.template a abrir
     */
    openProduct(productId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "product.template",
            res_id: productId,
            views: [[false, "form"]],
        });
    }
}

/**
 * Registro del componente como client action en el registry de Odoo.
 *
 * El tag 'stock_critical_alert.dashboard' debe coincidir exactamente con
 * el campo <field name="tag"> del registro ir.actions.client en el XML de vistas.
 * Cuando Odoo carga esa acción, busca en el registry y renderiza este componente.
 */

registry.category("actions").add("stock_critical_alert.dashboard", StockCriticalDashboard);
