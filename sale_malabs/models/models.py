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
        record = super(SaleOrder, self).create(vals)

        for order_line in vals.get('order_line'):
            liaisons = self.env['product.product'].browse([order_line[2].get('product_id')]).manufacturer.liaisons
            if liaisons:
                record.message_subscribe(liaisons.ids)

        return record


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


class Res_Users(models.Model):
    _inherit = 'res.users'

    employee_name = fields.Char(string='Employee Name')


class Res_Partner(models.Model):
    _inherit = 'res.partner'

    customer_id = fields.Char(string='Customer ID')
    vendor_number = fields.Char(string='Vendor Number')
    owner_name = fields.Char(string='Owner Name')
    fax = fields.Char(string='Fax')
    sales_note = fields.Char(string='Sales Note')
    rma_note = fields.Char(string='RMA Note')
    credit_note = fields.Char(string='Credit Note')
    acct_note = fields.Char(string='Acct Note')
    post_days = fields.Char(string='Post Days')
    giacc = fields.Char(string='GIAcc')
    limit = fields.Char(string='Limit')
    tmdisday = fields.Char(string='TmdisDay')
    tmnetday = fields.Char(string='TmnetDay')
    tmdisrate = fields.Char(string='TmdisRate')
    copypkup = fields.Char(string='CopyPKup')
    copyinv = fields.Char(string='CopyInv')
    copywhs_v = fields.Char(string='CopyWhs - V')
    copywhs_r = fields.Char(string='CopyWhs - R')
    startdate = fields.Char(string='StartDate')
    vndtype = fields.Char(string='VndType')
    holdpay = fields.Char(string='HoldPay')
    daystoclr = fields.Char(string='Daystoclr')
    credline = fields.Char(string='Credline')
    rotation = fields.Char(string='Rotation')
    asigner = fields.Char(string='Asigner')
    other = fields.Char(string='Other')
    nondisagr = fields.Char(string='Nondisagr')
    ndaexpire = fields.Char(string='Ndaexpire')
    pay_type = fields.Char(string='Pay Type')
    pay_method = fields.Char(string='Pay Method')
    rem_email = fields.Char(string='Rem Email')
    rma_phone = fields.Char(string='RMA Phone')
    rma_fax = fields.Char(string='RMA Fax')
    rma_attn = fields.Char(string='RMA Attn')
    rma_email = fields.Char(string='RMA Email')
    caddr1 = fields.Char(string='CAddr1')
    caddr2 = fields.Char(string='CAddr2')
    ccity = fields.Char(string='CCity')
    cstate = fields.Char(string='CState')
    czip = fields.Char(string='CZip')
    rma1_addr1 = fields.Char(string='RMA1 Addr1')
    rma1_addr2 = fields.Char(string='RMA1 Addr2')
    rma1_city = fields.Char(string='RMA1 City')
    rma1_state = fields.Char(string='RMA1 State')
    rma1_zip = fields.Char(string='RMA1 ZIP')
    rma1_cont = fields.Char(string='RMA1 cont')
    credit_line = fields.Char(string='Credit Line')
    insurance = fields.Char(string='Insurance')
    d_b_no = fields.Char(string='D & B No.')
    d_b_rating = fields.Char(string='D & B Rating')
    credit_reference_a = fields.Char(string='Credit Reference (a)')
    credit_reference_b = fields.Char(string='Credit Reference (b)')
    credit_reference_c = fields.Char(string='Credit Reference (c)')
    bank_info = fields.Char(string='Bank Info')
    re_sell_certificate = fields.Char(string='Re-sell Certificate')
    si_min_max = fields.Char(string='SI MIN/MAX')
    si_expired = fields.Char(string='SI Expired')
    si_agent = fields.Char(string='SI AGENT')
    si_polcy = fields.Char(string='SI POLCY#')
    si_covrg = fields.Char(string='SI COVRG')
    si_dducb = fields.Char(string='SI DDUCB')
    si_exp_d = fields.Char(string='SI EXP. D')
    new_text = fields.Char(string='New Text')
    company_name = fields.Char(string='Company Name')
    opend = fields.Char(string='Opend')
    term = fields.Char(string='Term')
    c_limit = fields.Char(string='C Limit')
    hicred = fields.Char(string='Hicred')
    remarks = fields.Char(string='Remarks')
    period = fields.Char(string='Period')
    sales = fields.Char(string='$Sales')
    profit = fields.Char(string='Profit')
    p_margin = fields.Char(string='P_Margin')
    cash = fields.Char(string='Cash')
    c_ratio = fields.Char(string='C Ratio')
    li_nw = fields.Char(string='LI/NW')
    s_wc = fields.Char(string='S/WC')
    s_invent = fields.Char(string='S/INVENT')
    ar_s_365 = fields.Char(string='AR/S*365')
    remark = fields.Char(string='REMARK')
    president = fields.Char(string='President')
    ceo_cfo = fields.Char(string='CEO/CFO')
    authorized_purchaser = fields.Char(string='Authorized Purchaser')
    account_payable_contact_name = fields.Char(string='Account Payable Contact Name')
    this_company_is_a = fields.Selection(string='This company is a ', selection=[['sole_proprietorship', 'Sole Proprietorship'], ['partnership', 'Partnership'], ['llc', 'LLC'], ['corporation', 'Corporation']])
    date_business_was_founded = fields.Char(string='Date business was founded')
    personal_guarantee = fields.Boolean(string='Personal Guarantee')
    ssn = fields.Char(string='SSN')
    credit_card = fields.Text(string='Credit Card')
    business_category = fields.Selection(string='Business Category', selection=[['system_integrator', 'System Integrator'], ['distributor', 'Distributor'], ['retail_store', 'Retail Store'], ['corporate_reseller', 'Corporate Reseller'], ['var_system_consultant', 'VAR/System Consultant'], ['e_commerce', 'E-Commerce'], ['dealer', 'Dealer'], ['oem', 'OEM'], ['educational_reseller', 'Educational Reseller'], ['exporter', 'Exporter'], ['other', 'Other']])
    employee_s_amount = fields.Selection(string='Employee(s) amount', selection=[['1_5', '1-5'], ['6_10', '6-10'], ['11_20', '11-20'], ['21_50', '21-50'], ['51_100', '51-100'], ['101_300', '101-300'], ['300', '300+']])
    total_revenue_last_year = fields.Selection(string='Total revenue last year', selection=[['less_than_100_000', 'Less than $100,000'], ['100_000_499_999', '$100,000-$499,999'], ['500_000_999_999', '$500,000-$999,999'], ['1_000_000_4_999_999', '$1,000,000-$4,999,999'], ['5_000_000_9_999_999', '$5,000,000-$9,999,999'], ['10_000_000_49_999_999', '$10,000,000-$49,999,999'], ['50_000_000_100_000_000', '$50,000,000-$100,000-000'], ['10_000_000', '$10,000,000+']])
    there_is_a_parent_company_yes = fields.Boolean(string='There is a parent company (yes)')
    parent_company_name = fields.Char(string='Parent Company - Name')
    parent_company_address = fields.Char(string='Parent Company - Address')
    parent_company_guarantee_debts_yes = fields.Boolean(string='Parent Company guarantee debts (yes)')
    number_of_branch_office_s = fields.Char(string='Number of branch office(s)')
    branch_office_address = fields.Text(string='Branch office address')
    how_did_you_find_out_about_ma_labs = fields.Selection(string='How did you find out about Ma Labs', selection=[['trade_show_ces', 'Trade Show - CES'], ['trade_show_cebit', 'Trade Show - CeBIT'], ['trade_show_computex_taipei', 'Trade Show - Computex Taipei'], ['trade_show_other', 'Trade Show - Other'], ['referred_by_another_company', 'Referred by another company'], ['advertisement_print_ad', 'Advertisement - Print Ad'], ['advertisement_online', 'Advertisement - Online'], ['advertisement_other', 'Advertisement - Other']])
    ups_account = fields.Char(string='UPS Account #')
    fedex_account = fields.Char(string='FedEx Account #')
    contact_name = fields.Char(string='Contact Name')