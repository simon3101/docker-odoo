from odoo import models, fields, api
from odoo.exceptions import ValidationError


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

    has_discount_rules = fields.Boolean(
        string='Tiene Reglas de Descuento',
        compute='_compute_has_discount_rules',
        store=False,
    )

    @api.depends_context('company')
    def _compute_has_discount_rules(self):
        """Verifica si existen reglas de descuento activas configuradas."""
        has_rules = bool(self.env['account.discount.rule'].search_count([
            ('active', '=', True),
        ]))
        for partner in self:
            partner.has_discount_rules = has_rules

    @api.constrains('customer_type')
    def _check_customer_type_has_rule(self):
        """
        Valida que exista una regla de descuento activa para el tipo
        de cliente seleccionado. Evita que el usuario asigne un tipo
        que no tiene regla configurada y genere confusión.
        """
        for partner in self:
            if not partner.customer_type:
                continue
            rule_exists = self.env['account.discount.rule'].search_count([
                ('customer_type', '=', partner.customer_type),
                ('active', '=', True),
            ])
            if not rule_exists:
                type_label = dict(
                    self._fields['customer_type'].selection
                ).get(partner.customer_type, partner.customer_type)
                raise ValidationError(
                    f'No existe una regla de descuento activa para el tipo '
                    f'"{type_label}". Configure la regla en '
                    f'Contabilidad → Configuración → Reglas de Descuento antes '
                    f'de asignar este tipo al cliente.'
                )
