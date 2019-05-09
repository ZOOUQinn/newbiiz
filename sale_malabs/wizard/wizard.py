from odoo import models, fields


class ClaimProcessWizard(models.TransientModel):
    _name = 'claim.process.wizard'
    _description = 'Wizard to process claim lines'

    claim_line_id = fields.Many2one(comodel_name='claim.line.ept', string='Claim Line')
    display_name = fields.Char(readonly=True)
    hide = fields.Selection(selection=[])
    is_create_invoice = fields.Boolean(string='Create Invoice')
    is_visible_goods_back = fields.Boolean()
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')
    product_id = fields.Many2one(comodel_name='product.product', string='Product to be Replace')
    quantity = fields.Float()
    reject_message_id = fields.Many2one(comodel_name='claim.reject.message', string='Reject Reason')
    send_goods_back = fields.Boolean(string='Send Goods Back to Customer')
    state = fields.Selection(selection=[])