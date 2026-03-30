from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


KPI_FORMULAS = {
    'gross_margin': 'Margen Bruto',
    'current_ratio': 'Liquidez Corriente',
    'receivables_turnover': 'Rotación de Cuentas por Cobrar',
}


class AccountFinancialKpi(models.Model):
    _name = 'account.financial.kpi'
    _description = 'Indicador de Salud Financiera'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
    )
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

    @api.constrains('threshold_warning', 'threshold_critical')
    def _check_thresholds(self):
        for kpi in self:
            if kpi.threshold_critical >= kpi.threshold_warning:
                raise ValidationError(
                    'El umbral crítico debe ser menor que el umbral de advertencia.'
                )

    def _compute_value(self):
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
        """Suma balances de cuentas por tipo."""
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
        """Retorna los últimos 6 meses de datos para la gráfica."""
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
