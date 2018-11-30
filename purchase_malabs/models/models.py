from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_item = fields.Char(string='Item No', compute='_compute_item_no')
    product_list = fields.Char(string='List No', compute='_compute_list_no')

    @api.depends('product_id')
    def _compute_item_no(self):
        for rec in self:
            rec.product_item = rec.product_id.item

    @api.depends('product_id')
    def _compute_list_no(self):
        for rec in self:
            rec.product_list = rec.product_id.ma_labs_list