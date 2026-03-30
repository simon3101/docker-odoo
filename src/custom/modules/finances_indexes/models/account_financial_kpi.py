from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


# Diccionario de referencia que mapea las claves técnicas del campo formula
# a sus etiquetas legibles. Se usa en el dashboard JS para mostrar el nombre
# del KPI sin depender del ORM.
KPI_FORMULAS = {
    'gross_margin': 'Margen Bruto',
    'current_ratio': 'Liquidez Corriente',
    'receivables_turnover': 'Rotación de Cuentas por Cobrar',
}


class AccountFinancialKpi(models.Model):
    # _name define el nombre técnico del modelo en la base de datos.
    # _order asegura que los KPIs se listen alfabéticamente en vistas y búsquedas.
    _name = 'account.financial.kpi'
    _description = 'Indicador de Salud Financiera'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        readonly=True,
    )

    # formula es un Selection en vez de texto libre por dos razones:
    # 1. Seguridad: evita inyección de código Python arbitrario.
    # 2. Mantenibilidad: las fórmulas están definidas y documentadas en _evaluate_formula.
    formula = fields.Selection(
        selection=[
            ('gross_margin', 'Margen Bruto'),
            ('current_ratio', 'Liquidez Corriente'),
            ('receivables_turnover', 'Rotación de Cuentas por Cobrar'),
        ],
        string='Fórmula / KPI',
        required=True,
    )

    threshold_warning = fields.Float(
        string='Umbral Advertencia',
        required=True,
        help='Si el valor está por debajo de este umbral, se muestra amarillo.',
    )

    threshold_critical = fields.Float(
        string='Umbral Crítico',
        required=True,
        help='Si el valor está por debajo de este umbral, se muestra rojo.',
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    # value y status son campos computados con store=False — no se persisten en BD.
    # Se recalculan en cada lectura consultando los asientos contables en tiempo real.
    value = fields.Float(
        string='Valor Actual',
        compute='_compute_value',
        store=False,
    )

    status = fields.Selection(
        selection=[
            ('green', 'Verde'),
            ('yellow', 'Amarillo'),
            ('red', 'Rojo'),
        ],
        string='Estado',
        compute='_compute_value',
        store=False,
    )

    FORMULA_PREFIXES = {
        'gross_margin': 'GM',
        'current_ratio': 'CR',
        'receivables_turnover': 'RT',
    }
    _sql_constraints = [
            ('unique_formula', 'UNIQUE(formula)',
            'Ya existe un KPI configurado para esta fórmula.'),
        ]

    @api.depends('formula')
    def _compute_name(self):
        labels = {
            'gross_margin': 'GM-01',
            'current_ratio': 'CR-01',
            'receivables_turnover': 'RT-01',
        }
        for kpi in self:
            kpi.name = labels.get(kpi.formula, '')

    @api.constrains('threshold_warning', 'threshold_critical')
    def _check_thresholds(self):
        """
        Valida que el umbral crítico sea estrictamente menor que el umbral
        de advertencia. Si no se cumple, la lógica del semáforo sería incoherente
        porque nunca habría estado 'yellow' entre los dos umbrales.
        """
        for kpi in self:
            if kpi.threshold_critical >= kpi.threshold_warning:
                raise ValidationError(
                    'El umbral crítico debe ser menor que el umbral de advertencia.'
                )

    def _compute_value(self):
        """
        Calcula el valor actual del KPI y determina su estado (semáforo).

        Lógica del semáforo:
        - Verde  : valor >= threshold_warning  (situación saludable)
        - Amarillo: threshold_critical <= valor < threshold_warning (advertencia)
        - Rojo   : valor < threshold_critical  (situación crítica)

        Si la fórmula falla por cualquier razón (sin datos, división por cero, etc.),
        el KPI se muestra en rojo con valor 0.0 para evitar errores silenciosos.
        """
        for kpi in self:
            try:
                value = kpi._evaluate_formula(kpi.formula)
                kpi.value = value
                if value >= kpi.threshold_warning:
                    kpi.status = 'green'
                elif value >= kpi.threshold_critical:
                    kpi.status = 'yellow'
                else:
                    kpi.status = 'red'
            except Exception:
                kpi.value = 0.0
                kpi.status = 'red'

    def _get_account_balance(self, account_types):
        """
        Suma los saldos de todas las cuentas contables que pertenecen
        a los tipos indicados, considerando solo asientos confirmados (posted).

        Usa read_group en vez de iterar registros para mayor eficiencia —
        delega el cálculo a la BD con una sola consulta SQL agregada.

        Retorna el valor absoluto del balance para que los cálculos de los
        KPIs sean siempre positivos independientemente de la naturaleza
        deudora o acreedora de las cuentas.
        """
        accounts = self.env['account.account'].search([
            ('account_type', 'in', account_types),
        ])
        if not accounts:
            return 0.0
        result = self.env['account.move.line'].read_group(
            [('account_id', 'in', accounts.ids), ('parent_state', '=', 'posted')],
            ['balance'], [],
        )
        return abs(result[0]['balance']) if result and result[0]['balance'] else 0.0

    def _evaluate_formula(self, formula):
        """
        Evalúa la fórmula del KPI usando saldos de cuentas contables reales.

        Fórmulas implementadas:

        gross_margin (Margen Bruto):
            (Ingresos - Costo de Ventas) / Ingresos × 100
            Indica qué porcentaje de los ingresos queda después de cubrir
            los costos directos. Un margen alto indica mayor eficiencia.

        current_ratio (Liquidez Corriente):
            Activos Corrientes / Pasivos Corrientes
            Mide la capacidad de la empresa para cubrir sus obligaciones
            a corto plazo. Un valor > 1 indica liquidez positiva.

        receivables_turnover (Rotación de Cuentas por Cobrar):
            Ingresos / Cuentas por Cobrar
            Indica cuántas veces se cobran las cuentas por cobrar en un período.
            Un valor alto indica cobro eficiente de clientes.

        Retorna 0.0 si no hay datos suficientes para calcular (evita ZeroDivisionError).
        """
        if formula == 'gross_margin':
            revenue = self._get_account_balance(['income', 'income_other'])
            cogs = self._get_account_balance(['expense'])
            return ((revenue - cogs) / revenue * 100) if revenue else 0.0

        elif formula == 'current_ratio':
            current_assets = self._get_account_balance([
                'asset_cash', 'asset_receivable', 'asset_current'
            ])
            current_liabilities = self._get_account_balance([
                'liability_payable', 'liability_current'
            ])
            return (current_assets / current_liabilities) if current_liabilities else 0.0

        elif formula == 'receivables_turnover':
            revenue = self._get_account_balance(['income', 'income_other'])
            receivables = self._get_account_balance(['asset_receivable'])
            return (revenue / receivables) if receivables else 0.0

        return 0.0

    def get_monthly_data(self):
        """
        Retorna los últimos 6 meses de datos del KPI para renderizar
        la gráfica de evolución en el dashboard.

        Nota: actualmente retorna el mismo valor para todos los meses
        porque los saldos de cuentas son acumulados. Para una evolución
        real por período habría que filtrar account.move.line por fechas.

        Retorna una lista de dicts con 'label' (nombre del mes) y 'value' (valor calculado).
        """
        self.ensure_one()
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            month_date = today - relativedelta(months=i)
            months.append({
                'label': month_date.strftime('%b %Y'),
                'value': round(self._evaluate_formula(self.formula), 2),
            })
        return months
