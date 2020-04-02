# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class SalePurchaseJournalReport(models.TransientModel):
    _name = 'sp.report'
    _description = 'Sale Purchase Journal Report'

    company_id= fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    journal = fields.Selection( selection=[('purchase', 'Purchase =In invoices'), ('sale', 'Sale = Out invoices')],string='Journal type', default='sale',required=True)
    date_from = fields.Date("Start Date", required=True, default=(fields.Date.today()-relativedelta(months=1)).replace(day=1))
    date_to = fields.Date("End Date", required=True, default=fields.Date.today().replace(day=1)-timedelta(days=1) )     
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for fy in self:
            # Starting date must be prior to the ending date
            date_from = fy.date_from
            date_to = fy.date_to
            if date_to < date_from:
                raise ValidationError(_('The ending date must not be prior to the starting date.'))

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'sp.report',
            'form': data
        }
        if self.journal=='sale':
            report_action= 'l10n_ro_account_report.action_report_sale'
        else:
            report_action= 'l10n_ro_account_report.action_report_purchase'
        ref=  self.env.ref(report_action)
        res =ref.report_action(docids=[], data=datas,config=False)
        return res

