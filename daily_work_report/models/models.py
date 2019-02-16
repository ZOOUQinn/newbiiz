from odoo import models, fields, api, _


class DailyReport(models.Model):
    _name = 'daily.report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'title'


    title = fields.Char(compute='_compute_title')
    write_date_display = fields.Char(string='Write Date', compute='_compute_write_date')
    state = fields.Selection(string="State", selection=[
        ('draft', 'Draft'),
        ('saved', 'Saved'),
        ('submitted', 'Submitted'),
    ], default='draft')
    keywords = fields.Char(string='Keywords')
    content = fields.Html(string='Content')

    def _compute_title(self):
        for r in self:
            r.title = '%s %s' % (
                _('Report on'),
                r.write_date_display,
            )

    @api.depends('write_date')
    def _compute_write_date(self):
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
            r.write_date_display = r.write_date.isoformat(' ')[:10] + ' ' + WEEK.get(r.write_date.weekday())

    @api.multi
    def submit(self):
        for rec in self:
            rec.state = 'submitted'

    @api.multi
    def write(self, vals):
        vals.update({'state': 'saved'})
        super(DailyReport, self).write(vals)
        return True