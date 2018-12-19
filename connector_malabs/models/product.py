﻿# -*- coding: utf-8 -*-
#
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.techreceptives.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import base64
import logging
from datetime import datetime

import requests
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from odoo import models, fields, _

_logger = logging.getLogger(__name__)

def get_rate(base='USD', symbols='CAD'):
    url = 'https://openexchangerates.org/api/latest.json'
    params = {'app_id': '477b87e78dd244a3b388a81951d869b1', 'base': base, 'symbols': symbols}
    r = requests.get(url=url, params=params)
    res = r.json()
    return res.get('rates').get(symbols, 0), str(datetime.utcfromtimestamp(res.get('timestamp', None)))

RATE, RATE_TIME = get_rate()

class MalabsProductProduct(models.Model):
    _name = 'malabs.product.product'
    _inherit = 'malabs.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'malabs product product'

    _rec_name = 'name'
    odoo_id = fields.Many2one(comodel_name='product.product',
                                 string='product',
                                 required=True,
                                 ondelete='cascade')
    backend_id = fields.Many2one(
        comodel_name='mccsv.backend',
        string='Malabs Backend',
        store=True,
        readonly=False,
        required=True,
    )


class ProductProductAdapter(Component):
    _apply_on = 'malabs.product.product'
    _inherit = ['malabs.adapter']
    _name = 'malabs.pruduct.adapter'
    _malabs_model = 'products'



class ProductBatchImporter(Component):
    """ Import the MalabsCommerce Partners.

    For every partner in the list, a delayed job is created.
    """
    _apply_on = ['malabs.product.product']
    _inherit = ['malabs.delayed.batch.importer']
    _name = 'malabs.product.batch.importer'


class ProductProductImporter(Component):
    _name = 'malabs.product.product.importer'
    _inherit = ['malabs.importer']
    _apply_on = ['malabs.product.product']

    def _after_import(self, binding):

        # Todo category

        # Price List
        now = datetime.now()
        start = fields.Datetime().from_string(binding.instant_rebate_start)
        end = fields.Datetime().from_string(binding.instant_rebate_end)
        if binding.instant_rebate and float(binding.instant_rebate) and start < now and now < end:
            records = self.env['product.pricelist.item'].search((
                ('product_tmpl_id', '=', binding.product_tmpl_id.id),
                ('pricelist_id', '=', self.env.ref('product_malabs.regular_rebate').id)
            ))
            data = {
                'applied_on': '1_product',
                'date_start': binding.instant_rebate_start,
                'date_end': binding.instant_rebate_end,
                'compute_price': 'fixed',
                'fixed_price': binding.list_price + float(binding.instant_rebate),
                'pricelist_id': self.env.ref('product_malabs.regular_rebate').id
            }
            if records:
                for rec in records:
                    rec.write(data)
            else:
                data.update({'product_tmpl_id': binding.product_tmpl_id.id})
                self.env['product.pricelist.item'].create(data)


class ProductProductImportMapper(Component):
    _name = 'malabs.product.import.mapper'
    _inherit = ['base.import.mapper']
    _apply_on = 'malabs.product.product'

    # @mapping
    # def in_stock(self, record):
    #     if record:
    #         return {'in_stock': record['in_stock']}

    @mapping
    def name(self, record):
        if record:
            return {'name': record['name']}

    @mapping
    def type(self, record):
        if record:
            return {'type': 'product'}

    @mapping
    def price(self, record):
        return {
            'currency_rate': RATE,
            'currency_rate_date': RATE_TIME,
            'usd_sales_price': record.get('price', 0.0),
            'usd_cost': record.get('cost', 0.0),
            'list_price': float(record.get('price', 0.0)) * RATE,
            'standard_price': float(record.get('cost', 0.0)) * RATE,
        }

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def malabs_id(self, rec):
        if rec.get('barcode', None):
            return {'malabs_id': rec['barcode']}

    @mapping
    def custom(self, rec):
        record = {
            'website_description': rec.get('website_description', None),
            'ma_labs_list': rec.get('ma_labs_list', None),
            'item': rec.get('item', None),
            'mfr_part': rec.get('mfr_part', None),
            'manufacturer': rec.get('manufacturer', None),
            'unit': rec.get('unit', None),
            'package': rec.get('package', None),
        }

        if rec.get('barcode', None) and rec['barcode'] != '':
            record.update({'barcode': rec['barcode']})

        return record

    @mapping
    def image(self, rec):
        if rec.get('image', None):
            image_url = rec['image']
            i = 0
            while i < 5:
                i += 1
                try:
                    r = requests.get(image_url)
                    if r.status_code == 200:
                        image = base64.b64encode(r.content).decode("utf-8")
                        _logger.info(msg=_('Get Image from %s' % (image_url,)))
                        return {'image': image}
                    msg = ' '.join((str(i), image_url, str(r.status_code)))
                except Exception as err:
                    msg = ' '.join((str(i), image_url, str(err)))

                _logger.warning(msg=msg)

    @mapping
    def weight(self, rec):
        return {
            'weight': float(rec.get('weight', 0)) * 0.45359237 / (int(rec.get('unit', 1)) if int(rec.get('unit')) else 1)
        }

    @mapping
    def volume(self, rec):
        length_cm = float(rec.get('length', 0)) * 2.54
        width_cm = float(rec.get('width', 0)) * 2.54
        height_cm = float(rec.get('height', 0)) * 2.54
        return {
            'length_cm': length_cm,
            'width_cm': width_cm,
            'height_cm': height_cm,
            'volume': length_cm * width_cm * height_cm / (100 ** 3)
        }

    @mapping
    def rebate(self, rec):
        return {
            'instant_rebate': float(rec.get('instant_rebate', 0)) * RATE if rec.get('instant_rebate') != '' else 0,
            'instant_rebate_start': rec.get('instant_rebate_start', None),
            'instant_rebate_end': rec.get('instant_rebate_end', None),
        }

    @mapping
    def tracking(self, rec):
        return {'tracking': 'serial'}

    @mapping
    def tax(self, rec):
        return {
            'taxes_id': [(6, False, self.env.ref('l10n_ca.1_gst_sale_en').ids)],
            'supplier_taxes_id': [(5, False, False)]
        }