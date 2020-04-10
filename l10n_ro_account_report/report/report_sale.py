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
        report_lines,totals = self.compute_report_lines(invoices,data,show_warnings)
        
        docargs = { 
            'print_datetime':fields.datetime.now(),
            'date_from':date_from,
            'date_to':date_to,
            'show_warnings':show_warnings,
            'user':self.env.user.name,
            'company':self.env['res.company'].browse(company_id[0]),
            'lines':report_lines,
            'totals':totals,

        }
        return docargs
    
#     def search_what_base_in_tag_ids(self,base_tax,tag_ids):
#         "input tag_ids and returns a key_name for base_value and eventualy warning"
#         if len(tag_ids)>1:
#             return ('',f'you have more tag_ids={tag_ids}')
#         if base_tax==
    
#     def find_all_account_tax_report_line(self):
#         "return a list with names of all account_tax_report_line"
#         Account_tax_report_line = self.env['account.tax.report.line']
#         account_tax_report_lines = Account_tax_report_line.search([('country_id','=',self.env.ref('base.ro').id)]).read(['name','parent_id'])
# 
#         agregate_account_tax_report_line_names = [x['name'] for x in account_tax_report_lines if  not x['parent_id']]
#         account_tax_report_line_names = [(x['name'],x['parent_id']) for x in account_tax_report_lines if  x['parent_id']]
#         return agregate_account_tax_report_line_names,account_tax_report_line_names
    
    def compute_report_lines(self,invoices,data,show_warnings):
        # find all the keys for dictionary
 #       agregate_account_tax_report_line_names, account_tax_report_line_names = self.find_all_account_tax_report_line()
        posible_tags = self.env['account.account.tag'].search([('country_id','=',self.env.ref('base.ro').id)]).read(['name'])
        
        report_lines = []
        # totals will have the sum of all the values
#         totals = {}
#         totals['total_base'] = totals['base_neex'] = totals['base_exig'] = totals['base_ded1'] = totals[
#             'base_ded2'] =  totals['base_19'] = totals['base_9'] = totals['base_5'] = totals['base_0'] = 0.00
#         totals['total_vat'] = totals['tva_neex'] = totals['tva_exig'] =  totals['tva_20'] = totals['tva_19'] = totals[
#             'tva_9'] = totals['tva_5'] = totals['tva_bun'] = totals['tva_serv'] = 0.00
#         totals['base_col'] = totals['tva_col'] = 0.00
#         totals['invers'] = totals['neimp'] = totals['others'] = totals['scutit1'] = totals['scutit2'] = 0.00
#         totals['total'] =totals['amount'] = 0.0

        for inv1 in invoices:
#             agreg_vals = dict.fromkeys(agregate_account_tax_report_line_names, {'parent_id':False,'value':0} )
#             vals = {x[0]:{'parent_id':x[1][1],'value':0} for x in account_tax_report_line_names} 
            vals = {x['name']:0 for x in posible_tags}
            vals_keys = vals.keys()
            vals['number'] = inv1.name
            vals['date'] = inv1.invoice_date
            vals['partner'] = inv1.invoice_partner_display_name
            vals['vat'] = inv1.partner_stored_vat
            vals['total'] = inv1.amount_total_signed
            vals['show_warnings'] = ''
            for line in inv1.line_ids:
                if line.account_internal_type not in ['receivable','payable']:
                    if not line.tag_ids or len(line.tag_ids)>1: # or if no tva put tva 0 in future
                        vals['show_warnings']+=f"line id={line.id} name={line.name}  does not have line_tag_ids or have more and I'm not going to guess it ( maybe in future); "
                    elif line.tag_ids[0].name not in vals_keys:
                        vals['show_warnings']+=f"this tag_ids={line.tag_ids[0].name} is not in  find_all_account_tax_report_line"
                    else:
                        vals[line.tag_ids[0].name] += line.credit-line.debit
# put the agregated values
#             for key,value in vals:
#                 if type(value) is dict:
#                     if value['parent_id']:
#                         agreg_vals[value['parent_id']]['value'] += value['value']
#         
#             report_lines += [agreg_values.update(vals)] 

            report_lines += [vals]

#            for line in inv1.line_ids: # line_ids is including invoice_line_ids but has also the taxes
#                 if line.account_internal_type=='other' and line.exclude_from_invoice_tab: # is the base without taxes
#                     vals['total_base'] += line.credit - line.debit # is in ron ( if it was in another currency is already converted )
#                     if not line.tag_ids:
#                         vals['show_warnings']+=f"line id={line.id} name={line.name}  is a baze, but does not have line_tag_ids and I'm not going to guess it ( maybe in future); "
#                     else:
#                         what_base,warning = search_what_base_in_tag_ids('base',line.tag_ids)
#                         if not what_base[0]:
#                             vals['show_warnings']+=what_base[1]+'; '
#                         else:
#                             vals[what_base[0]] += line.credit - line.debit
#                 elif line.account_internal_type=='receivable': # is the invoice total 
#                     if line.tax_line_id:
#                         vals['show_warnings']+= f"line id={line.id} name={line.name}  has a tax but is a receivable; "
#                     else:
#                         if vals['total'] != line.debit-line.credit:
#                             vals['show_warnings'] += f"line id={line.id} name={line.name} has value {line.debit-line.credit} != invoice_value {vals['total']}; "
#                 elif line.account_internal_type=='other':  # must be taxes
#                     if not line.tax_line_id:
#                         vals['show_warnings']+=f"line id={line.id} name={line.name}  must be a tax, but does not have tax_line_id; "
#                     else:
#                         if not line.tag_ids:
#                             vals['show_warnings']+=f"line id={line.id} name={line.name}  is a tax, but does not have line_tag_ids and I'm not going to guess it ( maybe in future); "
#                         else:
#                             what_tax,warning = search_what_base_in_tag_ids('tax',line.tag_ids)
#                             if not what_tax[0]:
#                                 vals['show_warnings']+=what_tax[1]+'; '
#                             else:
#                                 vals[what_base[0]] += 0 - line.credit + line.debit
#                             
#             inv.append(vals1)                              
#             totals['total_base'] += vals['total_base'] 
#             totals['base_neex'] += vals['base_neex']
#             totals['base_exig'] += vals['base_exig']
#             totals['base_ded1']+= vals['base_ded1']
#             totals['base_ded2']+= vals['base_ded2']
#             totals['base_19']+= vals['base_19']
#             totals['base_9']+= vals['base_9']
#             totals['base_5']+= vals['base_5']
#             totals['base_0']  += vals['base_0']
#                 
#             totals['total_vat']+= vals['total_vat']
#             totals['tva_neex']+= vals['tva_neex']
#             totals['tva_exig']+= vals['tva_exig']
#             totals['tva_20']+= vals['tva_20']
#             totals['tva_19']+= vals['tva_19']
#             totals['tva_9'] += vals['tva_9']
#             totals['tva_5']+= vals['tva_5']
#             totals['tva_bun']+= vals['tva_bun']
#             totals['tva_serv']+= vals['tva_serv']
#             totals['base_col']+= vals['base_col']
#             totals['tva_col']+= vals['base_col']
#             
#             totals['invers']= vals['invers']
#             totals['neimp']= vals['neimp']
#             totals['others']= vals['others']
#             totals['scutit1']= vals['scutit1']
#             totals['scutit2']= vals['scutit2']
#             totals['total']= vals['total']


        return report_lines,totals