from odoo import models
from odoo.tools import html_escape
from markupsafe import Markup


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """Aplica el descuento automático en las líneas de factura
        según el tipo de cliente del partner, antes de validar."""
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.partner_id:
                customer_type = move.partner_id.customer_type
                if customer_type:
                    rule = self.env['account.discount.rule'].search([
                        ('customer_type', '=', customer_type),
                        ('active', '=', True),
                    ], limit=1)
                    if rule:
                        for line in move.invoice_line_ids:
                            line.discount = rule.discount
                        # Obtener etiqueta legible del tipo de cliente
                        type_label = dict(
                            move.partner_id._fields['customer_type'].selection
                        ).get(customer_type, customer_type)
                        move.message_post(
                            body=Markup(
                                '💰 <b>Descuento aplicado:</b> Se aplicó un <b>%s%%</b> '
                                'de descuento en todas las líneas de factura '
                                'por ser cliente tipo <b>%s</b>.'
                            ) % (rule.discount, html_escape(type_label)),
                            message_type='comment',
                            subtype_xmlid='mail.mt_note',
                        )
        return super().action_post()
