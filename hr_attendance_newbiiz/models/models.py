# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    text_message = fields.Text(string='Text Message')
    photos = fields.One2many(comodel_name='hr.employee.avator',inverse_name='employee', string='Photos')
    image = fields.Binary(readonly=True)
    group = fields.Many2one(comodel_name='hr.employee.group',string='Group')

    @api.constrains('photos')
    def _constrains_photos(self):
        if self.photos:
            for photo in self.photos:
                if photo.used:
                    self.image = photo.photo


class Avator(models.Model):
    _name = 'hr.employee.avator'
    _description = "Avator"

    name = fields.Char()
    photo = fields.Binary(attachment=True)
    employee = fields.Many2one(comodel_name='hr.employee')
    used = fields.Boolean(string='Used?', default=True)

    @api.constrains('photo')
    def _constrains_photo(self):
        if self.photo:
            self.name = self.employee.name + '_' + str(self.id)

    @api.constrains('used')
    def _constrains_used(self):
        if self.used:
            for rec in self.env['hr.employee.avator'].search([('id','!=',self.id),('used','=',True)]):
                rec.used = False


class EmployeeGroup(models.Model):

    _name = "hr.employee.group"
    _description = "Employee Group"

    name = fields.Char(string="Employee Group", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]