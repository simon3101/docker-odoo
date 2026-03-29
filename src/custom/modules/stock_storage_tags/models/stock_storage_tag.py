from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockStorageTag(models.Model):
    _name = 'stock.storage.tag'
    _description = 'Etiqueta de Almacenamiento'

    name = fields.Char(
        string='Nombre',
        required=True,
    )
    color = fields.Integer(
        string='Color',
        required=True,
        default=0,
    )
    description = fields.Text(
        string='Descripción',
    )
    product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_template_storage_tag_rel',
        column1='tag_id',
        column2='product_id',
        string='Productos',
    )

    @api.constrains('color')
    def _check_color(self):
        for tag in self:
            if tag.color == 0:
                raise ValidationError('Debes seleccionar un color para la etiqueta.')
