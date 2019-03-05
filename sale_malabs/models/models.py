from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    credit_note = fields.Text(string='Credit Note')
    re_sell_certificate = fields.Char(string='Re-sell Certificate')
    ups_account = fields.Char(string='UPS Account #')
    fedex_account = fields.Char(string='FedEx Account #')
    delivery_confirmation_option = fields.Selection(string='Delivery Confirmation Option', selection=[['y', 'Y'], ['n', 'N']])
    delivery_confirmation_signature_required = fields.Selection(string='Delivery Confirmation Signature Required', selection=[['y', 'Y'], ['n', 'N']])
    declared_value_option = fields.Selection(string='Declared Value Option', selection=[['y', 'Y'], ['n', 'N']])
    declared_value_amount = fields.Char(string='Declared Value Amount')
    blind_shipment = fields.Selection(string='Blind Shipment', selection=[['y', 'Y'], ['n', 'N']])
    customer_po = fields.Char(string="Customer PO #")

    @api.model
    def _credit_limit(self):
        self.ensure_one()
        credit_limit = self.partner_id.credit_limit
        unpaid = 0.0
        for invoice in self.env['account.invoice'].browse(self.env['account.invoice'].search((('state', '!=', 'paid'), ('partner_id', '=', self.partner_id.id),)).ids):
            unpaid += invoice.residual_signed

        if unpaid >= credit_limit:
            return True
        else:
            return False

    @api.multi
    def action_confirm(self):
        if self.partner_invoice_id != self.partner_shipping_id:
            raise UserError(_('The Invoice Address must be identical with Shipping Address.'))
        elif self._credit_limit():
            raise UserError(_('Unpaid invoice(s) total greater or equal to the credit line.'))
        else:
            return super(SaleOrder, self).action_confirm()

    purchase_order = fields.Many2one(comodel_name='purchase.order', string='Purchase Order #')

    @api.depends('order_line.price_total', 'payment_term_id')
    def _amount_all(self):

        super(SaleOrder, self)._amount_all()

        for order in self:
            total_rate = order.payment_term_id.total_rate
            if total_rate:
                order.update({
                    'amount_total': order.amount_total * total_rate,
                })

    @api.model
    def create(self, vals):
        rec = super(SaleOrder, self).create(vals)
        for order_line in rec.order_line:
            users = order_line.product_id.manufacturer.liaison
            if users:
                rec.message_subscribe_users(user_ids=users.ids)
        return rec


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # todo use state field instead.
    is_danger = fields.Boolean(default=False)

    @api.multi
    @api.onchange('price_unit')
    def price_unit_change(self):
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        if self.price_unit < self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id):
            self.is_danger = True
        else:
            self.is_danger = False

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


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    total_rate = fields.Float(string='Total Rate', default=1.0, digits=(5,3))