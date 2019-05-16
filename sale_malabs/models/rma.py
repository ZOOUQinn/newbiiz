from odoo import models, fields, api, exceptions, _


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
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Delivery Order',  domain=[
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
        ('reject', 'Rejected'),
    ], default='draft')
    to_return_picking_ids = fields.Many2many(comodel_name='stock.picking', string='Return Delivery Orders')
    type_action = fields.Selection(selection=[
        ('correction', 'Corrective Action'),
        ('prevention', 'Preventive Action')
    ], string='Action Type')
    user_fault = fields.Char(string='Trouble Responsible')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible')
    website_message_ids = fields.One2many(comodel_name='mail.message', inverse_name='res_id')

    @api.onchange('picking_id')
    def onchange_picking(self):
        picking = self.picking_id
        if picking:
            self.partner_id = picking.partner_id
            self.email_from = picking.partner_id.email
            self.partner_phone = picking.partner_id.phone
            self.sale_id = picking.sale_id
            self.section_id = picking.sale_id.team_id

            claim_line_ids = [(5, 0, 0)]
            for move in picking.move_ids_without_package:
                claim_line_ids.append((0, 0, {
                    'product_id': move.product_id.id,
                    'done_qty': move.quantity_done,
                    'quantity': move.quantity_done,
                    'move_id': move.id,
                }))

            self.claim_line_ids = claim_line_ids

    @api.model
    def create(self, vals):
        vals.update({'code': self.env['ir.sequence'].next_by_code('crm.claim.ept')})
        record = super(CrmClaimEpt, self).create(vals)
        record.sale_id = record.picking_id.sale_id
        return record

    @api.multi
    def action_rma_send(self):
        pass

    @api.multi
    def approve_claim(self):
        self.ensure_one()
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or self.picking_id.location_id.id,
            'partner_id': self.partner_id.id,
            'origin': 'Return of ' + self.picking_id.name
        })

        for line in self.claim_line_ids:
            line.move_id = self.env['stock.move'].create({
                'name': 'Qinn',
                'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.picking_id.location_dest_id.id,
                'location_dest_id': self.location_id.id or self.picking_id.location_id.id,
            })

        self.return_picking_id = picking.id
        self.state = 'approve'

    @api.multi
    def set_to_draft(self):
        pass

    @api.multi
    def process_claim(self):
        for claim in self:

            picking = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'location_dest_id': self.picking_id.location_dest_id.id,
                'location_id': self.location_id.id or self.picking_id.location_id.id,
                'partner_id': self.partner_id.id,
                'origin': 'Return of ' + self.return_picking_id.name
            })

            sale_order_lines = []
            account_invoice_lines = []

            price_unit = {}
            for order_line in claim.sale_id.order_line:
                price_unit.update({order_line.product_id.id: order_line.price_unit})

            for claim_line in claim.claim_line_ids:
                if claim_line.claim_type == 'replace':
                    if claim_line.to_be_replace_product_id and claim_line.to_be_replace_quantity > 0:
                        claim_line.move_id = self.env['stock.move'].create({
                            'name': 'Qinn',
                            'picking_id': picking.id,
                            'product_id': claim_line.to_be_replace_product_id.id,
                            'product_uom_qty': claim_line.to_be_replace_quantity,
                            'product_uom': claim_line.to_be_replace_product_id.uom_id.id,
                            'location_dest_id': self.picking_id.location_dest_id.id,
                            'location_id': self.location_id.id or self.picking_id.location_id.id,
                        })
                        if claim_line.is_create_invoice == True:
                            sale_order_lines.append((0, 0, {
                                'product_id': claim_line.to_be_replace_product_id.id,
                                'product_uom_qty': claim_line.to_be_replace_quantity,
                            }))

                    else:
                        raise exceptions.Warning(
                            _('Claim line with %s has Replace product or Replace quantity or both not set.')
                            % claim_line.product_id.name
                        )

                elif claim_line.claim_type == 'repair':
                    claim_line.move_id = self.env['stock.move'].create({
                        'name': 'Qinn',
                        'picking_id': picking.id,
                        'product_id': claim_line.product_id.id,
                        'product_uom_qty': claim_line.return_qty,
                        'product_uom': claim_line.product_id.uom_id.id,
                        'location_dest_id': self.picking_id.location_dest_id.id,
                        'location_id': self.location_id.id or self.picking_id.location_id.id,
                    })
                elif claim_line.claim_type == 'refund':
                    account_invoice_lines.append((0, 0, {
                        'name': 'Refund for %s' % self.sale_id.name,
                        'product_id': claim_line.product_id.id,
                        'quantity': claim_line.return_qty,
                        'price_unit': price_unit.get(claim_line.product_id.id),
                        'account_id': self.env.ref('l10n_ca.1_chart2171_en').id
                    }))

            if picking.move_lines:
                self.to_return_picking_ids = ((4, picking.id, False),)
            else:
                picking.unlink()

            if sale_order_lines:
                self.new_sale_id = self.env['sale.order'].create({
                    'partner_id': self.partner_id.id,
                    'order_line': sale_order_lines,
                })

            if account_invoice_lines:
                self.refund_invoice_ids = ((4, self.env['account.invoice'].create({
                    'partner_id': self.partner_id.id,
                    'invoice_line_ids': account_invoice_lines,
                    'claim_id': self.id,
                }).id, False),)

            claim.state = 'close'

    @api.multi
    def action_claim_reject_process_ept(self):
        pass

    @api.multi
    def show_return_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        picking = self.return_picking_id

        action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
        action['res_id'] = picking.id
        return action

    @api.multi
    def show_delivery_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('to_return_picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def act_supplier_invoice_refund_ept(self):
        action = self.env.ref('account.action_invoice_tree').read()[0]

        invoices = self.mapped('refund_invoice_ids')
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif invoices:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.id
        return action

    @api.multi
    def act_new_so_ept(self):
        action = self.env.ref('sale.action_quotations').read()[0]
        sale_order = self.new_sale_id

        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['res_id'] = sale_order.id
        return action


class ClaimLineEpt(models.Model):
    _name = 'claim.line.ept'
    _description = 'Claim Line EPT'

    claim_id = fields.Many2one(comodel_name='crm.claim.ept', string='Related claim', readonly=True, ondelete='cascade')
    claim_type = fields.Selection(selection=[
        ('refund', 'Refund'),
        ('replace', 'Replace'),
        ('repair', 'Repair'),
    ], string='Claim Type')
    display_name = fields.Char(string='Display Name', readonly=True)
    done_qty = fields.Float(string='Delivered Quantity', readonly=True)
    is_create_invoice = fields.Boolean(string='Create Invoice')
    move_id = fields.Many2one(comodel_name='stock.move', string='Move')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    quantity = fields.Float(string='Return Quantity')
    return_qty = fields.Float(string='Received Quantity', readonly=True)
    rma_reason_id = fields.Many2one(comodel_name='rma.reason.ept', string='Reason')
    to_be_replace_product_id = fields.Many2one(comodel_name='product.product', string='Product to be Replace')
    to_be_replace_quantity = fields.Float(string='Replace Quantity', default=0)

    @api.model
    def create(self, vals):
        record = super(ClaimLineEpt, self).create(vals)
        record.done_qty = record.move_id.quantity_done
        return record


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

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        crm_claim_ept = self.env['crm.claim.ept'].search((('return_picking_id', '=', self.id),))
        if crm_claim_ept:

            for claim_line in crm_claim_ept.claim_line_ids:
                claim_line.claim_type = claim_line.rma_reason_id.action

            crm_claim_ept.state = 'process'
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, vals):
        record = super(StockMove, self).write(vals)

        if vals.get('state') == 'done':
            for move in self:
                for claim_lime in self.env['claim.line.ept'].search((('move_id', '=', move.id),)):
                    claim_lime.return_qty = move.quantity_done

        return record


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    claim_id = fields.Many2one(comodel_name='crm.claim.ept')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rma_count = fields.Integer(string='RMA', readonly=True)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    return_partner_id = fields.Many2one(comodel_name='res.partner', string='Return Address')