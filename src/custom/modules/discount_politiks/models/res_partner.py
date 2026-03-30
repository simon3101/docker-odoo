from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_type = fields.Selection(
        selection=[
            ('retail', 'Minorista'),
            ('wholesale', 'Mayorista'),
            ('vip', 'VIP'),
        ],
        string='Tipo de Cliente',
        default=False,
    )
