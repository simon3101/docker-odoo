from odoo.tests.common import TransactionCase


class TestStockStorageTags(TransactionCase):

    def setUp(self):
        super().setUp()
        self.tag_a = self.env['stock.storage.tag'].create({
            'name': 'Refrigerado',
            'color': 1,
            'description': 'Productos que requieren refrigeración',
        })
        self.tag_b = self.env['stock.storage.tag'].create({
            'name': 'Frágil',
            'color': 2,
            'description': 'Productos que requieren manejo especial',
        })
        self.product = self.env['product.template'].create({
            'name': 'Producto Test',
            'is_storable': True,
        })

    def test_tag_creation(self):
        """Verifica que una etiqueta se crea con los campos correctos"""
        self.assertEqual(self.tag_a.name, 'Refrigerado')
        self.assertEqual(self.tag_a.color, 1)
        self.assertEqual(self.tag_a.description, 'Productos que requieren refrigeración')

    def test_tag_assignment_to_product(self):
        """Verifica que se pueden asignar etiquetas a un producto"""
        self.product.storage_tag_ids = [(4, self.tag_a.id)]
        self.assertIn(self.tag_a, self.product.storage_tag_ids)

    def test_multiple_tags_assignment(self):
        """Verifica que se pueden asignar múltiples etiquetas a un producto"""
        self.product.storage_tag_ids = [(4, self.tag_a.id), (4, self.tag_b.id)]
        self.assertEqual(len(self.product.storage_tag_ids), 2)
        self.assertIn(self.tag_a, self.product.storage_tag_ids)
        self.assertIn(self.tag_b, self.product.storage_tag_ids)

    def test_remove_tag_from_product(self):
        """Verifica que se puede quitar una etiqueta de un producto"""
        self.product.storage_tag_ids = [(4, self.tag_a.id), (4, self.tag_b.id)]
        self.product.storage_tag_ids = [(3, self.tag_a.id)]
        self.assertNotIn(self.tag_a, self.product.storage_tag_ids)
        self.assertIn(self.tag_b, self.product.storage_tag_ids)

    def test_many2many_relation_from_tag(self):
        """Verifica la relación inversa: desde la etiqueta ver sus productos"""
        self.product.storage_tag_ids = [(4, self.tag_a.id)]
        self.assertIn(self.product, self.tag_a.product_ids)

    def test_product_without_tags(self):
        """Caso límite: producto sin etiquetas no causa errores"""
        self.assertEqual(len(self.product.storage_tag_ids), 0)

    def test_tag_without_products(self):
        """Caso límite: etiqueta sin productos asignados"""
        self.assertEqual(len(self.tag_a.product_ids), 0)

    def test_multiple_products_same_tag(self):
        """Verifica que una etiqueta puede asignarse a múltiples productos"""
        product_b = self.env['product.template'].create({
            'name': 'Producto B',
            'is_storable': True,
        })
        self.product.storage_tag_ids = [(4, self.tag_a.id)]
        product_b.storage_tag_ids = [(4, self.tag_a.id)]
        self.assertIn(self.product, self.tag_a.product_ids)
        self.assertIn(product_b, self.tag_a.product_ids)

    def test_wizard_opens_empty_for_product_without_tags(self):
        """Caso límite: wizard abre vacío si el producto no tiene etiquetas"""
        action = self.product.action_open_tag_wizard()
        wizard = self.env['stock.product.tag.wizard'].browse(action['res_id'])
        self.assertEqual(wizard.product_id, self.product)
        self.assertEqual(len(wizard.storage_tag_ids), 0)

    def test_tag_color_zero_raises_validation_error(self):
        """Caso límite: crear etiqueta con color 0 debe lanzar ValidationError"""
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['stock.storage.tag'].create({
                'name': 'Etiqueta Sin Color',
                'color': 0,
            })