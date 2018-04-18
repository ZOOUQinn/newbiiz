# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = "hr.employee"

    text_message = fields.Text(string='Text Message')