from odoo.tests.common import TransactionCase


class TestStockCriticalAlert(TransactionCase):

    def setUp(self):
        super().setUp()
        self.location = self.env.ref('stock.stock_location_stock')
        self.product_a = self.env['product.template'].create({
            'name': 'Producto A',
            'is_storable': True,
            'stock_min': 10.0,
        })
        self.product_b = self.env['product.template'].create({
            'name': 'Producto B',
            'is_storable': True,
            'stock_min': 5.0,
        })

    def _set_stock(self, product, qty):
        """Helper para establecer el stock disponible del producto"""
        self.env['stock.quant']._update_available_quantity(
            product.product_variant_ids[0],
            self.location,
            qty,
        )

    def _get_alerts(self, product):
        return self.env['mail.message'].search([
            ('res_id', '=', product.id),
            ('model', '=', 'product.template'),
            ('body', 'ilike', 'Stock crítico'),
            ('message_type', '=', 'comment'),
        ])

    def _run_cron(self):
        """Simula la ejecución del cron"""
        products = self.env['product.template'].search([('stock_min', '>', 0)])
        products._check_critical_stock()

    # --- Tests del método directo ---

    def test_alert_generated_when_stock_below_minimum(self):
        """Verifica que se genera una alerta cuando el stock está por debajo del mínimo"""
        self._set_stock(self.product_a, 5.0)
        self.product_a._check_critical_stock()
        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'Debe generarse exactamente una alerta')

    def test_no_duplicate_alerts(self):
        """Verifica que no se generan alertas duplicadas"""
        self._set_stock(self.product_a, 5.0)
        self.product_a._check_critical_stock()
        self.product_a._check_critical_stock()
        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'No deben generarse alertas duplicadas')

    def test_no_alert_when_stock_above_minimum(self):
        """Verifica que no se genera alerta si el stock está bien"""
        self._set_stock(self.product_a, 50.0)
        self.product_a._check_critical_stock()
        self.assertEqual(len(self._get_alerts(self.product_a)), 0,
            'No debe generarse alerta si el stock está sobre el mínimo')

    # --- Tests del cron ---

    def test_cron_generates_alert_for_product_below_minimum(self):
        """Cron genera alerta cuando un producto está bajo el mínimo"""
        self._set_stock(self.product_a, 3.0)
        self._set_stock(self.product_b, 10.0)
        self._run_cron()
        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'El cron debe generar alerta para producto_a bajo el mínimo')
        self.assertEqual(len(self._get_alerts(self.product_b)), 0,
            'El cron no debe generar alerta para producto_b sobre el mínimo')

    def test_cron_only_alerts_products_below_minimum(self):
        """Cron solo alerta productos que estén bajo su mínimo, no todos"""
        self._set_stock(self.product_a, 3.0)
        self._set_stock(self.product_b, 20.0)
        self._run_cron()
        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'Solo producto_a debe tener alerta')
        self.assertEqual(len(self._get_alerts(self.product_b)), 0,
            'Producto_b no debe tener alerta')

    def test_cron_no_error_after_stock_replenishment(self):
        """Cron no falla cuando un producto que tenía stock bajo fue repuesto"""
        # Primero bajamos el stock y generamos la alerta
        self._set_stock(self.product_a, 3.0)
        self._run_cron()
        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'Debe generarse alerta inicial')

        # Reponemos el stock por encima del mínimo
        self._set_stock(self.product_a, 50.0)

        # El cron no debe fallar ni generar nueva alerta
        try:
            self._run_cron()
        except Exception as e:
            self.fail(f'El cron falló después de reponer el stock: {e}')

        self.assertEqual(len(self._get_alerts(self.product_a)), 1,
            'No debe generarse una segunda alerta si el stock fue repuesto')

    def test_no_alert_when_stock_equals_minimum(self):
        """Caso límite: no genera alerta cuando el stock es exactamente igual al mínimo"""
        # qty < stock_min es False cuando son iguales, no debe generar alerta
        self._set_stock(self.product_a, 10.0)  # stock_min también es 10.0
        self._run_cron()
        self.assertEqual(len(self._get_alerts(self.product_a)), 0,
            'No debe generarse alerta cuando el stock es exactamente igual al mínimo')

    def test_no_alert_when_stock_min_is_zero(self):
        """Caso límite: no genera alerta cuando stock_min no está configurado (= 0)"""
        product_sin_min = self.env['product.template'].create({
            'name': 'Producto Sin Mínimo',
            'is_storable': True,
            'stock_min': 0.0,
        })
        # No seteamos stock — aunque tenga 0 unidades, stock_min = 0
        # por lo que el if product.stock_min > 0 lo debe filtrar
        product_sin_min._check_critical_stock()
        self.assertEqual(len(self._get_alerts(product_sin_min)), 0,
            'No debe generarse alerta si stock_min es 0')
