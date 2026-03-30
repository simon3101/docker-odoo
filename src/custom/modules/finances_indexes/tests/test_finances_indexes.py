from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestFinancesIndexes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kpi_gross = cls.env['account.financial.kpi'].create({
            'formula': 'gross_margin',
            'threshold_warning': 50.0,
            'threshold_critical': 20.0,
        })
        cls.kpi_liquidity = cls.env['account.financial.kpi'].create({
            'formula': 'current_ratio',
            'threshold_warning': 1.5,
            'threshold_critical': 1.0,
        })
        cls.kpi_receivables = cls.env['account.financial.kpi'].create({
            'formula': 'receivables_turnover',
            'threshold_warning': 5.0,
            'threshold_critical': 2.0,
        })

    def test_kpi_name_computed_automatically(self):
        """Verifica que el nombre se genera automáticamente según la fórmula"""
        self.assertEqual(self.kpi_gross.name, 'GM-01')
        self.assertEqual(self.kpi_liquidity.name, 'CR-01')
        self.assertEqual(self.kpi_receivables.name, 'RT-01')

    def test_kpi_value_computed(self):
        """Verifica que el valor del KPI se calcula sin errores"""
        self.assertIsInstance(self.kpi_gross.value, float)
        self.assertIsInstance(self.kpi_liquidity.value, float)
        self.assertIsInstance(self.kpi_receivables.value, float)

    def test_kpi_status_is_set(self):
        """Verifica que el estado siempre es uno de los tres valores válidos"""
        self.assertIn(self.kpi_gross.status, ['green', 'yellow', 'red'])
        self.assertIn(self.kpi_liquidity.status, ['green', 'yellow', 'red'])
        self.assertIn(self.kpi_receivables.status, ['green', 'yellow', 'red'])

    def test_kpi_status_green_when_above_warning(self):
        """Verifica estado verde cuando valor supera umbral advertencia"""
        self.kpi_gross.write({
            'threshold_warning': 0.0,
            'threshold_critical': -1.0,
        })
        self.assertEqual(self.kpi_gross.status, 'green')

    def test_kpi_status_red_when_below_critical(self):
        """Verifica estado rojo cuando valor está bajo umbral crítico"""
        self.kpi_gross.write({
            'threshold_warning': 999999.0,
            'threshold_critical': 888888.0,
        })
        self.assertEqual(self.kpi_gross.status, 'red')

    def test_kpi_threshold_validation(self):
        """Caso límite: umbral crítico >= umbral advertencia lanza ValidationError"""
        with self.assertRaises(ValidationError):
            self.kpi_gross.write({
                'threshold_warning': 100.0,
                'threshold_critical': 100.0,
            })

    def test_kpi_inactive_not_in_dashboard(self):
        """Caso límite: KPI inactivo no aparece en el tablero"""
        self.kpi_gross.active = False
        active_kpis = self.env['account.financial.kpi'].search([
            ('active', '=', True),
            ('id', '=', self.kpi_gross.id),
        ])
        self.assertEqual(len(active_kpis), 0)
        self.kpi_gross.active = True

    def test_monthly_data_returns_six_months(self):
        """Verifica que get_monthly_data retorna 6 meses de datos"""
        data = self.kpi_gross.get_monthly_data()
        self.assertEqual(len(data), 6)
        for month in data:
            self.assertIn('label', month)
            self.assertIn('value', month)

    def test_unique_formula_constraint(self):
        """Caso límite: no se pueden crear dos KPIs con la misma fórmula"""
        from psycopg2 import IntegrityError
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['account.financial.kpi'].create({
                    'formula': 'gross_margin',
                    'threshold_warning': 50.0,
                    'threshold_critical': 20.0,
                })
