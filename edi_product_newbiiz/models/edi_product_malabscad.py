"""EDI product tutorial

This example shows the code required to implement a simple EDI product
document format comprising a CSV file with a fixed list of columns:

* Product code
* Product description
* Product weight (in grams, optional)
* Product volume (in cubic centimetres, optional)
"""
import base64
import csv
from datetime import datetime, timedelta

import requests

from odoo import api, fields, models

PACKAGE = [('retail', 'RETAIL'), ('bulk', 'BULK')]

class EdiDocument(models.Model):
    """Extend ``edi.document`` to include EDI product tutorial records"""

    _inherit = 'edi.document'

    product_malabscad_ids = fields.One2many('edi.product.malabscad.record',
                                           'doc_id', string="Products")

    currency_rate = fields.Float(string='Currency Rate', default=1)
    currency_rate_datetime = fields.Datetime(string='Currency Rate Datetime')


class EdiProductMalabsCADRecord(models.Model):
    """EDI product tutorial record"""

    _name = 'edi.product.malabscad.record'
    _inherit = 'edi.product.record'
    _description = "Product"

    # name
    ma_labs_list_no = fields.Char(string='Ma Labs List #')
    item_no = fields.Char(string='Item #')
    barcode = fields.Char(string='Barcode')
    mfr_part_no = fields.Char(string='Mfr Part #')
    manufacturer = fields.Char(string='Manufacturer')
    package = fields.Selection(string='Package', selection=PACKAGE)
    unit = fields.Char(string='Unit')
    weight = fields.Float(string='Weight(lbs)', default=0)
    width = fields.Float(string='Width(cm)', default=0)
    height = fields.Float(string='Height(cm)', default=0)
    length = fields.Float(string='Length(cm)', default=0)
    price = fields.Float(string='Sales Price', default=0)
    cost = fields.Float(string='Cost', default=0)
    instant_rebate = fields.Char(string='Instant Rebate')
    ir_start = fields.Datetime(string='Instant Rebate Start')
    ir_end = fields.Datetime(string='Instant Rebate End')
    # website_description
    image = fields.Binary(string='Image')

    @api.model
    def _product_values(self, record_vals):
        product_vals = super()._product_values(record_vals)
        product_vals.update({
            'length': record_vals.get('length', 0),
            'width': record_vals.get('width', 0),
            'height': record_vals.get('height', 0),
        })
        product_vals.update({
            # 'barcode': record_vals['name'],
            'weight': record_vals.get('weight', 0) * 0.45359237,
            'volume': record_vals.get('length', 0)*record_vals.get('width', 0)*record_vals.get('height', 0) / (100 ** 3),
            'usd_sales_price': record_vals.get('price', 0),
            'usd_cost': record_vals.get('cost', 0),
            'currency_rate': self.doc_id.currency_rate,
            'currency_rate_date': self.doc_id.currency_rate_datetime,
            'list_price': record_vals.get('price', 0),
            'standard_price': record_vals.get('cost', 0),
        })
        del product_vals['price']
        return product_vals


class EdiProductMalabsCADDocument(models.AbstractModel):
    """EDI product tutorial document model"""

    _name = 'edi.product.malabscad.document'
    _inherit = 'edi.product.document'
    _description = "Ma Labs CAD product CSV file"

    @api.model
    def _record_values(self, data):
        reader_origin = csv.reader(data.decode().splitlines())
        # TODO: recode later
        reader = []
        for row in reader_origin:
            reader.append(row)

        data = []
        keys = reader[0]
        values = reader[1:]
        for val in values:
            d = {}
            i = 0
            for key in keys:
                d[key] = val[i]
                i += 1

            d['price'] = d.get('Sales Price', None)
            d['cost'] = d.get('Cost', None)
            d['description'] = d.get('website_description', None)
            try:
                r = requests.get(d.get('image'))
                if r.status_code == 200:
                    d['image'] = base64.b64encode(r.content).decode("utf-8")
                else:
                    del d['image']
            except requests.exceptions.MissingSchema as err:
                del d['image']
            d['type'] = d.get('Product Type', None)
            d['categ_id'] = d.get('Internal Category', None)
            d['ma_labs_list_no'] = d.get('Ma Labs List #', None)
            d['mfr_part_no'] = d.get('Mfr Part #', None)
            d['manufacturer'] = d.get('Manufacturer', None)
            # d['package'] = d.get('Package', None)
            d['unit'] = d.get('Unit', None)
            d['instant_rebate'] = d.get('Instant Rebate', None)

            try:
                fields.Datetime().from_string(d.get('Instant Rebate Start', None))
                d['ir_start'] = d.get('Instant Rebate Start', None)
            except ValueError:
                d['ir_start'] = fields.Datetime().now()

            try:
                fields.Datetime().from_string(d.get('Instant Rebate End', None))
                d['ir_end'] = d.get('Instant Rebate End', None)
            except ValueError:
                d['ir_end'] = fields.Datetime().to_string(fields.Datetime().from_string(d.get('ir_start', None)) + timedelta(days=30))

            d['length'] = d.get('Length', 0)

            for selection in PACKAGE:
                if selection[1] == d.get('Package', None):
                    d['package'] = selection[0]

            data.append(d)
        return data

    @api.multi
    def execute(self, doc):
        url = 'https://openexchangerates.org/api/latest.json'
        symbols = 'CAD'
        params = {'app_id': '477b87e78dd244a3b388a81951d869b1', 'base': 'USD', 'symbols': symbols}
        r = requests.get(url=url, params=params)
        res = r.json()
        doc.currency_rate, doc.currency_rate_datetime = res.get('rates').get(symbols, 0), str(datetime.utcfromtimestamp(res.get('timestamp', None)))
        doc.execute_records()