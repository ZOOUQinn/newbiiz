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
import platform

from odoo import models, api, fields, _


class mc_backend(models.Model):
    _name = 'mc.backend'
    _inherit = 'connector.backend'
    _description = 'Malabs Backend Configuration'
    name = fields.Char(string='Name', required=True)
    _backend_type = 'malabs'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='Status', readonly=True, default='draft')

    # Attachments (e.g. CSV files)
    input_ids = fields.One2many('ir.attachment', 'res_id',
                                domain=[('res_field', '=', 'input_ids')],
                                string="Input Attachments")
    output_ids = fields.One2many('ir.attachment', 'res_id',
                                 domain=[('res_field', '=', 'output_ids')],
                                 string="Output Attachments")
    input_count = fields.Integer(string="Input Count", compute='_compute_input_count', store=True)
    output_count = fields.Integer(string="Output Count", compute='_compute_output_count', store=True)

    @api.depends('input_ids', 'input_ids.res_id')
    def _compute_input_count(self):
        """Compute number of input attachments (for UI display)"""
        for doc in self:
            doc.input_count = len(doc.input_ids)

    @api.depends('output_ids', 'output_ids.res_id')
    def _compute_output_count(self):
        """Compute number of output attachments (for UI display)"""
        for doc in self:
            doc.output_count = len(doc.output_ids)

    @api.multi
    def action_view_inputs(self):
        """View input attachments"""
        self.ensure_one()
        action = self.env.ref('connector_malabs.document_attachments_action').read()[0]
        action['display_name'] = _("Inputs")
        action['domain'] = [('res_field', '=', 'input_ids'),
                            ('res_id', '=', self.id)]
        action['context'] = {'default_res_field': 'input_ids',
                             'default_res_id': self.id}
        return action

    @api.multi
    def action_view_outputs(self):
        """View output attachments"""
        self.ensure_one()
        action = self.env.ref('connector_malabs.document_attachments_action').read()[0]
        action['display_name'] = _("Outputs")
        action['domain'] = [('res_field', '=', 'output_ids'),
                            ('res_id', '=', self.id)]
        action['context'] = {'default_res_field': 'output_ids',
                             'default_res_id': self.id}
        return action

    def import_data(self, malabs_model):
        self.env[malabs_model].import_batch(self)

    @api.multi
    def import_product(self):
        self.ensure_one()
        return self.import_data('malabs.product.product')

    @api.multi
    def import_products(self):
        """ Import categories from all websites """
        for backend in self:
            backend.import_product()
            backend.state = 'done'
        return True