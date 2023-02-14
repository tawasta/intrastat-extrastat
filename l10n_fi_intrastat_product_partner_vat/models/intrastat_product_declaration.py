from odoo import api, models


class IntrastatProductDeclaration(models.Model):

    _inherit = "intrastat.product.declaration"

    @api.model
    def _xls_computation_line_fields(self):
        res = super(IntrastatProductDeclaration, self)._xls_computation_line_fields()
        res.append("partner_vat")
        return res
