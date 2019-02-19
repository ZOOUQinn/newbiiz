import datetime

from odoo import models, fields, api, _, exceptions


class DailyReport(models.Model):
    _name = 'daily.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'

    user_id = fields.Many2one(comodel_name='res.users',
                              string='Submitter',
                              default=lambda self: self.env.uid,
                              index=True, track_visibility='always')
    title = fields.Char(compute='_compute_title')
    create_date_display = fields.Char(string='Create Date', compute='_compute_create_date')
    state = fields.Selection(string="State", selection=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
    ], default='draft')
    keywords = fields.Char(string='Keywords')
    content = fields.Html(string='Content')

    def _compute_title(self):
        for r in self:
            r.title = '%s %s' % (
                _('Report on'),
                r.create_date_display,
            )

    @api.depends('create_date')
    def _compute_create_date(self):
        WEEK = {
            0: _('Monday'),
            1: _('Tuesday'),
            2: _('Wednesday'),
            3: _('Thursday'),
            4: _('Friday'),
            5: _('Saturday'),
            6: _('Sunday')
        }

        for r in self:
            r.create_date_display = r.create_date.isoformat(' ')[:11] + WEEK.get(r.create_date.weekday())

    @api.multi
    def unlink(self):
        if self.state == 'submitted':
            raise exceptions.Warning(_('Can\'t Delete Submitted report'))
        else:
            return super(DailyReport, self).unlink()