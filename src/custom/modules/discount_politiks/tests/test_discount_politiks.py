from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestDiscountPolitiks(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule_retail = cls.env['account.discount.rule'].create({
            'customer_type': 'retail',
            'discount': 5.0,
        })
        cls.rule_wholesale = cls.env['account.discount.rule'].create({
            'customer_type': 'wholesale',
            'discount': 15.0,
        })
        cls.rule_vip = cls.env['account.discount.rule'].create({
            'customer_type': 'vip',
            'discount': 25.0,
        })
        cls.partner_retail = cls.env['res.partner'].create({
            'name': 'Cliente Minorista',
            'customer_type': 'retail',
            'customer_rank': 1,
        })
        cls.partner_wholesale = cls.env['res.partner'].create({
            'name': 'Cliente Mayorista',
            'customer_type': 'wholesale',
            'customer_rank': 1,
        })
        cls.partner_vip = cls.env['res.partner'].create({
            'name': 'Cliente VIP',
            'customer_type': 'vip',
            'customer_rank': 1,
        })
        cls.partner_no_type = cls.env['res.partner'].create({
            'name': 'Cliente Sin Tipo',
            'customer_rank': 1,
        })

    def _create_invoice(self, partner):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_a.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

    def test_discount_applied_on_retail_customer(self):
        """Verifica que se aplica el descuento correcto para minorista"""
        invoice = self._create_invoice(self.partner_retail)
        invoice.action_post()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.discount, 5.0)

    def test_discount_applied_on_wholesale_customer(self):
        """Verifica que se aplica el descuento correcto para mayorista"""
        invoice = self._create_invoice(self.partner_wholesale)
        invoice.action_post()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.discount, 15.0)

    def test_discount_applied_on_vip_customer(self):
        """Verifica que se aplica el descuento correcto para VIP"""
        invoice = self._create_invoice(self.partner_vip)
        invoice.action_post()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.discount, 25.0)

    def test_no_discount_for_customer_without_type(self):
        """Caso límite: sin tipo de cliente no se aplica descuento"""
        invoice = self._create_invoice(self.partner_no_type)
        invoice.action_post()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.discount, 0.0)

    def test_no_discount_when_rule_is_inactive(self):
        """Caso límite: regla inactiva no aplica descuento"""
        self.rule_retail.active = False
        invoice = self._create_invoice(self.partner_retail)
        invoice.action_post()
        for line in invoice.invoice_line_ids:
            self.assertEqual(line.discount, 0.0)

    def test_discount_rule_validation_over_100(self):
        """Caso límite: descuento mayor a 100% lanza ValidationError"""
        with self.assertRaises(ValidationError):
            self.rule_retail.discount = 101.0
            self.rule_retail._check_discount()

    def test_discount_rule_validation_negative(self):
        """Caso límite: descuento negativo lanza ValidationError"""
        with self.assertRaises(ValidationError):
            self.rule_retail.discount = -1.0
            self.rule_retail._check_discount()
