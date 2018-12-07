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
        """ Import the dependencies for the record"""
        record = self.malabs_record
        for malabs_category in record['categories']:
            self._import_dependency(malabs_category.get('id'), 'malabs.product.category')


class ProductProductImportMapper(Component):
    _name = 'malabs.product.import.mapper'
    _inherit = ['base.import.mapper']
    _apply_on = 'malabs.product.product'

    direct = [
        ('description', 'description'),
        ('weight', 'weight'),
    ]

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

    # @mapping
    # def categories(self, record):
    #     if record:
    #         malabs_categories = record['categories']
    #         binder = self.binder_for('malabs.product.category')
    #         category_ids = []
    #         main_categ_id = None
    #         for malabs_category in malabs_categories:
    #             malabs_category_id = malabs_category.get('id')
    #             cat_id = binder.to_openerp(malabs_category_id, unwrap=True)
    #             if cat_id is None:
    #                 raise MappingError("The product category with "
    #                                    "malabs id %s is not imported." %
    #                                    malabs_category_id)
    #             category_ids.append(cat_id)
    #         if category_ids:
    #             main_categ_id = category_ids.pop(0)
    #         result = {'malabs_categ_ids': [(6, 0, category_ids)]}
    #         if main_categ_id:  # OpenERP assign 'All Products' if not specified
    #             result['categ_id'] = main_categ_id
    #         return result

    @mapping
    def price(self, record):
        if record:
            return {'list_price': record and record.get('price', None) or 0.0}

    @mapping
    def sale_price(self, record):
        if record:
            return {'standard_price': record and record.get('cost', None) or 0.0}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def malabs_id(self, rec):
        if rec.get('barcode', None):
            return {'malabs_id': rec['barcode']}

    @mapping
    def custom(self, rec):
        record ={
            'weight': rec.get('weight', 0),
            'width_cm': rec.get('width', 0),
            'height_cm': rec.get('height', 0),
            'website_description': rec.get('website_description', None),
            'ma_labs_list': rec.get('ma_labs_list', None),
            'mfr_part': rec.get('mfr_part', None),
            'manufacturer': rec.get('manufacturer', None),
            'unit': rec.get('unit', None),
            'instant_rebate': rec.get('instant_rebate', None),
            'length_cm': rec.get('length', None),
            'item': rec.get('item', None),
            'instant_rebate_start': rec.get('instant_rebate_start', None),
            'instant_rebate_end': rec.get('instant_rebate_end', None),
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
