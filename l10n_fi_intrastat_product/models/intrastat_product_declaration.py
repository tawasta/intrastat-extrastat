from odoo import _, api, models
from odoo.exceptions import UserError


class IntrastatProductDeclaration(models.Model):
    _inherit = "intrastat.product.declaration"

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
            attachment_id = self._attach_csv_file(
                csv_string, "{}_{}".format(self.declaration_type, self.revision)
            )
            return self._download_attachment(attachment_id)
        else:
            raise UserError(_("No CSV File has been generated."))

    def _download_attachment(self, attachment):
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        )
        url = "{}/web/content/{}?download=true".format(
            base_url,
            str(attachment.id),
        )
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "current",
        }

    @api.model
    def _open_attach_view(self, attachment, title="XML file"):
        """
        Returns an action which opens the form view of the
        corresponding attachment
        """
        action = {
            "name": title,
            "view_mode": "form",
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "current",
            "res_id": attachment.id,
        }
        return action

    def _generate_csv(self):
        csv_string = self._generate_csv_headers()
        first = True
        europe = self.env.ref("base.europe").country_ids

        for declaration_line in self.declaration_line_ids:

            # Check does a Member country belong to EU
            if (
                declaration_line.src_dest_country_id.id not in europe.ids
                or declaration_line.src_dest_country_id.code == "GB"
            ):
                continue

            grouped_by_vat = {}

            # Loop through transactions and fetch amount, quantity and
            # weight information and group them by VAT
            for computation_line in declaration_line.computation_line_ids:

                vat = computation_line.partner_vat
                amount = computation_line.amount_company_currency
                suppl_unit_qty = computation_line.suppl_unit_qty
                weight = computation_line.weight

                # If VAT is not found, set null values
                if not grouped_by_vat.get(vat):
                    grouped_by_vat[vat] = [0, 0, 0]
                grouped_by_vat[vat][0] += amount
                grouped_by_vat[vat][1] += suppl_unit_qty
                grouped_by_vat[vat][2] += weight

            for vat, amount_line in grouped_by_vat.items():
                amount = amount_line[0]
                suppl_unit_qty = amount_line[1]
                weight = amount_line[2]

                # Add information provider information to first row
                # if 'first' is set to True
                csv_string += self._generate_csv_line(
                    vat, amount, suppl_unit_qty, weight, declaration_line, first
                )
                first = False

        return csv_string

    def _generate_csv_headers(self):
        headers = [
            _("Information provider"),
            _("Period"),
            _("Direction"),
            _("VAT"),
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

    def _generate_csv_line(
        self, vat, amount, suppl_unit_qty, weight, declaration_line, first=False
    ):
        line = list()

        # Report type is 1 for arrival, 2 for dispatch
        report_type = 1 if self.declaration_type == "arrivals" else 2

        if first:
            # The first line has information provider info

            # Company's VAT (Information provider)
            line.append(self.company_id.vat)
            # Period
            line.append(self.year_month.replace("-", ""))
            # Direction
            line.append(report_type)
        else:
            # Other lines have three empty columns
            line += ["", "", ""]

        # VAT
        line.append(vat)

        # CN8
        line.append(declaration_line.hs_code_id.local_code)

        # Transaction code (Transaction)
        transaction_code = ""
        if declaration_line.transaction_id:
            transaction_code = declaration_line.transaction_id.code
        line.append(transaction_code)

        # Member country
        line.append(declaration_line.src_dest_country_id.code)

        # Origin country (Country of Origin)
        coo = declaration_line.product_origin_country_id.code

        line.append(coo)

        # Mode of transport
        transport_mode = ""
        if declaration_line.transport_id:
            transport_mode = declaration_line.transport_id.code
        line.append(transport_mode)

        # Net weight
        line.append(str(weight).replace(".", ","))

        # Quantity (Additional units)
        line.append(str(suppl_unit_qty).replace(".", ","))

        # Invoice amount
        if amount < 0:
            # Minimum amount is 1
            amount = 1
        # Round the amount to an integer
        amount = round(amount, 0)
        line.append(str(amount).replace(".", ","))

        # Statistical amount
        line.append("")

        # Ref (not yet used in Finnish Intrastat-report)
        line.append("")

        return self._list_to_csv_line(line)

    def _list_to_csv_line(self, input_list, delimiter=";"):
        return delimiter.join(str(x) for x in input_list) + "\n"

    def _attach_csv_file(self, csv_string, declaration_name):
        # Attach the CSV file to the report_intrastat_product/service object
        self.ensure_one()
        import base64

        filename = "{}_{}.csv".format(self.year_month, declaration_name)
        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "res_id": self.id,
                "res_model": self._name,
                "datas": base64.b64encode(csv_string.encode("ascii")),
            }
        )
        return attachment

    def _prepare_invoice_domain(self):
        domain = super(IntrastatProductDeclaration, self)._prepare_invoice_domain()

        domain.remove(
            (
                "move_type",
                "in",
                ("out_invoice", "out_refund", "in_invoice", "in_refund"),
            )
        )

        if self.declaration_type == "arrivals":
            # Import
            domain.append(("move_type", "in", ["in_invoice"]))
        else:
            # Export
            domain.append(("move_type", "in", ["out_invoice"]))

        return domain
