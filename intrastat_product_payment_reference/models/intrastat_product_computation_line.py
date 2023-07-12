from odoo import fields, models


class IntrastatProductComputationLine(models.Model):

    _inherit = "intrastat.product.computation.line"

    payment_reference = fields.Char(related="invoice_id.payment_reference")
