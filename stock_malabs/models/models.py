from odoo import models, api, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    count_starting_with = fields.Integer(string='Starting With', default=1)

    @api.multi
    def serial_batch(self):
        self.ensure_one()
        count_start = self.count_starting_with
        count_stop = count_start + int(self.product_uom_qty - self.quantity_done)

        for i in list(range(count_start, count_stop)):
            move_line = self.env['stock.move.line'].create({
                'lot_name': str(i),
                'move_id': self.id,
                'product_uom_id': self.product_uom.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_id': self.product_id.id,
                'qty_done': 1,
            })
            self.picking_id.write({'move_line_ids': [(4, move_line.id, False)]})
        return True
