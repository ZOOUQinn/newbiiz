import datetime

from odoo import models, fields, api, _, exceptions


class DailyReport(models.Model):
    _name = 'daily.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'
    _order = 'create_date desc'

    user_id = fields.Many2one(comodel_name='res.users',
                              string='Submitter',
                              default=lambda self: self.env.uid,
                              index=True, track_visibility='always')
    title = fields.Char(compute='_compute_title')
    create_date_display = fields.Char(string='Create Date', compute='_compute_create_date')
    state = fields.Selection(string="State", selection=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
    ], default='draft', track_visibility='onchange')
    keywords = fields.Char(string='Keywords')
    working_hours = fields.Integer(string='Working hours', default=8)
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
            r.create_date_display = r.create_date.isoformat(' ')[:11] + _('Daily Report') + ' From ' + r.create_uid.name + ' ' + WEEK.get(r.create_date.weekday())

    @api.multi
    def unlink(self):
        if self.state == 'submitted':
            raise exceptions.Warning(_('Can\'t Delete Submitted report'))
        else:
            return super(DailyReport, self).unlink()

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'submitted':
            return 'daily_work_report.mt_daily_report'
        return super(DailyReport, self)._track_subtype(init_values)

    @api.model
    def create(self, vals):
        result = super(DailyReport, self).create(vals)
        partner_ids = []
        admins = self.env.ref('base.group_system').users.ids
        for user in self.env.ref('project.group_project_manager').users:
            if user.id not in admins:
                partner_ids.append(user.partner_id.id)
        result.message_subscribe(partner_ids=partner_ids)
        return result