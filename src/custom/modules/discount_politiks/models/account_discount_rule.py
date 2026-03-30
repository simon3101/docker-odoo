
from odoo import models, fields, api

from odoo.exceptions import ValidationError

class AccountDiscountRule(models.Model):
    _name = 'account.discount.rule'
    _description = 'Regla de Descuento por Tipo de Cliente'
    _order = 'customer_type'

    customer_type = fields.Selection(

        selection=[
            ('retail', 'Minorista'),
            ('wholesale', 'Mayorista'),
            ('vip', 'VIP'),
        ],

        string='Tipo de Cliente',
        required=True,

    )

    discount = fields.Float(
        string='Descuento (%)',
        required=True,
        digits=(5, 2),
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    _sql_constraints = [
        ('unique_customer_type', 'UNIQUE(customer_type)',
         'Ya existe una regla de descuento para este tipo de cliente.'),
    ]

    @api.constrains('discount')

    def _check_discount(self):

        for rule in self:
            if rule.discount < 0 or rule.discount > 100:
                raise ValidationError('El descuento debe estar entre 0 y 100%.')

