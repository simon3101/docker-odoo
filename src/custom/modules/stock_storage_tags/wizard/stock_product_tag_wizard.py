from odoo import models, fields


class StockProductTagWizard(models.TransientModel):
    _name = 'stock.product.tag.wizard'
    _description = 'Asignación rápida de etiquetas de almacenamiento'

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Producto',
        required=True,
        ondelete='cascade',
    )
    storage_tag_ids = fields.Many2many(
        comodel_name='stock.storage.tag',
        string='Etiquetas de Almacenamiento',
        relation='stock_product_tag_wizard_tag_rel',
        column1='wizard_id',
        column2='tag_id',
    )

    def action_apply(self):
        """Aplica las etiquetas seleccionadas al producto"""
        self.product_id.storage_tag_ids = self.storage_tag_ids
        return {'type': 'ir.actions.act_window_close'}
