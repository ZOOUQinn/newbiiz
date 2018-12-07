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

from odoo.addons.queue_job.job import job, related_action

from odoo import models, fields, api


class WooBinding(models.AbstractModel):

    """ Abstract Model for the Bindigs.

    All the models used as bindings between MalabsCommerce and OpenERP
    (``woo.res.partner``, ``woo.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'malabs.binding'
    _inherit = 'external.binding'
    _description = 'Malabs Binding (abstract)'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='mccsv.backend',
        string='Malabs Backend',
        required=True,
        ondelete='restrict',
    )

    malabs_id = fields.Char(string='ID on Malabs')

    _sql_constraints = [
        ('malabs_uniq', 'unique(backend_id, malabs_id)',
         'A binding already exists with the same Woo ID.'),
    ]

    @job
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on MalabsCommerce """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a MalabsCommerce record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=force)