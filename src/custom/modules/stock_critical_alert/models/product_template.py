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

    stock_alert_sent = fields.Boolean(
        string='Alerta de Stock Enviada',
        default=False,
        copy=False,
        help='Indica si ya se generó una alerta de stock crítico. '
             'Se resetea automáticamente cuando el stock se recupera.',
    )

    def _check_critical_stock(self):
        """
        Genera una alerta en mail.message si el stock disponible
        cae por debajo del stock mínimo. Evita duplicados usando
        el campo booleano stock_alert_sent en vez de buscar por texto.

        Incluye reset automático: cuando el stock se recupera por encima
        del mínimo, stock_alert_sent vuelve a False para que la próxima
        caída genere una nueva alerta.
        """
        for product in self:
            qty = product.qty_available

            if product.stock_min > 0 and qty < product.stock_min:
                # Solo genera alerta si no se ha enviado una previamente
                if not product.stock_alert_sent:
                    product.message_post(
                        body=Markup(
                            '⚠️ <b>Stock crítico:</b> El producto <b>%s</b> '
                            'tiene %s unidades disponibles, '
                            'por debajo del mínimo configurado de %s.'
                        ) % (html_escape(product.name), qty, product.stock_min),
                        message_type='comment',
                        subtype_xmlid='mail.mt_note',
                    )
                    product.stock_alert_sent = True
            else:
                # Reset automático cuando el stock se recupera
                if product.stock_alert_sent:
                    product.stock_alert_sent = False

    def action_check_critical_stock(self):
        """Método público para verificar el stock crítico manualmente desde la vista."""
        self._check_critical_stock()