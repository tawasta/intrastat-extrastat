from odoo import fields, models


class IntrastatProductComputationLine(models.Model):
    _inherit = "intrastat.product.computation.line"

    partner_vat = fields.Char(string="VAT", compute="_compute_partner_vat")

    def _compute_partner_vat(self):
        for record in self:
            record.partner_vat = (
                # VAT on the declaration line
                record.vat
                or
                # VAT from invoice shipping address
                record.invoice_id.partner_shipping_id.vat
                or
                # Fallback for invoice customer
                record.invoice_id.partner_id.vat
            )
