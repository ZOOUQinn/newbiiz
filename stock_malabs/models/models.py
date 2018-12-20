from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def skip_serial(self):
        move_line = self.env['stock.move.line'].create({
            'move_id': self.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty - self.quantity_done,
            'qty_done': self.product_uom_qty - self.quantity_done,
        })
        self.picking_id.write({'move_line_ids': [(4, move_line.id, False)]})
        return True


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if self.purchase_id:
            if not self.move_lines and not self.move_line_ids:
                raise UserError(_('Please add some lines to move'))

            # If no lots when needed, raise error
            picking_type = self.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                raise UserError(_('You cannot validate a transfer if you have not processed any quantity. You should rather cancel the transfer.'))

            if no_quantities_done:
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
                view = self.env.ref('stock.view_overprocessed_transfer')
                wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.overprocessed.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if self._check_backorder():
                return self.action_generate_backorder_wizard()
            self.action_done()
            return
        else:
            return super(Picking, self).button_validate()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        if all(move_line.picking_id.purchase_id for move_line in self):
            ml_to_delete = self.env['stock.move.line']
            for ml in self:
                # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
                uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding,
                                      rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                              defined on the unit of measure "%s". Please change the quantity done or the \
                                              rounding precision of your unit of measure.') % (
                    ml.product_id.display_name, ml.product_uom_id.name))

                qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done_float_compared > 0:
                    pass
                elif qty_done_float_compared < 0:
                    raise UserError(_('No negative quantities allowed'))
                else:
                    ml_to_delete |= ml
            ml_to_delete.unlink()

            # Now, we can actually move the quant.
            done_ml = self.env['stock.move.line']
            for ml in self - ml_to_delete:
                if ml.product_id.type == 'product':
                    Quant = self.env['stock.quant']
                    rounding = ml.product_uom_id.rounding

                    # if this move line is force assigned, unreserve elsewhere if needed
                    if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty,
                                                                                        precision_rounding=rounding) > 0:
                        extra_qty = ml.qty_done - ml.product_qty
                        ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id,
                                             package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)

                    quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,
                                                                   rounding_method='HALF-UP')
                    available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity,
                                                                              lot_id=ml.lot_id,
                                                                              package_id=ml.package_id,
                                                                              owner_id=ml.owner_id)
                    if available_qty < 0 and ml.lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False,
                                                                      package_id=ml.package_id, owner_id=ml.owner_id,
                                                                      strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                            Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty,
                                                             lot_id=False, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                            Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty,
                                                             lot_id=ml.lot_id, package_id=ml.package_id,
                                                             owner_id=ml.owner_id)
                    Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id,
                                                     package_id=ml.result_package_id, owner_id=ml.owner_id,
                                                     in_date=in_date)
                done_ml |= ml
            # Reset the reserved quantity as we just moved it to the destination location.
            (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
                'product_uom_qty': 0.00,
                'date': fields.Datetime.now(),
            })
        else:
            super(StockMoveLine, self)._action_done()