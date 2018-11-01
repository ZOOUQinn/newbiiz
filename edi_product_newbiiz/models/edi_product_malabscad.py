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
    ma_labs_list = fields.Char(string='Ma Labs List #')
    item = fields.Char(string='Item #')
    barcode = fields.Char(string='Barcode')
    mfr_part = fields.Char(string='Mfr Part #')
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
    instant_rebate_start = fields.Datetime(string='Instant Rebate Start')
    instant_rebate_end = fields.Datetime(string='Instant Rebate End')
    website_description = fields.Html()
    image = fields.Char(string='Image URL')
    category = fields.Char()

    @api.model
    def target_values(self, record_vals):
        '''
        Modify the data before pass to
        :meth:`product.product.create` or :meth:`product.product.write`
        in order to create or update a record within the target model.

        :param record_vals: a dictionary of record(row) for this model
        :return: a dictionary which could passed to :meth:`product.product.create`
        '''
        product_vals = super().target_values(record_vals)

        image = record_vals.get('image', None)
        if image:
            try:
                r = requests.get(image)
                if r.status_code == 200:
                    image = base64.b64encode(r.content).decode("utf-8")
            except requests.exceptions.MissingSchema as err:
                pass

        product_vals.update({
            'length_cm': record_vals.get('length', 0),
            'width_cm': record_vals.get('width', 0),
            'height_cm': record_vals.get('height', 0),
            'weight': record_vals.get('weight', 0),
            'volume': record_vals.get('length', 0)*record_vals.get('width', 0)*record_vals.get('height', 0) / (100 ** 3),
            # 'usd_sales_price': record_vals.get('price', 0),
            # 'usd_cost': record_vals.get('cost', 0),
            # 'currency_rate': self.doc_id.currency_rate,
            # 'currency_rate_date': self.doc_id.currency_rate_datetime,
            'list_price': record_vals.get('price', 0),
            'standard_price': record_vals.get('cost', 0),
            'type': 'product',
            'image': image,
            'name': record_vals.get('name', None),
            'ma_labs_list': record_vals.get('ma_labs_list', None),
            'item': record_vals.get('item', None),
            'barcode': record_vals.get('barcode', None),
            'mfr_part': record_vals.get('mfr_part', None),
            'manufacturer': record_vals.get('manufacturer', None),
            'package': record_vals.get('package', None),
            'unit': record_vals.get('unit', None),
            'instant_rebate': record_vals.get('instant_rebate', None),
            'instant_rebate_start': record_vals.get('instant_rebate_start', None),
            'instant_rebate_end': record_vals.get('instant_rebate_end', None),
            # 'categ_id': record_vals.get('category', None), TODO
            'website_description': record_vals.get('website_description', None),
        })
        return product_vals


class EdiProductMalabsCADDocument(models.AbstractModel):
    """EDI product malabs_canada document model"""

    _name = 'edi.product.malabscad.document'
    _inherit = 'edi.product.document'
    _description = "Ma Labs CAD product CSV file"

    @api.model
    def product_record_values(self, data):
        """
        **overriding** Python method in 'edi.product.document' which should be abstract.

        :param data: bytes read form external csv file.
        :return: an iterable of dictionaries, each of which could
        passed to :meth:`edi.product.malabscad.record.create`.
        """
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
            d['category'] = d.get('PDL', None)
            d['ma_labs_list'] = d.get('Ma Labs List #', None)
            d['mfr_part'] = d.get('Mfr Part #', None)
            d['manufacturer'] = d.get('Manufacturer', None)
            d['unit'] = d.get('Unit', None)
            d['instant_rebate'] = d.get('Instant Rebate', None)
            d['length'] = d.get('Length', 0)
            d['item'] = d.get('item_no')

            try:
                fields.Datetime().from_string(d.get('Instant Rebate Start', None))
                d['instant_rebate_start'] = d.get('Instant Rebate Start', None)
            except ValueError:
                d['instant_rebate_start'] = fields.Datetime().now()

            try:
                fields.Datetime().from_string(d.get('Instant Rebate End', None))
                d['instant_rebate_end'] = d.get('Instant Rebate End', None)
            except ValueError:
                d['instant_rebate_end'] = fields.Datetime().to_string(fields.Datetime().from_string(d.get('instant_rebate_start', None)) + timedelta(days=30))

            for selection in PACKAGE:
                if selection[1] == d.get('Package', None):
                    d['package'] = selection[0]

            for key in (
                'Cost',
                'Instant Rebate',
                'Instant Rebate End',
                'Instant Rebate Start',
                'Length',
                'Ma Labs List #',
                'Manufacturer',
                'Mfr Part #',
                'PDL',
                'Package',
                'Sales Price',
                'Unit',
                'item_no',
            ):
                del d[key]

            data.append(d)
        return data
