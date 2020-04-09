# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class RaportSale(models.TransientModel):
    _name = 'report.l10n_ro_account_report.report_sale'
    _description = 'Report Sale ANAF'


    @api.model    
    def _get_report_values(self,docids,  data=None ):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        invoices = self.env['account.move'].search([
             ('type', 'in',  ['out_invoice', 'out_refund', 'out_receipt'] ), # puchase ['in_invoice', 'in_refund',  'in_receipt']
             ('state','=','posted'),
             ('invoice_date','>=',date_from),('invoice_date','<=',date_to),
             ('company_id','=', company_id[0]),
        ],order='invoice_date, name')
        
        show_warnings = data['form']['show_warnings']
        report_lines = self.compute_report_lines(invoices,data,show_warnings)
        
        docargs = { 
            'print_datetime':fields.datetime.now(),
            'date_from':date_from,
            'date_to':date_to,
            'show_warnings':show_warnings,
            'user':self.env.user.name,
            'company':self.env['res.company'].browse(company_id[0]),
            'lines':report_lines,
        }
        return docargs
    
    
    def compute_report_lines(self,invoices,data,show_warnings):
        report_lines = []
        for inv1 in invoices:
            vals = {}
            vals['type'] = inv1.type
            vals['total_base'] = vals['base_neex'] = vals['base_exig'] = vals['base_ded1'] = vals[
                'base_ded2'] =  vals['base_19'] = vals['base_9'] = vals['base_5'] = vals['base_0'] = 0.00
            vals['total_vat'] = vals['tva_neex'] = vals['tva_exig'] =  vals['tva_20'] = vals['tva_19'] = vals[
                'tva_9'] = vals['tva_5'] = vals['tva_bun'] = vals['tva_serv'] = 0.00
            vals['base_col'] = vals['tva_col'] = 0.00
            vals['invers'] = vals['neimp'] = vals['others'] = vals['scutit1'] = vals['scutit2'] = 0.00
            vals['payments'] = []
            vals['number'] = inv1.name
            vals['date'] = inv1.invoice_date
            vals['partner'] = inv1.invoice_partner_display_name
            vals['vat'] = inv1.partner_stored_vat
            vals['total'] = inv1.amount_total_signed
            vals['show_warnings'] = ''

# I think that vat_on_payment must exist on invoice so, l10n_ro_vat_on_payment must be modified ( and to be put also on compnay - as related to partner?)
#             if inv1.vat_on_payment:
#                 total_base = total_vat = paid = 0.00
#                 base_neex = tva_neex = 0.00
#                 for payment in inv1.payment_ids:
#                     if payment.date <= date_to:
#                         paid += payment.credit or payment.debit
#                         for line in payment.move_id.line_id:
#                             if (inv1.number in line.name) and (line.account_id.type == 'other') and line.tax_code_id and ((inv1.type in ['out_invoice', 'out_refund'] and ((inv1.amount_total > 0 and line.tax_amount > 0) or (inv1.amount_total < 0 and line.tax_amount < 0))) or (inv1.type in ['in_invoice', 'in_refund'] and ((inv1.amount_total > 0 and line.tax_amount > 0) or (inv1.amount_total < 0 and line.tax_amount < 0)))):
#                                 if 'BAZA' in line.tax_code_id.name.upper():
#                                     base_neex += inv1.amount_tax != 0.00 and currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     tva_neex += inv1.amount_tax != 0.00 and currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, dp, context={'date': inv1.date_invoice}) or 0.00
# 
#                 if inv1.tax_line:
#                     for tax_line in inv1.tax_line:
#                         if ' 0' not in tax_line.name:
#                             total_base += currency_obj.compute(
#                                 self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice})
#                             total_vat += currency_obj.compute(
#                                 self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice})
#                         elif ' 0' in tax_line.name and inv1.date_invoice >= date_from and inv1.date_invoice <= date_to:
#                             vals['base_0'] += currency_obj.compute(
#                                 self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, context={'date': inv1.date_invoice})
#                 vals['base_neex'] = total_base - base_neex
#                 vals['tva_neex'] = total_vat - tva_neex
#                 if vals['tva_neex'] < 0.01 and vals['tva_neex'] > -0.01:
#                     vals['base_neex'] = vals['tva_neex'] = 0.00

            if not inv1.fiscal_position_id or (inv1.fiscal_position_id and ('National' in inv1.fiscal_position_id.name)):
                vals['total_base'] = inv1.amount_untaxed_signed
                vals['total_vat'] =  inv1.amount_tax_signed  # or we should add them  and just compare with this
                for line in inv1.invoice_line_ids: # or line_ids?
                    if len(line.tax_ids)>1:
                        vals['show_warnings'] += 'you have more taxes; '
                    if line.tax_exigible:    #original v8 not vat on payment
#     tax_exigible = fields.Boolean(string='Appears in VAT report', default=True, readonly=True,
#         help="Technical field used to mark a tax line as exigible in the vat report or not (only exigible journal items"
#              " are displayed). By default all new journal items are directly exigible, but with the feature cash_basis"
#              " on taxes, some will become exigible only when the payment is recorded.")
                        base_exig = tva_exig = 0
                        base_exig = line.price_subtotal  # is not taking into consideration currency ( must take from debit/credit)
                        tva_exig = line.price_total-base_exig  # here must search some function or value in line
                        if line.tax_ids:
                            tax_line_upper=line.tax_ids[0].name.upper()
                            if 'INVERS' in tax_line_upper:
                                vals['invers'] += 0# ???
                            elif ' 19' in tax_line_upper:
                                vals['base_19'] += base_exig 
                                vals['tva_19'] += tva_exig           
                            elif ' 9' in tax_line_upper:
                                vals['base_9'] += base_exig
                                vals['tva_9'] += tva_exig          
                            elif ' 5' in tax_line_upper:
                                vals['base_5'] += base_exig
                                vals['tva_5'] += tva_exig        
                            elif ' 0' in tax_line_upper:
                                vals['base_0'] += base_exig
                            else:
                                vals['show_warnings'] += f' you some unknown taxes={tax_line_upper}'
                            vals['base_exig'] += base_exig
                            vals['tva_exig'] += tva_exig
                        else:
                            vals['base_0'] = base_exig
                            vals['base_exig'] += base_exig

#             if inv1.fiscal_position:
#                 if inv1.tax_line:
#                     for tax_line in inv1.tax_line:
#                         if inv1.fiscal_position and ('Taxare Inversa' in inv1.fiscal_position.name):
#                             if inv1.partner_id.vat and 'RO' in inv1.partner_id.vat.upper():
#                                 if 'INVERS' in tax_line.name.upper():
#                                     vals['invers'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 24' in tax_line.name:
#                                     vals['base_24'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['tva_24'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 20' in tax_line.name:
#                                     vals['base_20'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['tva_20'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 19' in tax_line.name:
#                                     vals['base_19'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['tva_19'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 9' in tax_line.name:
#                                     vals['base_9'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['tva_9'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 5' in tax_line.name:
#                                     vals['base_5'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['tva_5'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if ' 0' in tax_line.name:
#                                     vals['base_0'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                 if (' 24' in tax_line.name) or (' 20' in tax_line.name) or (' 9' in tax_line.name) or (' 5' in tax_line.name):
#                                     vals['total_base'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                                     vals['total_vat'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.amount, dp, context={'date': inv1.date_invoice}) or 0.00
#                             else:
#                                 vals['scutit1'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Intra-Comunitar Bunuri' in inv1.fiscal_position.name):
#                             if 'INTRACOMUNITAR' in tax_line.name:
#                                 vals['base_ded1'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Intra-Comunitar Servicii' in inv1.fiscal_position.name):
#                             if 'INTRACOMUNITAR' in tax_line.name:
#                                 vals['base_ded1'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Scutite' in inv1.fiscal_position.name):
#                             if 'SCUTIT' in tax_line.name.upper():
#                                 vals['scutit2'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Neimpozabile' in inv1.fiscal_position.name):
#                             if 'INVERS' in tax_line.name.upper():
#                                 vals['neimp'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, dp, context={'date': inv1.date_invoice}) or 0.00
#                 elif inv1.fiscal_position and ('Extra-Comunitar' in inv1.fiscal_position.name):
#                     vals['others'] = currency_obj.compute(
#                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, inv1.amount_untaxed, dp, context={'date': inv1.date_invoice})
#                         
#             if inv1.vat_on_payment:
#                 vals['total_base'] = vals['total_vat'] = 0.00
#                 if inv1.payment_ids:
#                     for payment in inv1.payment_ids:
#                         if payment.date >= date_from and payment.date <= date_to:
#                             pay = {}
#                             pay['base_exig'] = pay['tva_exig'] = 0.00
#                             pay['base_24'] = pay['base_20'] = pay['base_19'] = pay['base_9'] = pay['base_5'] = 0.00
#                             pay['tva_24'] = pay['tva_20'] = pay['tva_19'] = pay['tva_9'] = pay['tva_5'] = 0.00
#                             pay['number'] = str(payment.move_id.name)
#                             pay['date'] = payment.move_id.date
#                             pay['amount'] = currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, payment.credit or payment.debit, dp, context={
#                                                                  'date': inv1.date_invoice}) or currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, payment.debit, dp, context={'date': inv1.date_invoice})
#                             for line in payment.move_id.line_id:
#                                 if (inv1.type in ['out_invoice', 'out_refund'] and '4427' in line.account_id.code) or (inv1.type in ['in_invoice', 'in_refund'] and '4426' in line.account_id.code):
#                                     if line.tax_code_id and ' 24' in line.tax_code_id.name:
#                                         pay['base_24'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, round(
#                                             (line.credit or line.debit) / 0.24), dp, context={'date': inv1.date_invoice}) or 0.00
#                                         pay['tva_24'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, (
#                                             line.credit or line.debit), dp, context={'date': inv1.date_invoice}) or 0.00
#                                     if line.tax_code_id and ' 20' in line.tax_code_id.name:
#                                         pay['base_20'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, round(
#                                             (line.credit or line.debit) / 0.20), dp, context={'date': inv1.date_invoice}) or 0.00
#                                         pay['tva_20'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, (
#                                             line.credit or line.debit), dp, context={'date': inv1.date_invoice}) or 0.00
#                                     if line.tax_code_id and ' 19' in line.tax_code_id.name:
#                                         pay['base_19'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, round(
#                                             (line.credit or line.debit) / 0.19), dp, context={'date': inv1.date_invoice}) or 0.00
#                                         pay['tva_19'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, (
#                                             line.credit or line.debit), dp, context={'date': inv1.date_invoice}) or 0.00
#                                     if line.tax_code_id and ' 9' in line.tax_code_id.name:
#                                         pay['base_9'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, round(
#                                             (line.credit or line.debit) / 0.09), dp, context={'date': inv1.date_invoice}) or 0.00
#                                         pay['tva_9'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, (
#                                             line.credit or line.debit), dp, context={'date': inv1.date_invoice}) or 0.00
#                                     if line.tax_code_id and ' 5' in line.tax_code_id.name:
#                                         pay['base_5'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, round(
#                                             (line.credit or line.debit) / 0.05), dp, context={'date': inv1.date_invoice}) or 0.00
#                                         pay['tva_5'] += currency_obj.compute(self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, (
#                                             line.credit or line.debit), dp, context={'date': inv1.date_invoice}) or 0.00
# 
#                             pay['base_exig'] += pay['base_24'] + pay['base_20'] + pay['base_19'] +\
#                                 pay['base_9'] + pay['base_5']
#                             pay['tva_exig'] += pay['tva_24'] + pay['tva_20'] + pay['tva_19'] +\
#                                 pay['tva_9'] + pay['tva_5']
#                             vals['payments'].append(pay)
#                             vals['total_base'] += pay['base_exig']
#                             vals['total_vat'] += pay['tva_exig']
#                             vals['base_24'] += pay['base_24']
#                             vals['tva_24'] += pay['tva_24']
#                             vals['base_20'] += pay['base_20']
#                             vals['tva_20'] += pay['tva_20']
#                             vals['base_19'] += pay['base_19']
#                             vals['tva_19'] += pay['tva_19']
#                             vals['base_9'] += pay['base_9']
#                             vals['tva_9'] += pay['tva_9']
#                             vals['base_5'] += pay['base_5']
#                             vals['tva_5'] += pay['tva_5']
#                             vals['payments'].sort(
#                                 key=itemgetter("date", "number"))

            if vals != {}:
                report_lines.append(vals)
#             # Adding undeductible vat and inverse taxation colected VAT
#             # amount from purchase
#                         
#             if inv1.type in ['in_invoice', 'in_refund'] and inv1.period_id.id == period_id and inv1.date_invoice >= date_from and inv1.date_invoice <= date_to:
#                 not_deductible = False
#                 for inv_line in inv1.invoice_line:
#                     if inv_line.not_deductible:
#                         not_deductible = True
#                 if not_deductible:
#                     vals1 = {}
#                     vals1['type'] = 'out_invoice'
#                     vals1['total_base'] = vals1['base_neex'] = vals1['base_exig'] = vals1['base_ded1'] = vals1[
#                         'base_ded2'] = vals1['base_24'] = vals1['base_20'] = vals1['base_19'] = vals1['base_9'] = vals1['base_5'] = vals1['base_0'] = 0.00
#                     vals1['total_vat'] = vals1['tva_neex'] = vals1['tva_24'] = vals1['tva_20'] = vals1['tva_19'] = vals1['tva_9'] = vals1[
#                         'tva_5'] = vals1['tva_exig'] = vals1['tva_bun'] = vals1['tva_serv'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     vals1['invers'] = vals1['neimp'] = vals1[
#                         'others'] = vals1['scutit1'] = vals1['scutit2'] = 0.00
#                     vals1['payments'] = []
#                     vals1['vat_on_payment'] = '0'
#                     pay = {}
#                     pay['amount'] = pay['base_exig'] = pay[
#                         'tva_exig'] = 0.00
#                     pay['base_24'] = pay['base_20'] = pay['base_19'] = pay['base_9'] = pay['base_5'] = 0.00
#                     pay['tva_24'] = pay['tva_20'] = pay['tva_19'] = pay['tva_9'] = pay['tva_5'] = 0.00
#                     pay['number'] = ''
#                     pay['date'] = ''
#                     vals1['payments'].append(pay)
#                     vals1[
#                         'number'] = inv1.supplier_invoice_number or inv1.origin
#                     vals1['date'] = inv1.date_invoice
#                     vals1['partner'] = inv1.partner_id.name
#                     vals1['vat'] = ''
#                     if inv1.partner_id.vat:
#                         if inv1.partner_id.vat_subjected:
#                             vals1['vat'] = inv1.partner_id.vat
#                         else:
#                             vals1['vat'] = inv1.partner_id.vat[2:]
#                     vals1['total'] = 0.00
#                     vals1['total_base'] = 0.00
#                     vals1['total_vat'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     for line in inv1.move_id.line_id:
#                         if line.tax_code_id and 'COLECTATA' in line.tax_code_id.code.upper():
#                             if 'BAZA' in line.tax_code_id.code.upper():
#                                 vals1['total_base'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             else:
#                                 vals1['total_vat'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             if ' 24' in line.tax_code_id.code:
#                                 if 'BAZA' in line.tax_code_id.code.upper():
#                                     vals1['base_24'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     vals1['tva_24'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             if ' 20' in line.tax_code_id.code:
#                                 if 'BAZA' in line.tax_code_id.code.upper():
#                                     vals1['base_20'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     vals1['tva_20'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             if ' 19' in line.tax_code_id.code:
#                                 if 'BAZA' in line.tax_code_id.code.upper():
#                                     vals1['base_19'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     vals1['tva_19'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             if ' 9' in line.tax_code_id.code:
#                                 if 'BAZA' in line.tax_code_id.code.upper():
#                                     vals1['base_9'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     vals1['tva_9'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                             if ' 5' in line.tax_code_id.code:
#                                 if 'BAZA' in line.tax_code_id.code.upper():
#                                     vals1['base_5'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
#                                 else:
#                                     vals1['tva_5'] += currency_obj.compute(
#                                         self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, line.tax_amount, context={'date': inv1.date_invoice}) or 0.00
# 
#                     vals1['total'] = vals1[
#                         'total_base'] + vals1['total_vat']
#                     inv.append(vals1)
#                 if inv1.fiscal_position and (('Taxare Inversa' in inv1.fiscal_position.name) or ('Intra-Comunitar' in inv1.fiscal_position.name)):
#                     vals1 = {}
#                     vals1['type'] = 'out_invoice'
#                     vals1['total_base'] = vals1['base_neex'] = vals1['base_exig'] = vals1['base_ded1'] = vals1[
#                         'base_ded2'] = vals1['base_24'] = vals1['base_20'] = vals1['base_19'] = vals1['base_9'] = vals1['base_5'] = vals1['base_0'] = 0.00
#                     vals1['total_vat'] = vals1['tva_neex'] = vals1['tva_24'] = vals1['tva_20'] = vals1['tva_19'] = vals1['tva_9'] = vals1[
#                         'tva_5'] = vals1['tva_exig'] = vals1['tva_bun'] = vals1['tva_serv'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     vals1['invers'] = vals1['neimp'] = vals1[
#                         'others'] = vals1['scutit1'] = vals1['scutit2'] = 0.00
#                     vals1['payments'] = []
#                     vals1['vat_on_payment'] = '0'
#                     pay = {}
#                     pay['amount'] = pay['base_exig'] = pay[
#                         'tva_exig'] = 0.00
#                     pay['base_24'] = pay['base_20'] = pay['base_19'] = pay['base_9'] = pay['base_5'] = 0.00
#                     pay['tva_24'] = pay['tva_20'] = pay['tva_19'] = pay['tva_9'] = pay['tva_5'] = 0.00
#                     pay['number'] = ''
#                     pay['date'] = ''
#                     vals1['payments'].append(pay)
#                     vals1[
#                         'number'] = inv1.supplier_invoice_number or inv1.origin
#                     vals1['date'] = inv1.date_invoice
#                     vals1['partner'] = inv1.partner_id.name
#                     vals1['vat'] = ''
#                     if inv1.partner_id.vat:
#                         if inv1.partner_id.vat_subjected:
#                             vals1['vat'] = inv1.partner_id.vat
#                         else:
#                             vals1['vat'] = inv1.partner_id.vat[2:]
#                     vals1['total'] = 0.00
#                     vals1['total_base'] = 0.00
#                     vals1['total_vat'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     for tax_line in inv1.tax_line:
#                         if inv1.fiscal_position and ('Taxare Inversa' in inv1.fiscal_position.name):
#                             if 'ach-c' in tax_line.name:
#                                 vals1['base_col'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, context={'date': inv1.date_invoice}) or 0.00
#                                 vals1['tva_col'] += (-1) * currency_obj.compute(self.cr, self.uid, inv1.currency_id.id,
#                                                                                 company.currency_id.id, tax_line.amount, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Intra-Comunitar Bunuri' in inv1.fiscal_position.name):
#                             if 'ach_c' in tax_line.name:
#                                 vals1['base_col'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, context={'date': inv1.date_invoice}) or 0.00
#                                 vals1['tva_col'] += (-1) * currency_obj.compute(self.cr, self.uid, inv1.currency_id.id,
#                                                                                 company.currency_id.id, tax_line.amount, context={'date': inv1.date_invoice}) or 0.00
#                         if inv1.fiscal_position and ('Intra-Comunitar Servicii' in inv1.fiscal_position.name):
#                             if 'ach_c' in tax_line.name:
#                                 vals1['base_col'] += currency_obj.compute(
#                                     self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, context={'date': inv1.date_invoice}) or 0.00
#                                 vals1['tva_col'] += (-1) * currency_obj.compute(self.cr, self.uid, inv1.currency_id.id,
#                                                                                 company.currency_id.id, tax_line.amount, context={'date': inv1.date_invoice}) or 0.00
#                     vals1['total'] = vals1['base_col']
#                     inv.append(vals1)
#                 elif not inv1.fiscal_position and not inv1.vat_on_payment and 'RO' in inv1.partner_id.vat.upper(): 
#                     vals1 = {}
#                     vals1['type'] = 'out_invoice'
#                     vals1['total_base'] = vals1['base_neex'] = vals1['base_exig'] = vals1['base_ded1'] = vals1[
#                         'base_ded2'] = vals1['base_24'] = vals1['base_20'] = vals1['base_19'] = vals1['base_9'] = vals1['base_5'] = vals1['base_0'] = 0.00
#                     vals1['total_vat'] = vals1['tva_neex'] = vals1['tva_24'] = vals1['tva_20'] = vals1['tva_19'] = vals1['tva_9'] = vals1[
#                         'tva_5'] = vals1['tva_exig'] = vals1['tva_bun'] = vals1['tva_serv'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     vals1['invers'] = vals1['neimp'] = vals1[
#                         'others'] = vals1['scutit1'] = vals1['scutit2'] = 0.00
#                     vals1['payments'] = []
#                     vals1['vat_on_payment'] = '0'
#                     pay = {}
#                     pay['amount'] = pay['base_exig'] = pay[
#                         'tva_exig'] = 0.00
#                     pay['base_24'] = pay['base_20'] = pay['base_19'] = pay['base_9'] = pay['base_5'] = 0.00
#                     pay['tva_24'] = pay['tva_20'] = pay['tva_19'] = pay['tva_9'] = pay['tva_5'] = 0.00
#                     pay['number'] = ''
#                     pay['date'] = ''
#                     vals1['payments'].append(pay)
#                     vals1[
#                         'number'] = inv1.supplier_invoice_number or inv1.origin
#                     vals1['date'] = inv1.date_invoice
#                     vals1['partner'] = inv1.partner_id.name
#                     vals1['vat'] = ''
#                     if inv1.partner_id.vat:
#                         if inv1.partner_id.vat_subjected:
#                             vals1['vat'] = inv1.partner_id.vat
#                         else:
#                             vals1['vat'] = inv1.partner_id.vat[2:]
#                     vals1['total'] = 0.00
#                     vals1['total_base'] = 0.00
#                     vals1['total_vat'] = 0.00
#                     vals1['base_col'] = vals1['tva_col'] = 0.00
#                     for tax_line in inv1.tax_line:
#                         if 'Ti-ach-c' in tax_line.name:
#                             vals1['base_col'] += currency_obj.compute(
#                                 self.cr, self.uid, inv1.currency_id.id, company.currency_id.id, tax_line.base, context={'date': inv1.date_invoice}) or 0.00
#                             vals1['tva_col'] += (-1) * currency_obj.compute(self.cr, self.uid, inv1.currency_id.id,
#                                                                             company.currency_id.id, tax_line.amount, context={'date': inv1.date_invoice}) or 0.00
#                     vals1['total'] = vals1['base_col'] 
#                     if vals1['base_col'] != 0.00:
#                         inv.append(vals1)                              
        return report_lines