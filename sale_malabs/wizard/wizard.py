from odoo import models, fields, api


class ClaimProcessWizard(models.TransientModel):
    _name = 'claim.process.wizard'
    _description = 'Wizard to process claim lines'

    claim_line_id = fields.Many2one(comodel_name='claim.line.ept', string='Claim Line')
    display_name = fields.Char(readonly=True)
    hide = fields.Boolean()
    is_create_invoice = fields.Boolean(string='Create Invoice')
    is_visible_goods_back = fields.Boolean()
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')
    product_id = fields.Many2one(comodel_name='product.product', string='Product to be Replace')
    quantity = fields.Float()
    reject_message_id = fields.Many2one(comodel_name='claim.reject.message', string='Reject Reason')
    send_goods_back = fields.Boolean(string='Send Goods Back to Customer')
    state = fields.Selection(selection=[
        ('process', 'Process'),
    ], default='process')

    @api.model
    def default_get(self, fields_list):
        defaults = super(ClaimProcessWizard, self).default_get(fields_list)
        if self.env.context['active_model'] == 'claim.line.ept':
            claim_line = self.env[self.env.context['active_model']].browse(self.env.context['active_ids'])
            defaults['product_id'] = claim_line.product_id.id
            defaults['quantity'] = claim_line.return_qty
            defaults['hide'] = True
            defaults['claim_line_id'] = claim_line.id
        elif self.env.context['active_model'] == 'crm.claim.ept':
            claim = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
            if claim.state == 'draft':
                defaults.update({'is_visible_goods_back': False})
            elif claim.state == 'process':
                defaults.update({'is_visible_goods_back': True})
        return defaults

    @api.multi
    def process_refund(self):
        self.ensure_one()
        self.claim_line_id.to_be_replace_product_id = self.product_id
        self.claim_line_id.to_be_replace_quantity = self.quantity
        self.claim_line_id.is_create_invoice = self.is_create_invoice

    @api.multi
    def reject_claim(self):
        record = self.env[self.env.context['active_model']].browse(self.env.context.get('active_id'))
        if record.state == 'process':
            if self.is_visible_goods_back:
                record.to_return_picking_ids = ((4, record.return_picking_id.copy(default={
                    'location_id': record.return_picking_id.location_dest_id.id,
                    'location_dest_id': record.return_picking_id.location_id.id,
                    'origin': 'Return of ' + record.return_picking_id.name,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id
                }).id, False),)
            else:
                pass
        record.state = 'reject'
        record.reject_message_id = self.reject_message_id

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id == self.claim_line_id.product_id:
            self.hide = True
            self.is_create_invoice = False
            self.quantity = self.claim_line_id.return_qty
        else:
            self.hide = False
            self.is_create_invoice = True