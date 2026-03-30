from odoo import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

    contract_type = fields.Selection(
        selection=[
            ('full_time', 'Tiempo Completo'),
            ('part_time', 'Medio Tiempo'),
            ('temporary', 'Temporal'),
        ],
        string='Tipo de Contrato',
        default=False,
        help='Define el tipo de contrato del empleado. '
             'Determina qué estructura salarial y beneficios se aplicarán '
             'automáticamente al generar la nómina.',
    )
