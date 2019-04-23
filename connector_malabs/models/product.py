# -*- coding: utf-8 -*-
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

    def _import_dependencies(self):
        record = self.malabs_record

        """ Import the dependencies for the record"""
        categ_name = record.get('category', None)
        categ_ids = self.env['product.category'].search([('name', '=', categ_name)])
        if len(categ_ids) == 0 and categ_name:
            self.env['product.category'].create({
                'name': categ_name
            })

        """ Import the manufacturer for the record"""
        manufacturer_name = record.get('manufacturer', None)
        manufacturer_ids = self.env['product.manufacturer'].search([('name', '=', manufacturer_name)])
        if len(manufacturer_ids) == 0 and manufacturer_name:
            self.env['product.manufacturer'].create({
                'name': manufacturer_name
            })

    def _after_import(self, binding):

        # Public Price List USD
        records_0 = self.env['product.pricelist.item'].search((
            ('product_tmpl_id', '=', binding.product_tmpl_id.id),
            ('pricelist_id', '=', self.env.ref('product_malabs.public_usd').id),
            ('compute_price', '=', 'fixed')
        ))
        data = {
            'applied_on': '1_product',
            'compute_price': 'fixed',
            'fixed_price': binding.usd_sales_price,
            'pricelist_id': self.env.ref('product_malabs.public_usd').id,
            'product_tmpl_id': binding.product_tmpl_id.id,
        }
        if records_0:
            for rec in records_0:
                rec.write(data)
        else:
            self.env['product.pricelist.item'].create(data)

        now = datetime.now()
        start = fields.Datetime().from_string(binding.instant_rebate_start)
        end = fields.Datetime().from_string(binding.instant_rebate_end)
        if binding.instant_rebate and float(binding.instant_rebate) and start < now and now < end:
            data.update({
                'date_start': binding.instant_rebate_start,
                'date_end': binding.instant_rebate_end,
                'compute_price': 'formula',
                'price_surcharge': binding.instant_rebate,
            })

            # USD
            records_1 = self.env['product.pricelist.item'].search((
                ('product_tmpl_id', '=', binding.product_tmpl_id.id),
                ('pricelist_id', '=', self.env.ref('product_malabs.regular_rebate_usd').id),
                ('compute_price', '=', 'formula'),
            ))
            data.update({
                'pricelist_id': self.env.ref('product_malabs.regular_rebate_usd').id,
                'base': 'pricelist',
                'base_pricelist_id': self.env.ref('product_malabs.public_usd').id
            })

            if records_1:
                for rec in records_1:
                    rec.write(data)
            else:
                self.env['product.pricelist.item'].create(data)

            # CAD
            records_2 = self.env['product.pricelist.item'].search((
                ('product_tmpl_id', '=', binding.product_tmpl_id.id),
                ('pricelist_id', '=', self.env.ref('product.list0').id)
            ))
            data.update({
                'pricelist_id': self.env.ref('product.list0').id,
                'price_surcharge': binding.instant_rebate / self.env.ref('base.USD').rate,
            })
            del data['base']
            del data['base_pricelist_id']
            if records_2:
                for rec in records_2:
                    rec.write(data)
            else:
                data.update({'product_tmpl_id': binding.product_tmpl_id.id})
                self.env['product.pricelist.item'].create(data)

    def _create(self, data):
        product = self.env['product.product'].search([('barcode', '=', data.get('barcode'))])
        if product:
            self._validate_data(data)
            model = self.model.with_context(connector_no_export=True)
            model = str(model).split('()')[0]
            binding = self.env[model].create({
                'odoo_id': product.id,
                'backend_id': self.backend_record.id,
            })
            binding.write(data)
            return binding
        else:
            return super(ProductProductImporter, self)._create(data)


class ProductProductImportMapper(Component):
    _name = 'malabs.product.import.mapper'
    _inherit = ['base.import.mapper']
    _apply_on = 'malabs.product.product'

    @mapping
    def category(self, rec):
        categ_id = self.env['product.category'].search([('name', '=', rec.get('category', None)),]).ids[0]
        return {'categ_id': categ_id}

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
            'usd_sales_price': record.get('price', 0.0),
            'usd_cost': record.get('cost', 0.0),
            'list_price': float(record.get('price', 0.0)) / self.env.ref('base.USD').rate,
            'currency_rate': self.env.ref('base.USD').rate,
            # 'currency_rate_date': '??', TODO: Figure out getting value from 'res.config.settings'.
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
            'unit': rec.get('unit', None),
            'package': rec.get('package', None),
            'default_code': rec.get('mfr_part'),
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
            'instant_rebate': float(rec.get('instant_rebate', 0)) if rec.get('instant_rebate') != '' else 0,
            'instant_rebate_start': rec.get('instant_rebate_start', None),
            'instant_rebate_end': rec.get('instant_rebate_end', None),
        }

    @mapping
    def tax(self, rec):
        return {
            'taxes_id': [(6, False, self.env.ref('l10n_ca.1_gst_sale_en').ids)],
            'supplier_taxes_id': [(5, False, False)]
        }

    @mapping
    def manufacturer(self, rec):
        manufacturer = self.env['product.manufacturer'].search([('name', '=', rec.get('manufacturer', None)), ]).ids[0]
        return {'manufacturer': manufacturer}
