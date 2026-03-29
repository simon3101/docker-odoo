from odoo import models, fields, api
from odoo.tools import html_escape
from markupsafe import Markup


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_min = fields.Float(
        string='Stock Mínimo',
        default=0.0,
        help='Cantidad mínima de stock antes de generar una alerta',
    )

    def _check_critical_stock(self):
        """Genera una alerta en mail.message si el stock disponible
        cae por debajo del stock mínimo. Evita duplicados."""
        for product in self:
            qty = product.qty_available
            if product.stock_min > 0 and qty < product.stock_min:
                already_alerted = self.env['mail.message'].search_count([
                    ('res_id', '=', product.id),
                    ('model', '=', 'product.template'),
                    ('body', 'ilike', 'Stock crítico'),
                    ('message_type', '=', 'comment'),
                ])
                if not already_alerted:
                    product.message_post(
                        body=Markup(
                            '⚠️ <b>Stock crítico:</b> El producto <b>%s</b> '
                            'tiene %s unidades disponibles, '
                            'por debajo del mínimo configurado de %s.'
                        ) % (html_escape(product.name), qty, product.stock_min),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )