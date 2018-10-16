from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if self.partner_invoice_id == self.partner_shipping_id:
            return super(SaleOrder, self).action_confirm()
        else:
            raise UserError(_('The Invoice Address must be identical with Shipping Address.'))


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