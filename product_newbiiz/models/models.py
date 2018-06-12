from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # x_studio_field_6tXJu = fields.Char(string='Ma Labs List \#')
    # x_studio_field_UYxVl = fields.Char(string='Item #')
    # x_studio_field_BWwJH = fields.Char(string='Mfr Part #')
    # x_studio_field_LwlGR = fields.Char(string='Manufacturer')
    # x_studio_field_TML6a = fields.Selection(string='Package', selections=[('retail', 'RETAIL'), ('bulk', 'BULK')])
    # x_studio_field_0yhh4 = fields.Char(string='Unit')
    # x_studio_field_FkShp = fields.Float(string='Width(cm)')
    # x_studio_field_scAl6 = fields.Float(string='Height(cm)')
    # x_studio_field_40IN5 = fields.Float(string='Length(cm)')
    # x_studio_field_SmdFq = fields.Char(string='Instant Rebate')
    # x_studio_field_CTq8g = fields.Datetime(string='Instant Rebate Start')
    # x_studio_field_KGYbV = fields.Datetime(string='Instant Rebate End')
    # x_studio_field_HbNOx = fields.Html(string='Website Description')
    # x_studio_field_12pqb = fields.Float(string='Currency Rate')
    # x_studio_field_w1gf9 = fields.Float(string='Currency Rate Date')
    # x_studio_field_uqb5M = fields.Float(string='USD - Sales Price')
    # x_studio_field_JVAKN = fields.Float(string='USD - Cost')

    ma_labs_list_no = fields.Char(string='Ma Labs List \#')
    item_no = fields.Char(string='Item #')
    mfr_part_no = fields.Char(string='Mfr Part #')
    manufacturer = fields.Char(string='Manufacturer')

    # packaging_ids one2many product.packaging
    package = fields.Selection(string='Package', selection=[('retail', 'RETAIL'), ('bulk', 'BULK')])

    # uom_id(Unit of Measure) many2one product.uom
    unit = fields.Char(string='Unit')

    width = fields.Float(string='Width(cm)')
    height = fields.Float(string='Height(cm)')
    length = fields.Float(string='Length(cm)')
    instant_rebate = fields.Char(string='Instant Rebate')
    ir_start = fields.Datetime(string='Instant Rebate Start')
    ir_end = fields.Datetime(string='Instant Rebate End')
    description = fields.Html(string='Website Description')
    currency_rate = fields.Float(string='Currency Rate')
    currency_rate_date = fields.Datetime(string='Currency Rate Date')
    usd_sales_price = fields.Float(string='USD - Sales Price')
    usd_cost = fields.Float(string='USD - Cost')