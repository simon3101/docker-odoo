from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    storage_tag_ids = fields.Many2many(
        comodel_name='stock.storage.tag',
        relation='product_template_storage_tag_rel',
        column1='product_id',
        column2='tag_id',
        string='Etiquetas de Almacenamiento',
    )

    def action_open_tag_wizard(self):
        """Abre el wizard de asignación rápida de etiquetas"""
        self.ensure_one()
        wizard = self.env['stock.product.tag.wizard'].create({
            'product_id': self.id,
            'storage_tag_ids': [(6, 0, self.storage_tag_ids.ids)],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asignar Etiquetas',
            'res_model': 'stock.product.tag.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
