from datetime import datetime, timezone, timedelta

import pytz

from odoo import models, api, fields, exceptions, _


class Diary_Wizard(models.TransientModel):
    _name = 'daily.report_wizard'
    _description = 'Report Wizard'

    def submit(self):
        report = self.env['daily.report'].browse(self._context.get('active_id'))

        local = pytz.timezone(self.env.user.tz)

        today = fields.Datetime.to_datetime(
            datetime.fromtimestamp(
                fields.Datetime.now().timestamp(),
                tz=timezone(local._utcoffset)
            ).isoformat(' ')[:10]
        ) - local._utcoffset

        if report.user_id.id != self.env.uid:
            raise exceptions.Warning(_('Please submit your own report.'))
        elif self.env['daily.report'].search((
                ('state', '=', 'submitted'),
                ('create_date', '>=', today),
                ('create_date', '<', today + timedelta(days=1)),
                ('user_id', '=', self.env.uid),
        )):
            raise exceptions.Warning(_('Only ONE report for each day.'))
        else:
            sth = self.env['daily.report'].browse(self._context.get('active_id'))
            sth.state = 'submitted'

        return True
