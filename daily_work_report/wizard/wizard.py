import datetime

from odoo import models, api, fields, exceptions, _


class Diary_Wizard(models.TransientModel):
    _name = 'daily.report_wizard'

    @api.multi
    def submit(self):
        report = self.env['daily.report'].browse(self._context.get('active_id'))
        today = fields.Datetime.to_datetime(fields.Date.today().isoformat())

        if report.user_id.id != self.env.uid:
            raise exceptions.Warning(_('Please submit your own report.'))
        elif self.env['daily.report'].search((
                ('state', '=', 'submitted'),
                ('create_date', '>=', today),
                ('create_date', '<', today + datetime.timedelta(days=1)),
                ('user_id', '=', self.env.uid),
        )):
            raise exceptions.Warning(_('Only ONE report for each day.'))
        else:
            self.env['daily.report'].browse(self._context.get('active_id')).state = 'submitted'

        return True
