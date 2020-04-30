from odoo import _, api, models
from odoo.exceptions import UserError


class IntrastatProductDeclaration(models.Model):
    _inherit = "intrastat.product.declaration"

    @api.multi
    def generate_csv_finnish(self):
        """
        Generate Finnish Intrastat Declaration CSV file
        """

        self.ensure_one()
        self.message_post(body=_("Generate CSV Declaration File"))

        # Check if company has VAT number set
        self._check_generate_xml()

        # Delete current attachments to avoid confusion
        self._unlink_attachments()

        csv_string = self._generate_csv()

        if csv_string:
            attach_id = self._attach_csv_file(
                csv_string, "{}_{}".format(self.type, self.revision)
            )
            return self._open_attach_view(attach_id)
        else:
            raise UserError(_("No CSV File has been generated."))

    def _generate_csv(self):
        csv_string = self._generate_csv_headers()

        if self.declaration_line_ids:
            # Add information provider information to first row
            csv_string += self._generate_csv_line(self.declaration_line_ids[0], True)

        # Loop through rest of the rows
        for line in self.declaration_line_ids[1:]:
            csv_string += self._generate_csv_line(line)

        return csv_string

    def _generate_csv_headers(self):
        headers = [
            _("Information provider"),
            _("Period"),
            _("Direction"),
            _("Delegate"),
            _("CN8"),
            _("Transaction"),
            _("Member country"),
            _("Country of origin"),
            _("Mode of transport"),
            _("Net weight"),
            _("Additional units"),
            _("Invoice amount"),
            _("Statistical amount"),
            _("Reference"),
        ]

        return self._list_to_csv_line(headers)

    def _generate_csv_line(self, declaration_line, first=False):
        line = list()

        # Report type is 1 for arrival, 2 for dispatch
        report_type = 1 if self.type == "arrivals" else 2

        if first:
            # The first line has information provider info

            # VAT
            line.append(self.company_id.vat)
            # Period
            line.append(self.year_month.replace("-", ""))
            # Direction
            line.append(report_type)
            # Delegate
            line.append("")
        else:
            # Other lines have four empty columns
            line += ["", "", "", ""]

        # CN8
        line.append(declaration_line.hs_code_id.local_code)

        # Transaction code. We leave this empty as we can't realiably decide
        # the code. Most likely it is 11, but it is safer to add this manually
        line.append("")

        # Member country
        line.append(declaration_line.src_dest_country_id.code)

        # Origin country (Country of Origin)
        coo = ""
        if report_type == 1:
            coo = declaration_line.src_dest_country_id.code

        line.append(coo)

        # Mode of transport
        transport_mode = ""
        if declaration_line.transport_id:
            transport_mode = declaration_line.transport_id.code
        line.append(transport_mode)

        # Net weight
        line.append(declaration_line.weight)

        # Quantity
        qty = ""
        if declaration_line.suppl_unit_qty >= 1:
            # Add quantity if it is at least 1
            qty = declaration_line.suppl_unit_qty
        line.append(qty)

        # Invoice amount
        line.append(declaration_line.amount_company_currency)

        # Statistical amount
        line.append("")

        # Ref (not in use yet in Finnish report)
        line.append("")

        return self._list_to_csv_line(line)

    def _list_to_csv_line(self, input_list, delimiter=";"):
        return delimiter.join(str(x) for x in input_list) + "\n"

    @api.multi
    def _attach_csv_file(self, csv_string, declaration_name):
        # Attach the CSV file to the report_intrastat_product/service object
        self.ensure_one()
        import base64

        filename = "{}_{}.csv".format(self.year_month, declaration_name)
        attach = self.env["ir.attachment"].create(
            {
                "name": filename,
                "res_id": self.id,
                "res_model": self._name,
                "datas": base64.b64encode(csv_string.encode('ascii')),
                "datas_fname": filename,
            }
        )
        return attach.id

    def _prepare_invoice_domain(self):
        domain = super(IntrastatProductDeclaration, self)._prepare_invoice_domain()

        if self.type == "arrivals":
            # Import
            domain.append(("type", "in", ["in_invoice"]))
        else:
            # Export
            domain.append(("type", "in", ["out_invoice"]))

        return domain
