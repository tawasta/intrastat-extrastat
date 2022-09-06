
from odoo import fields, models


class IntrastatProductComputationLine(models.Model):

    _inherit = 'intrastat.product.computation.line'

    partner_vat = fields.Char(string="VAT", related="invoice_id.partner_id.vat")
