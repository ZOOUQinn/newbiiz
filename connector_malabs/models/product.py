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
    _inherits = {'product.product': 'openerp_id'}
    _description = 'malabs product product'

    _rec_name = 'name'
    openerp_id = fields.Many2one(comodel_name='product.product',
                                 string='product',
                                 required=True,
                                 ondelete='cascade')
    backend_id = fields.Many2one(
        comodel_name='mc.backend',
        string='Malabs Backend',
        store=True,
        readonly=False,
        required=True,
    )

    slug = fields.Char('Slung Name')
    credated_at = fields.Date('created_at')
    weight = fields.Float('weight')


class ProductProductAdapter(Component):
    _apply_on = 'malabs.product.product'
    _inherit = ['malabs.adapter']
    _name = 'malabs.pruduct.adapter'
    _malabs_model = 'products'

    def search(self, filters=None, from_date=None, to_date=None):
        """ Search records according to some criteria and return a
        list of ids

        :rtype: list
        """
        if filters is None:
            filters = {}
        WOO_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'
        dt_fmt = WOO_DATETIME_FORMAT
        if from_date is not None:
            # updated_at include the created records
            filters.setdefault('updated_at', {})
            filters['updated_at']['from'] = from_date.strftime(dt_fmt)
        if to_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['to'] = to_date.strftime(dt_fmt)

        res = self._call(self.malabs.location)

        return res

    def read_image(self, id, image_name, storeview_id=None):
        return self._call('products',
                          [int(id), image_name, storeview_id, 'id'])


class ProductBatchImporter(Component):
    """ Import the MalabsCommerce Partners.

    For every partner in the list, a delayed job is created.
    """
    _apply_on = ['malabs.product.product']
    _inherit = ['malabs.delayed.batch.importer']
    _name = 'malabs.product.batch.importer'

    def run(self, filters=None):
        """ Run the synchronization """
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        record_ids = self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
        )
        _logger.info('search for malabs Products %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id, priority=30)


class ProductProductImporter(Component):
    _name = 'malabs.product.product.importer'
    _inherit = ['malabs.importer']
    _apply_on = ['malabs.product.product']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.malabs_record
        for malabs_category in record['categories']:
            self._import_dependency(malabs_category.get('id'), 'malabs.product.category')

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        # image_importer = self.unit_for(ProductImageImporter)
        # image_importer.run(self.malabs_id, binding.id)
        self.component(usage='image.importer').run(self.malabs_record, binding.id)
        return


class ProductImageImporter(Component):
    """ Import images for a record.

    Usually called from importers, in ``_after_import``.
    For instance from the products importer.
    """
    _name = 'malabs.product.image.importer'
    _inherit = ['base.importer']
    _usage = 'image.importer'

    def _sort_images(self, images):
        """ Returns a list of images sorted by their priority.
        An image with the 'image' type is the the primary one.
        The other images are sorted by their position.

        The returned list is reversed, the items at the end
        of the list have the higher priority.
        """
        if not images:
            return {}
        # place the images where the type is 'image' first then
        # sort them by the reverse priority (last item of the list has
        # the the higher priority)

    def _get_binary_image(self, image_data):
        url = image_data['src']
        return requests.get(url).content

    def run(self, malabs_record, binding_id):
        images = malabs_record.get('images')
        binary = None
        while not binary and images:
            binary = self._get_binary_image(images.pop())
        if not binary:
            return
        model = self.model.with_context(connector_no_export=True)
        binding = model.browse(binding_id)
        binding.write({'image': base64.b64encode(binary)})


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
        if rec.get('id', None):
            return {'malabs_id': rec['id']}

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
