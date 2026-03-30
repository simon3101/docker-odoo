from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


# post_install: los tests corren después de que todos los módulos están instalados,
# garantizando que el plan de cuentas y datos base de 'account' estén disponibles.
# -at_install: evita que corran durante la instalación del módulo.
@tagged('post_install', '-at_install')
class TestFinancesIndexes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """
        Crea los KPIs base que se reutilizan en múltiples tests.
        Se usa setUpClass en vez de setUp para crear los registros una sola vez
        por clase en vez de una vez por test — más eficiente en tiempo y queries.

        Se crean los tres tipos de KPI disponibles para verificar que todos
        calculan sin errores independientemente del tipo de fórmula.
        """
        super().setUpClass()

        cls.kpi_gross = cls.env['account.financial.kpi'].create({
            'name': 'Margen Bruto Test',
            'formula': 'gross_margin',
            'threshold_warning': 50.0,
            'threshold_critical': 20.0,
        })
        cls.kpi_liquidity = cls.env['account.financial.kpi'].create({
            'name': 'Liquidez Test',
            'formula': 'current_ratio',
            'threshold_warning': 1.5,
            'threshold_critical': 1.0,
        })
        cls.kpi_receivables = cls.env['account.financial.kpi'].create({
            'name': 'Rotación CxC Test',
            'formula': 'receivables_turnover',
            'threshold_warning': 5.0,
            'threshold_critical': 2.0,
        })

    def test_kpi_value_computed(self):
        """
        Verifica que el valor del KPI se calcula sin errores para los 3 tipos.
        No valida el valor exacto porque depende de datos contables reales —
        solo verifica que el tipo de retorno es float y no lanza excepciones.
        """
        self.assertIsInstance(self.kpi_gross.value, float)
        self.assertIsInstance(self.kpi_liquidity.value, float)
        self.assertIsInstance(self.kpi_receivables.value, float)

    def test_kpi_status_is_set(self):
        """
        Verifica que el estado del KPI siempre es uno de los tres valores válidos.
        No valida cuál estado específico porque depende de datos contables reales,
        pero garantiza que el campo nunca queda vacío o con un valor inválido.
        """
        self.assertIn(self.kpi_gross.status, ['green', 'yellow', 'red'])
        self.assertIn(self.kpi_liquidity.status, ['green', 'yellow', 'red'])
        self.assertIn(self.kpi_receivables.status, ['green', 'yellow', 'red'])

    def test_kpi_status_green_when_above_warning(self):
        """
        Verifica la lógica del semáforo verde.
        Configuramos umbrales muy bajos (0 y -1) para garantizar que
        cualquier valor calculado los supere y el estado sea verde.
        """
        kpi = self.env['account.financial.kpi'].create({
            'name': 'KPI Verde',
            'formula': 'gross_margin',
            'threshold_warning': 0.0,
            'threshold_critical': -1.0,
        })
        self.assertEqual(kpi.status, 'green')

    def test_kpi_status_red_when_below_critical(self):
        """
        Verifica la lógica del semáforo rojo.
        Configuramos umbrales imposiblemente altos para garantizar que
        cualquier valor calculado esté por debajo y el estado sea rojo.
        """
        kpi = self.env['account.financial.kpi'].create({
            'name': 'KPI Rojo',
            'formula': 'gross_margin',
            'threshold_warning': 999999.0,
            'threshold_critical': 888888.0,
        })
        self.assertEqual(kpi.status, 'red')

    def test_kpi_threshold_validation(self):
        """
        Caso límite: umbral crítico igual al umbral de advertencia debe lanzar ValidationError.
        Si ambos umbrales fueran iguales, nunca existiría el estado 'yellow' — la
        validación previene esta configuración incoherente.
        """
        with self.assertRaises(ValidationError):
            self.env['account.financial.kpi'].create({
                'name': 'KPI Inválido',
                'formula': 'gross_margin',
                'threshold_warning': 100.0,
                'threshold_critical': 100.0,
            })

    def test_kpi_inactive_not_in_dashboard(self):
        """
        Caso límite: un KPI con active=False no debe aparecer en el tablero.
        El dashboard filtra por active=True — este test verifica que el campo
        active funciona correctamente como filtro de visibilidad.
        """
        kpi = self.env['account.financial.kpi'].create({
            'name': 'KPI Inactivo',
            'formula': 'gross_margin',
            'threshold_warning': 50.0,
            'threshold_critical': 20.0,
            'active': False,
        })
        # La búsqueda con active=True no debe encontrar este KPI
        active_kpis = self.env['account.financial.kpi'].search([
            ('active', '=', True),
            ('id', '=', kpi.id),
        ])
        self.assertEqual(len(active_kpis), 0)

    def test_monthly_data_returns_six_months(self):
        """
        Verifica que get_monthly_data retorna exactamente 6 meses de datos
        con la estructura correcta (label y value) para renderizar la gráfica
        en el dashboard OWL.
        """
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