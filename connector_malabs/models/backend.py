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
import csv
import logging
from datetime import datetime, timedelta
from io import StringIO

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

CODE = '''
model.import_products_cron(%s)
'''

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
            self.env['ir.cron'].create({
                'name': 'Import Product from %s' % (name),
                'model_id': self.env.ref('connector_malabs.model_mccsv_backend').id,
                'state': 'code',
                'code': CODE % backend_id,
                'interval_number': 1,
                'interval_type': 'hours',
                'numbercall': 1,
                'nextcall': fields.Datetime().to_string(datetime.now() + timedelta(minutes=1))
            })
        return True

    def create_edi_report(self):
        products = self.env['product.product'].search((('active', '=', True), ('location_id', '=', '13'), ('manufacturer', '=', 'Seagate')))
        data = []
        for product in products:
            quants = self.env['stock.quant'].search((('product_id', '=', product.id),))
            if quants:
                quantity = 0.0
                for quant in quants:
                    if quant.location_id.id == 13:
                        quantity += quant.quantity
                if quantity > 0:
                    data.append({
                        'display_name': product.display_name,
                        'quantity': quantity,
                        'sku': product.mfr_part,
                    })

        csvfile = StringIO()
        fieldnames = ['itmno', 'code', 'ma_itmno', 'country', 'qty', 'date', 'branch', 'distributor']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for cr in data:
            writer.writerow({
                'itmno': 'Seagate',
                'code': '36',
                'ma_itmno': cr['sku'],
                'country': 'US',
                'qty': cr['quantity'],
                'date': datetime.now().strftime("%d-%b-%y"),
                'branch': '1001',
                'distributor': 'MALABS'
            })

        attach_fname = 'Seagate_edi_Inventory_rpt__' + datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + '.csv'
        attachment = self.env['ir.attachment'].create({
            'name': attach_fname,
            'datas': base64.b64encode(csvfile.getvalue().encode('utf-8')),
            'datas_fname': attach_fname,
            'res_model': 'mccsv.backend',
            'res_id': 0,
            'type': 'binary',
        })

        template = self.env.ref('connector_malabs.email_template_edi_report', raise_if_not_found=False)

        admins = self.env.ref('base.group_system').users.ids
        for user in self.env.ref('sales_team.group_sale_manager').users:
            if user.id not in admins:
                with self.env.cr.savepoint():
                    template.with_context(lang=user.lang).send_mail(user.id, force_send=True, raise_exception=True, email_values={'attachment_ids': [attachment.id]})
                    _logger.info("EDI Report email sent for user <%s> to <%s>", user.login, user.email)

        return True