import base64

from odoo import models


class ProviderUPSMalabs(models.Model):
    _inherit = 'delivery.carrier'

    def ups_send_shipping(self, pickings):
        res = super(ProviderUPSMalabs, self).ups_send_shipping(pickings)
        if self.ups_label_file_type == 'EPL':
            for picking in pickings:
                for message in picking.message_ids:
                    for attachment in message.attachment_ids:
                        if attachment.datas_fname.endswith('.EPL'):
                            lines = ''
                            line = ''
                            for b in base64.b64decode(attachment.datas):
                                if b != 10:
                                    line += chr(b)
                                else:
                                    if line.startswith('A514,'):
                                        line = ''
                                        continue
                                    if 'DESC' in line:
                                        line = line.replace('DESC', 'REF') + '\nA12,1084,0,3,1,1,N,"CUST PONO: %s"' % picking.name.split('/')[-1]

                                    line = line + '\n'
                                    lines += line
                                    line = ''
                            attachment.datas = base64.b64encode(lines.encode())

        return res
