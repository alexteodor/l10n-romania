# Copyright 2015 Deltatech
# Copyright 2018 OdooERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Romania - Invoice Report",
    "summary": "Romania - Invoice Report",
    "version": "13.0.1.0.0",
    "category": "Localization",
    "author": "Deltatech," "OdooERP Romania," "Odoo Community Association (OCA)",
    "website": "https://odoo-community.org",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["base", "account", "l10n_ro", "l10n_ro_partner_create_by_vat"],
    "data": [
        "views/report_templates.xml",
        "views/account_invoice_view.xml",
        "views/res_bank_view.xml",
        "views/invoice_report.xml",
        "views/res_config_settings_view.xml",
    ],
}
