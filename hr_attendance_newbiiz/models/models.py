# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    text_message = fields.Text(string='Text Message')
    photos = fields.One2many(comodel_name='hr.avator',inverse_name='employee', string='Photos')
    image = fields.Binary(readonly=True)
    group = fields.Many2one(comodel_name='hr.employee.group',string='Group')

    @api.constrains('photos')
    def _onchange_photos(self):
        if self.photos:
            self.image = self.photos[0].photo


class Avator(models.Model):
    _name = 'hr.avator'
    _description = "Avator"

    name = fields.Char(compute='_compute_name')
    photo = fields.Binary(attachment=True)
    employee = fields.Many2one(comodel_name='hr.employee')

    @api.depends('employee')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.employee.name + ': ' + str(rec.id) if rec.employee and rec.id else 'None'


class EmployeeGroup(models.Model):

    _name = "hr.employee.group"
    _description = "Employee Group"

    name = fields.Char(string="Employee Group", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]