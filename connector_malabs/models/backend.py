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
import logging
import platform
from datetime import datetime, timedelta

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

class mccsv_backend(models.Model):
    _name = 'mccsv.backend'
    _inherit = 'connector.backend'
    _description = 'Malabs CSV Source Backend'
    _order = 'create_date DESC'
    name = fields.Char(string='Name', required=True)
    _backend_type = 'malabs'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', readonly=True, default='draft')

    csv_file = fields.Binary(string='CSV File')

    def import_data(self, malabs_model):

        # if platform.system() == 'Linux':
        #     self.env[malabs_model].with_delay().import_batch(self)
        # else:
        #     self.env[malabs_model].import_batch(self)
        self.env[malabs_model].import_batch(self)

    @api.multi
    def import_product(self):
        self.ensure_one()
        self.import_data('malabs.product.product')
        return True

    @api.multi
    def import_products(self):
        """ Import categories from all websites """
        for backend in self:
            if backend.state == 'draft':
                backend.import_product()
                backend.state = 'done'
        return True

    def import_products_cron(self, id):
        rec = self.browse([id])
        if rec.state == 'draft':
            rec.import_product()
            rec.state = 'done'

    @api.model
    def send_to(self, name, f, launch=False):
        _logger.info(name)
        backend_id = self.create({
            'name': name,
            'csv_file': f.data,
        }).id
        if launch:
            code = '''
model.import_products_cron(%s)
            ''' % backend_id
            self.env['ir.cron'].create({
                'name': 'Import Product from %s' % (name),
                'model_id': self.env.ref('connector_malabs.model_mccsv_backend').id,
                'state': 'code',
                'code': code,
                'interval_number': 1,
                'interval_type': 'hours',
                'numbercall': 1,
                'nextcall': fields.Datetime().to_string(datetime.now() + timedelta(minutes=1))
            })
        return True