from datetime import datetime, timezone, date, time, timedelta
import logging

import pytz

from odoo import models, fields, api, _, exceptions

_logger = logging.getLogger(__name__)


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
            if self.env.user.tz or r.create_uid.tz:
                tz = self.env.user.tz or r.create_uid.tz
                local = pytz.timezone(tz)
                create_date_local = datetime.fromtimestamp(r.create_date.timestamp(), tz=timezone(local._utcoffset))

                if r.create_uid:
                    r.create_date_display = create_date_local.isoformat(' ')[:11] + _('Daily Report') + ' From ' + r.create_uid.name + ' ' + WEEK.get(create_date_local.weekday())
                else:
                    r.create_date_display = 'Removed'
            else:
                raise exceptions.Warning(_('Please set your timezone in your Preference first.'))

    def unlink(self):
        if self.state == 'submitted':
            raise exceptions.Warning(_('Can\'t Delete Submitted report'))
        else:
            return super(DailyReport, self).unlink()

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

    def action_remind(self):
        """ Checking report status for each user, and send a remind email if the report for this day still didn't submitted """
        start = datetime.combine(date.today(), time(hour=7, minute=30))
        end = datetime.combine(date.today(), time(hour=7, minute=41))
        now = datetime.now()
        if start < now and end > now:

            today = fields.Datetime.to_datetime(fields.Date.today().isoformat())

            template = self.env.ref('daily_newbiiz.email_template_daily_report', raise_if_not_found=False)

            admins = self.env.ref('base.group_system').users.ids
            managers = self.env.ref('project.group_project_manager').users.ids
            for user in self.env.ref('project.group_project_user').users:
                if user.id not in admins and user.id not in managers:
                    if len(self.search((
                        ('state', '=', 'submitted'),
                        ('create_date', '>=', today),
                        ('create_date', '<', today + timedelta(days=1)),
                        ('user_id', '=', user.id),
                    ))) == 0:
                        if not user.email:
                            _logger.info(_("Cannot send email: user %s has no email address.") % user.name)
                            continue
                        with self.env.cr.savepoint():
                            template.with_context(lang=user.lang).send_mail(user.id, force_send=True, raise_exception=True)
                        _logger.info("Daily Report Remind email sent for user <%s> to <%s>", user.login, user.email)
                    else:
                        _logger.info("User <%s> has submitted the report for these day.", user.login)