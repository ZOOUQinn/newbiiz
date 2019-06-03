# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):

        if not kwargs.get('email_from', None):
            kwargs.update({'email_from': self.env.user.company_id.email})

        if not kwargs.get('reply_to', None):
            kwargs.update({'reply_to': self.env.user.email})

        return super(MailThread, self).message_post(**kwargs)
