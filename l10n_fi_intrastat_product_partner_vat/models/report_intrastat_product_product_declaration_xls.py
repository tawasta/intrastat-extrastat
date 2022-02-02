
from odoo import models


class IntrastatProductDeclarationXlsx(models.AbstractModel):

    _inherit = 'report.intrastat_product.product_declaration_xls'

    def _get_template(self, declaration):
        template = super(IntrastatProductDeclarationXlsx, self)._get_template(declaration)

        template["partner_vat"] = {
            'header': {
                'type': 'string',
                'value': self._('VAT'),
            },
            'line': {
                'type': 'string',
                'value': self._render(
                    "line.partner_vat or ''"),
            },
            'width': 16,
        }

        return template
