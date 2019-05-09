from odoo import models, fields, api


class CrmClaimEpt(models.Model):
    _name = 'crm.claim.ept'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    access_token = fields.Char(string='Security Token', readonly=True)
    access_url = fields.Char(string='Portal Access URL')
    access_warning = fields.Text(string='Access warning', readonly=True)
    action_next = fields.Char(string='Next Action')
    # active
    cause = fields.Text(string='Root Cause')
    claim_line_ids = fields.One2many(comodel_name='claim.line.ept', string='Return Line', inverse_name='claim_id')
    code = fields.Char(string='RMA Number', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    date = fields.Datetime(default=fields.Datetime.now())
    date_action_next = fields.Datetime(string='Next Action Date')
    date_closed = fields.Datetime(string='Closed', readonly=True)
    date_deadline = fields.Date(string='Deadline')
    description = fields.Text()
    display_name = fields.Char(readonly=True)
    email_cc = fields.Text(string='Watchers Emails')
    email_from = fields.Char(string='Emal')
    invoice_id = fields.Many2one(comodel_name='account.invoice', string='Invoice')
    is_visible = fields.Boolean(readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Return Location')
    move_product_ids = fields.Many2many(comodel_name='product.product', readonly=True, string='Move Product')
    name = fields.Char(string='Subject', required=True)
    new_sale_id = fields.Many2one(comodel_name='sale.order', string='New Sale Order')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    partner_phone = fields.Char(string='Phone')
    picking_id = fields.Many2one(comodel_name='stock.picking', domain=[
        ('location_dest_id.usage', '=', 'customer'),
        ('state', '=', 'done')
    ])
    priority = fields.Selection(selection=[
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
    ], default='1')
    refund_invoice_ids = fields.Many2many(comodel_name='account.invoice', string='Refund Invoices')
    reject_message_id = fields.Many2one(comodel_name='claim.reject.message', string='Reject Reason')
    resolution = fields.Text(string='Resolution')
    return_picking_id = fields.Many2one(comodel_name='stock.picking', string='Return Delivery Order')
    rma_send = fields.Boolean()
    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', readonly=True)
    section_id = fields.Many2one(comodel_name='crm.team', string='Sales Channel', index=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('approve', 'Approve'),
        ('process', 'Process'),
        ('close', 'Close'),
        ('rejected', 'Rejected'),
    ], default='draft')
    to_return_picking_ids = fields.Many2many(comodel_name='stock.picking', string='Return Delivery Orders')
    type_action = fields.Selection(selection=[
        ('correction', 'Corrective Action'),
        ('prevention', 'Preventive Action')
    ], string='Action Type')
    user_fault = fields.Char(string='Trouble Responsible')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible')
    website_message_ids = fields.One2many(comodel_name='mail.message', inverse_name='res_id')

    @api.multi
    def action_rma_send(self):
        pass

    @api.multi
    def approve_claim(self):
        pass

    @api.multi
    def reject_claim(self):
        pass

    @api.multi
    def set_to_draft(self):
        pass

    @api.multi
    def process_claim(self):
        pass

    @api.multi
    def action_claim_reject_process_ept(self):
        pass

    @api.multi
    def show_return_picking(self):
        pass

    @api.multi
    def show_delivery_picking(self):
        pass

    @api.multi
    def act_supplier_invoice_refund_ept(self):
        pass

    @api.multi
    def act_new_so_ept(self):
        pass


class Claim_line_Ept(models.Model):
    _name = 'claim.line.ept'
    _description = 'Claim Line EPT'

    claim_id = fields.Many2one(comodel_name='crm.claim.ept', string='Related claim', readonly=True)
    claim_type = fields.Selection(selection=[], string='Claim Type')
    display_name = fields.Char(string='Display Name', readonly=True)
    done_qty = fields.Float(string='Delivered Quantity', readonly=True)
    is_create_invoice = fields.Boolean(string='Create Invoice')
    move_id = fields.Many2one(comodel_name='stock.move', string='Move')
    product_id =fields.Many2one(comodel_name='product.product', string='Product')
    quantity = fields.Float(string='Return Quantity')
    return_qty = fields.Float(string='Received Quantity', readonly=True)
    rma_reason_id = fields.Many2one(comodel_name='rma.reason.ept', string='Reason')
    to_be_replace_product_id = fields.Many2one(comodel_name='product.product', string='Product to be Replace')
    to_be_replace_quantity = fields.Float(string='Replace Quantity')

    @api.multi
    def action_claim_refund_process_ept(self):
        pass


class RMA_Reason_Ept(models.Model):
    _name = 'rma.reason.ept'
    _description = 'RMA Reason Ept'

    action = fields.Selection(selection=[
        ('refund', 'Refund'),
        ('replace', 'Replace'),
        ('repair', 'Repair'),
    ], string='Related Action')
    display_name = fields.Char(readonly=True)
    name = fields.Char(string='RMA Reason', required=True)


class ClaimRejectMessage(models.Model):
    _name = 'claim.reject.message'
    _description = 'Claim Reject Message'

    display_name = fields.Char(readonly=True)
    name = fields.Char(string='Reject Reason', required=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    view_claim_button = fields.Boolean(string='View Claim Button', readonly=True)
    claim_count_out = fields.Integer(string='Claims', readonly=True)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    claim_id = fields.Many2one(comodel_name='crm.claim.ept')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rma_count = fields.Integer(string='RMA', readonly=True)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    return_partner_id = fields.Many2one(comodel_name='res.partner', string='Return Address')