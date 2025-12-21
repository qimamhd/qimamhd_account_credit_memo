# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
 
class partner_summary_xlsx(models.TransientModel):
    _inherit = 'partner.summary.report'
   
    hide_fully_credit_note = fields.Boolean(string="اخفاء المترجعات المكتملة")

    
    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        report_setup = {}
        

        for x in self.setup_lines_id:
            report_setup[x.attr_code] = x.att_value

       

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'partner_id': self.partner_id.id,
                'account_code': [(i['code']) for i in self.account_id],
                'analytic_account_ids1': [(i['id']) for i in self.analytic_account_ids1],
                'check_analytic_setting': self.check_analytic_setting,
                'enable_custom_seq': self.enable_custom_seq,
                'hide_zero_balance': self.hide_zero_balance,
                'only_customers': self.only_customers,
                'only_suppliers': self.only_suppliers,
                'filter_customers': self.filter_customers,
                'filter_suppliers': self.filter_suppliers,
                'sales_man_id': [(i['id']) for i in self.sales_man_id],
                'move_total_without_op': self.move_total_without_op,

                'company_ids1': [(i['id']) for i in self.company_ids1],
                'branch_id': [(i['id']) for i in self.branch_id],
                'currency_id': [(i['id']) for i in self.currency_id],
                'sort_type': self.sort_type,
                'report_type': self.report_type,
                'display_type': self.display_type,
                'summary_options': self.summary_options,

                'doc_state': self.doc_state,
                'report_setup': report_setup,
                'show_payments_before_posted': self.show_payments_before_posted,
                'branches_selected': self.branches_selected,
                'partner_branch_id': [(i['id']) for i in self.partner_branch_id],
                'hide_fully_credit_note': self.hide_fully_credit_note,
            },
        }

     
        return self.env.ref('qimmamhd_system.partner_statement_report').report_action(self, data=data)


class ReportAttendanceRecap(models.AbstractModel):
    _inherit = 'report.qimmamhd_system.partner_statement_report_view'
  

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        l_partner_id = data['form']['partner_id']
        l_account_code = data['form']['account_code']
        l_analytic_account_ids1 = data['form']['analytic_account_ids1']
        l_check_analytic_setting = data['form']['check_analytic_setting']
        l_enable_custom_seq = data['form']['enable_custom_seq']
        l_hide_zero_balance = data['form']['hide_zero_balance']
        l_only_customers = data['form']['only_customers']
        l_only_suppliers = data['form']['only_suppliers']

        l_filter_customers = data['form']['filter_customers']
        l_filter_suppliers = data['form']['filter_suppliers']
        l_sales_man_id = data['form']['sales_man_id']
        l_move_total_without_op = data['form']['move_total_without_op']
        l_company_ids1 = data['form']['company_ids1']
        l_branch_id = data['form']['branch_id']
        l_currency_id = data['form']['currency_id']
        l_sort_type = data['form']['sort_type']
        l_report_type = data['form']['report_type']
        l_summary_options = data['form']['summary_options']
        l_display_type = data['form']['display_type']
        l_doc_state = data['form']['doc_state']
        l_report_setup= data['form']['report_setup']
        l_show_payments_before_posted = data['form']['show_payments_before_posted']
        l_branches_selected = data['form']['branches_selected']
        l_partner_branch_id = data['form']['partner_branch_id']
        l_hide_fully_credit_note = data['form']['hide_fully_credit_note']

        # l_check_branch = data['form']['check_enable_branches']
        if l_check_analytic_setting:
            analytic_field = "l.analytic_account_id"
        else:
            analytic_field = "null"
        if not l_branches_selected:
            branchs = self.env['custom.branches'].search([])
            if branchs:
                l_branch_id.clear()
                for b in branchs:
                    l_branch_id.append(b.id)

     
        move_list = ''
        if l_hide_fully_credit_note:
           if l_display_type == 'detail':
                state =[]
                if l_doc_state == 'draft' or not l_doc_state:
                    state = ['draft','posted']
                elif l_doc_state == 'posted':
                    state = ['posted']

                move_list = self.env['account.move'].search([('partner_id','=',l_partner_id),('date', '>=', date_start), ('date', '<=', date_end),('state','in', state),
                                                        ('type','=','out_refund'),('hide_credit_note_report','=',True)])
                exception_move= []
                for move in move_list:
                    if round(move.amount_total,2) != round(move.reversed_entry_id.amount_total,2):
                        exception_move.append(move.name)
                

                if exception_move:
                    raise ValidationError("تنبيه: توجد فواتير مترجعة [%s] ليست مطابقة مع فواتيرها" % exception_move)
         

        query_summary = ''
        query_payment_summary = ''
        query_summary_init = ''
        query_payment_summary_init = ''
        query_summary_move = ''
        query_payment_summary_move = ''

        query_detail = ''
        query_payment_detail = ''

        check_swailm_fields = self.env['ir.model.fields'].search([('name', '=', 'x_send_num'), ('model', '=', 'account.move')])
       

        if check_swailm_fields:
            if l_report_type == 'account':
                query_summary = """
                      select l.partner_id ,p.name as partner_name,null as analytic_account_id, l.company_id,ac.code as code, ac.name as account_name,
                       '{}' as doc_date,
                             'رصيد ماقبله' as ref,
                            null as automatic_seq ,
                             null as partner_branch_id ,

                        
                            null as type, 
                            null as type_seq,
                            null as haraj_num,		
                            null as delivery_date,
                            case when sum (debit - credit)> 0 then sum (debit - credit)  else 0 end as debit , 
                            case when sum (debit - credit) < 0 then (sum (debit - credit))*-1 else 0 end as credit , 
                            sum (debit - credit) as balance,
                            case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as fc_debit , 
                            case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as fc_credit ,
                            sum (l.amount_currency) as fc_balance

                         FROM account_move_line l
                             LEFT JOIN account_account ac ON l.account_id = ac.id 
                             LEFT JOIN res_partner p ON l.partner_id = p.id 
                             JOIN account_move h ON l.move_id = h.id
                             where l.account_id=ac.id
                             and l.partner_id is not null
                                 """
                query_payment_summary = """
                                    select  h.partner_id ,
                                            p.name as partner_name,
                                            null as analytic_account_id, 
                                            COALESCE(p.company_id, 1::numeric) as company_id,
                                             ac.code,
                                            (select a.name from account_account a where a.id=ac.id) as account_name,
                                              '{}' as doc_date,
                                            'رصيد ماقبله' as ref,
                                            null as automatic_seq ,
                                             null as partner_branch_id ,

                                            null as type, 
                                            null as type_seq,
                                            null as haraj_num,		
                                            null as delivery_date,
                                            sum(case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                            sum(case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                            sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                            0 as fc_debit , 
                                            0 as fc_credit,
                                            0 as fc_balance

                                            FROM account_payment h
                                            inner JOIN res_partner p ON h.partner_id = p.id
                                            inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                            on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                            where h.state='draft'


                                             """

                if l_display_type == 'summary':
                    query_summary += " and l.date <='{} ' ".format(date_end, date_end)
                    query_payment_summary += " and h.payment_date <='{} ' ".format(date_end, date_end)

                else:
                    query_summary += " and l.date < '{}' ".format(date_start, date_start)
                    query_payment_summary += " and h.payment_date < '{} ' ".format(date_start, date_start)

                if l_currency_id:
                    l_currency_id1 = l_currency_id[0]
                    if l_currency_id1 == self.env.company.currency_id.id:
                        query_summary += " and l.currency_id is null "
                        query_payment_summary += " and h.currency_id is null "

                    else:
                        query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                        query_payment_summary += " and h.currency_id = '{}' ".format(l_currency_id1)

                if l_display_type == 'detail':
                    query_detail = """
                                                  select l.partner_id ,
                                                  p.name as partner_name,
                                                  l.analytic_account_id,
                                                  l.company_id,
                                                  ac.code as code,
                                                  ac.name as account_name, 
                                                  l.analytic_account_id,
                                                  l.date as doc_date,
                                            case when l.ref is not null and l.name is not null then l.name || ' - ' || l.ref

                                                        when l.ref isnull and l.name is not null then l.name 
                                                        when l.ref is not null and l.name isnull then l.ref
                                                        when l.ref <>'' and l.payment_id is not null then l.ref || '( رقم السند : '|| pm.name ||')' 
                                                        when   h.type = 'out_invoice' then 'فاتورة مبيعات رقم  '|| h.name 
                
                                                        when  h.type = 'out_refund' then 'مردود مبيعات رقم ' || h.name
                                                        when   h.type = 'in_invoice' then 'فاتورة مشتريات رقم '  || h.name
                                                        when    h.type = 'in_refund' then 'مردود مشتريات رقم ' || h.name
                                                        when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية رقم ' || h.name
                                                        when   l.payment_id is not null and pm.payment_type ='inbound' then ' رقم سند القبض ( ' || pm.name || ')' 
                                                        when    l.payment_id is not null and pm.payment_type ='outbound' then 'رقم سند الصرف (' || pm.name || ')'
																 end as ref,
                                                        h.name as automatic_seq ,
                                                        h.partner_branch_id ,

                                                        case when h.type = 'out_invoice' then 'فاتورة مبيعات' 
                                                            when  h.type = 'out_refund' then 'مردود مبيعات' 
                                                            when h.type = 'in_invoice' then 'فاتورة مشتريات' 
                                                            when  h.type = 'in_refund' then 'مردود مشتريات' 
                                                            when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية' 
                                                            when  l.payment_id is not null and pm.payment_type ='inbound' then 'قيد يومية( ' || l.name || ')'
                                                            when  l.payment_id is not null and pm.payment_type ='outbound' then 'قيد يومية( ' || l.name || ')'
                                                                                                end as type,
                                                        
                                                           case when h.type = 'in_invoice' then 1 
                                                            when  h.type = 'in_refund' then 1
                                                            when  h.type = 'entry' and l.payment_id isnull then 3
                                                            when  l.payment_id is not null   then 2
                                                                                                 end as type_seq,
                                                 case when h.type  not in ('out_invoice','out_refund') then h.sale_notice_no end as haraj_num,

                                                  h.l10n_sa_delivery_date as delivery_date,

                                                  l.debit , 
                                                  l.credit , 
                                                  l.balance,
                                                  case when l.amount_currency > 0 then l.amount_currency else 0 end as fc_debit , 
                                                  case when l.amount_currency < 0 then l.amount_currency *-1 else 0 end as fc_credit,
                                                  l.amount_currency as fc_balance
                                                  FROM account_move_line l
                                                   LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                   LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                      left join account_payment pm on pm.id = l.payment_id

                                                   JOIN account_move h ON l.move_id = h.id
                                                   where l.account_id=ac.id
                                                   and l.partner_id is not null
                                                  and l.date between '{}' and '{}' 


                                      """.format(date_start, date_end)
                    query_payment_detail = """
                                    select 
                                        h.partner_id ,
                                        p.name as partner_name,
                                        null as analytic_account_id,
                                        COALESCE(p.company_id, 1::numeric) as company_id,
                                        ac.code,

                                       (select a.name from account_account a where a.id=ac.id) as account_name,

                                        null as analytic_account_id,
                                        h.payment_date as doc_date,
                                        h.communication  as "ref",

                                        h.name as automatic_seq ,
                                        h.partner_branch_id ,

                                        case when payment_type='inbound' then 'سند قبض' else 'سند صرف' end as type,	
                                        2 as type_seq,			
                                        h.notice_no as haraj_num,	
                                        h.payment_date as delivery_date,
                                        (case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                        (case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                        (case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                        0 as fc_debit , 
                                        0 as fc_credit,
                                        0 as fc_balance

                                        FROM account_payment h
                                        inner JOIN res_partner p ON h.partner_id = p.id
                                        inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                        where h.state='draft'
                                      and h.payment_date between '{}' and '{}' 


                          """.format(date_start, date_end)

                    if l_currency_id:
                        l_currency_id1 = l_currency_id[0]
                        if l_currency_id1 == self.env.company.currency_id.id:
                            query_detail += " and l.currency_id is null "
                            query_payment_detail += " and h.currency_id is null "

                        else:
                            query_detail += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_payment_detail += " and h.currency_id = '{}' ".format(l_currency_id1)

            else:
                if l_report_type == 'partner':
                    if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                        query_summary_init = """
                                                       select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                                            ,'' as code, '' as  account_name,
                                                            '{}' as doc_date,
                                                            'رصيد ماقبله' as ref,
                                                            null as automatic_seq , 
                                                            null as partner_branch_id ,

                                                            null as type,
                                                            null as type_seq,
                                                            null as  haraj_num,
                                                            
                                                            null as delivery_date,

                                                              sum (debit) as op_debit , 
                                                               sum(credit) as op_credit , 
                                                              sum (debit - credit) as op_balance,
                                                            case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as op_fc_debit , 
                                                            case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as op_fc_credit ,
                                                            sum (l.amount_currency) as op_fc_balance,
                                                            0 as  move_debit , 
                                                             0 as move_credit , 
                                                             0 as move_balance,
                                                            0 as move_fc_debit , 
                                                            0 as move_fc_credit ,
                                                            0 as move_fc_balance

                                                            FROM account_move_line l
                                                            LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                            LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                            JOIN account_move h ON l.move_id = h.id
                                                            where l.account_id=ac.id
                                                            and l.partner_id is not null

                                                             """
                        query_summary_move = """
                                                                select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                                                    ,'' as code, '' as  account_name,
                                                                    '{}' as doc_date,
                                                                    'رصيد ماقبله' as ref,
                                                                    null as automatic_seq , 
                                                                     null as partner_branch_id ,

                                                                    null as type,
                                                                    null as type_seq,
                                                                    null as haraj_num,	
                                                                    null as delivery_date,
                                                                    0 as  op_debit , 
                                                                     0 as op_credit , 
                                                                     0 as op_balance,
                                                                    0 as op_fc_debit , 
                                                                    0 as op_fc_credit ,
                                                                    0 as op_fc_balance,

                                                                    sum (debit) as move_debit , 
                                                                    sum (credit) as move_credit , 
                                                                    sum (debit - credit) as move_balance,
                                                                    case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as move_fc_debit , 
                                                                    case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as move_fc_credit ,
                                                                    sum (l.amount_currency) as move_fc_balance

                                                                    FROM account_move_line l
                                                                    LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                                    LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                                    JOIN account_move h ON l.move_id = h.id
                                                                    where l.account_id=ac.id
                                                                    and l.partner_id is not null

                                                                 """
                        query_payment_summary_init = """
                                                            select    h.partner_id ,
                                                                        p.name as partner_name,
                                                                        null as analytic_account_id, 
                                                                        COALESCE(p.company_id, 1::numeric)  as company_id,
                                                                        '' as code, '' as  account_name,
                                                                        '{}' as doc_date,
                                                                        'رصيد ماقبله' as ref,
                                                                        null as automatic_seq ,
                                                                         null as partner_branch_id ,

                                                                        null as type, 
                                                                        null as type_seq,
                                                                        null as haraj_num,	
                                                                        null as delivery_date,
                                                                        sum(case when payment_type = 'outbound' then h.amount else 0 end) as op_debit , 
                                                                        sum(case when payment_type = 'inbound' then h.amount else 0 end) as op_credit , 
                                                                        sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) op_balance,
                                                                        0 as op_fc_debit , 
                                                                        0 as op_fc_credit,
                                                                        0 as op_fc_balance,
                                                                        0 as move_debit , 
                                                                         0 as move_credit , 
                                                                        0 as move_balance,
                                                                        0 as move_fc_debit , 
                                                                        0 as move_fc_credit,
                                                                        0 as move_fc_balance


                                                                        FROM account_payment h
                                                                        inner JOIN res_partner p ON h.partner_id = p.id
                                                                        inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                                        where h.state='draft'

                                                             """
                        query_payment_summary_move = """
                                                       select    h.partner_id ,
                                                                   p.name as partner_name,
                                                                   null as analytic_account_id, 
                                                                   COALESCE(p.company_id, 1::numeric)  as company_id,
                                                                   '' as code, '' as  account_name,
                                                                   '{}' as doc_date,
                                                                   'رصيد ماقبله' as ref,
                                                                   null as automatic_seq ,
                                                                    null as partner_branch_id ,

                                                                   null as type, 
                                                                   null as type_seq,
                                                                   null as haraj_num,	
                                                                   null as delivery_date,

                                                                    0 as op_debit , 
                                                                    0 as op_credit , 
                                                                   0 as op_balance,
                                                                   0 as op_fc_debit , 
                                                                   0 as op_fc_credit,
                                                                   0 as op_fc_balance,

                                                                   sum(case when payment_type = 'outbound' then h.amount else 0 end) as move_debit , 
                                                                   sum(case when payment_type = 'inbound' then h.amount else 0 end) as move_credit , 
                                                                   sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) move_balance,
                                                                   0 as move_fc_debit , 
                                                                   0 as move_fc_credit,
                                                                   0 as move_fc_balance 


                                                                   FROM account_payment h
                                                                   inner JOIN res_partner p ON h.partner_id = p.id
                                                                   inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                                   on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                                   where h.state='draft'

                                                        """
                    else:
                        query_summary = """
                                                    select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                                          ,'' as code, '' as  account_name,
                                                            '{}' as doc_date,
                                                       'رصيد ماقبله' as ref,
                                                        null as automatic_seq , 
                                                          null as partner_branch_id ,

                                                        null as type,
                                                        null as type_seq,
                                                        null as haraj_num,	
                                                        null as delivery_date,

                                                        case when sum (debit - credit)> 0 then sum (debit - credit) else 0 end as debit , 
                                                        case when sum (debit - credit) < 0 then (sum (debit - credit))*-1 else 0 end as credit , 
                                                          sum (debit - credit) as balance,
                                                        case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as fc_debit , 
                                                        case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as fc_credit ,
                                                        sum (l.amount_currency) as fc_balance

                                                             FROM account_move_line l
                                                                 LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                                 LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                                 JOIN account_move h ON l.move_id = h.id
                                                                 where l.account_id=ac.id
                                                                 and l.partner_id is not null
                                                         """
                        query_payment_summary = """
                                                        select    h.partner_id ,
                                                            p.name as partner_name,
                                                            null as analytic_account_id, 
                                                            COALESCE(p.company_id, 1::numeric)  as company_id,
                                                             '' as code, '' as  account_name,
                                                             '{}' as doc_date,
                                                            'رصيد ماقبله' as ref,
                                                            null as automatic_seq ,
                                                             null as partner_branch_id ,

                                                            null as type, 
                                                            null as type_seq,
                                                            null as haraj_num,	
                                                            null as delivery_date,


                                                            sum(case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                                            sum(case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                                            sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                                            0 as fc_debit , 
                                                            0 as fc_credit,
                                                            0 as fc_balance

                                                            FROM account_payment h
                                                            inner JOIN res_partner p ON h.partner_id = p.id
                                                             inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                             on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                            where h.state='draft'

                                                         """

                    if l_display_type == 'summary':
                        if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                            query_summary_init += " and l.date < '{}' ".format(date_start, date_start)
                            query_payment_summary_init += " and h.payment_date < '{}' ".format(date_start, date_start)

                            query_summary_move += " and l.date between '{}' and '{}' ".format(date_start, date_end,
                                                                                              date_start)
                            query_payment_summary_move += " and h.payment_date between '{}' and '{}' ".format(
                                date_start, date_end, date_start)

                        else:
                            query_summary += " and l.date <='{}' ".format(date_end, date_end)
                            query_payment_summary += " and h.payment_date <='{}' ".format(date_end, date_end)

                    else:
                        query_summary += " and l.date < '{}' ".format(date_start, date_start)
                        query_payment_summary += " and h.payment_date < '{}' ".format(date_start, date_start)

                    if l_currency_id:
                        l_currency_id1 = l_currency_id[0]
                        if l_currency_id1 == self.env.company.currency_id.id:
                            if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                                query_summary_init += " and l.currency_id is null "
                                query_payment_summary_init += " and l.currency_id is null "

                                query_summary_move += " and l.currency_id is null "
                                query_payment_summary_move += " and l.currency_id is null "
                            else:
                                query_summary += " and l.currency_id is null "
                                query_payment_summary += " and h.currency_id is null "

                        else:
                            if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                                query_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)

                            else:

                                query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary += " and h.currency_id = '{}' ".format(l_currency_id1)

                    if l_display_type == 'detail':
                        query_detail = """
                                                                          select l.partner_id,
                                                                          p.name as partner_name,
                                                                           l.analytic_account_id,
                                                                          l.company_id,
                                                                          ac.code as code,
                                                                          ac.name as account_name, 
                                                                          l.date as doc_date,
                                                                        case when l.ref is not null and l.name is not null then l.name || ' - ' || l.ref

                                                                                when l.ref isnull and l.name is not null then l.name 
                                                                                when l.ref is not null and l.name isnull then l.ref
                                                                                when l.ref <>'' and l.payment_id is not null then l.ref || '( رقم السند : '|| pm.name ||')' 
                                                                                when   h.type = 'out_invoice' then 'فاتورة مبيعات رقم  '|| h.name 

                                                                                when  h.type = 'out_refund' then 'مردود مبيعات رقم ' || h.name
                                                                                when   h.type = 'in_invoice' then 'فاتورة مشتريات رقم '  || h.name
                                                                                when    h.type = 'in_refund' then 'مردود مشتريات رقم ' || h.name
                                                                                when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية رقم ' || h.name
                                                                                when   l.payment_id is not null and pm.payment_type ='inbound' then ' رقم سند القبض ( ' || pm.name || ')' 
                                                                                when    l.payment_id is not null and pm.payment_type ='outbound' then 'رقم سند الصرف (' || pm.name || ')'
                																 end as ref,
                                                                            h.name as automatic_seq ,
                                                                            h.partner_branch_id ,

                                                                            case when h.type = 'out_invoice' then 'فاتورة مبيعات' 
                                                                                when  h.type = 'out_refund' then 'مردود مبيعات' 
                                                                                when h.type = 'in_invoice' then 'فاتورة مشتريات' 
                                                                                when  h.type = 'in_refund' then 'مردود مشتريات' 
                                                                                when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية' 
                                                                                when  l.payment_id is not null and pm.payment_type ='inbound' then 'قيد يومية( ' || l.name || ')'
                                                                                when  l.payment_id is not null and pm.payment_type ='outbound' then 'قيد يومية( ' || l.name || ')'
                                                                                                                    end as type,

                                                                           case when h.type = 'in_invoice' then 1 
                                                                            when  h.type = 'in_refund' then 1
                                                                            when  h.type = 'entry' and l.payment_id isnull then 3
                                                                            when  l.payment_id is not null   then 2
                                                                                                                 end as type_seq,	
                                                                            case when h.type  not in ('out_invoice','out_refund') then h.sale_notice_no end as haraj_num,
                                                                            h.l10n_sa_delivery_date as delivery_date,
                                                                            l.debit , 
                                                                            l.credit , 
                                                                            l.balance,
                                                                            case when l.amount_currency > 0 then l.amount_currency else 0 end as fc_debit , 
                                                                            case when l.amount_currency < 0 then l.amount_currency *-1 else 0 end as fc_credit,
                                                                            l.amount_currency as fc_balance
                                                                          FROM account_move_line l
                                                                           LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                                           LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                                               left join account_payment pm on pm.id = l.payment_id

                                                                           JOIN account_move h ON l.move_id = h.id
                                                                           where l.account_id=ac.id
                                                                           and l.partner_id is not null

                                                                           and l.date between '{}' and '{}' 
                                                                          """.format(date_start, date_end)
                        query_payment_detail = """
                                                                  select 
                                                                        h.partner_id ,
                                                                        p.name as partner_name,
                                                                        null as analytic_account_id,
                                                                        COALESCE(p.company_id, 1::numeric) as company_id,
                                                                        ac.code,
                                                                        (select a.name from account_account a where a.id=ac.id) as account_name,
                                                                         h.payment_date as doc_date,
                                                                        h.communication  as "ref",

                                                                        h.name as automatic_seq ,
                                                                        h.partner_branch_id ,

                                                                        case when payment_type='inbound' then 'سند قبض' else 'سند صرف' end as type,	
                                                                        2 as type_seq,
                                                                         h.notice_no as haraj_num,					
                                                                         h.payment_date as delivery_date,
                                                                        (case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                                                        (case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                                                        (case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                                                        0 as fc_debit , 
                                                                        0 as fc_credit,
                                                                        0 as fc_balance

                                                                        FROM account_payment h
                                                                        inner JOIN res_partner p ON h.partner_id = p.id
                                                                         inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                                        where h.state='draft'

                                                                       and h.payment_date between '{}' and '{}' 
                                                                      """.format(date_start, date_end)

                        if l_currency_id:
                            l_currency_id1 = l_currency_id[0]
                            if l_currency_id1 == self.env.company.currency_id.id:
                                query_detail += " and l.currency_id is null "
                                query_payment_detail += " and h.currency_id is null "

                            else:
                                query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_detail += " and h.currency_id = '{}' ".format(l_currency_id1)

                # if l_report_type == 'partner':
                #     query_summary = """
                #                         select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                #                               ,'' as code, '' as  account_name,
                #                                 '{}' as doc_date,
                #                            'رصيد ماقبله' as ref,
                #                             null as automatic_seq ,
                #                             null as type,
                #                             null as type_seq,
                #                            null as haraj_num,
                #
                #                             null as delivery_date,
                #
                #                             case when sum (debit - credit)> 0 then sum (debit - credit) else 0 end as debit ,
                #                             case when sum (debit - credit) < 0 then (sum (debit - credit))*-1 else 0 end as credit ,
                #                               sum (debit - credit) as balance,
                #                             case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as fc_debit ,
                #                             case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as fc_credit ,
                #                             sum (l.amount_currency) as fc_balance
                #
                #                                  FROM account_move_line l
                #                                      LEFT JOIN account_account ac ON l.account_id = ac.id
                #                                      LEFT JOIN res_partner p ON l.partner_id = p.id
                #                                      JOIN account_move h ON l.move_id = h.id
                #                                      where l.account_id=ac.id
                #                                      and l.partner_id is not null
                #                              """
                #     query_payment_summary = """
                #                             select    h.partner_id ,
                #                                 p.name as partner_name,
                #                                 null as analytic_account_id,
                #                                 COALESCE(p.company_id, 1::numeric)  as company_id,
                #                                  '' as code, '' as  account_name,
                #                                  '{}' as doc_date,
                #                                 'رصيد ماقبله' as ref,
                #                                 null as automatic_seq ,
                #                                 null as type,
                #                                 null as type_seq,
                #                                 null as haraj_num,
                #
                #                                 null as delivery_date,
                #
                #
                #                                 sum(case when payment_type = 'outbound' then h.amount else 0 end) as debit ,
                #                                 sum(case when payment_type = 'inbound' then h.amount else 0 end) as credit ,
                #                                 sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                #                                 0 as fc_debit ,
                #                                 0 as fc_credit,
                #                                 0 as fc_balance
                #
                #                                 FROM account_payment h
                #                                 inner JOIN res_partner p ON h.partner_id = p.id
                #                                  inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac
                #                                  on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end
                #
                #                                 where h.state='draft'
                #
                #                              """
                #
                #     if l_display_type == 'summary':
                #         query_summary += " and l.date <='{}' ".format(date_end, date_end)
                #         query_payment_summary += " and h.payment_date <='{}' ".format(date_end, date_end)
                #
                #     else:
                #         query_summary += " and l.date < '{}' ".format(date_start, date_start)
                #         query_payment_summary += " and h.payment_date < '{}' ".format(date_start, date_start)
                #
                #     if l_currency_id:
                #         l_currency_id1 = l_currency_id[0]
                #         if l_currency_id1 == self.env.company.currency_id.id:
                #             query_summary += " and l.currency_id is null "
                #             query_payment_summary += " and h.currency_id is null "
                #
                #         else:
                #             query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                #             query_payment_summary += " and h.currency_id = '{}' ".format(l_currency_id1)
                #
                #     if l_display_type == 'detail':
                #         query_detail = """
                #                                           select l.partner_id,
                #                                           p.name as partner_name,
                #                                            l.analytic_account_id,
                #                                           l.company_id,
                #                                           ac.code as code,
                #                                           ac.name as account_name,
                #                                           l.date as doc_date,
                #                                           case when l.ref is not null and l.name is not null then l.name || ' - ' || l.ref
                #
                #                                                 when l.ref isnull and l.name is not null then l.name
                #                                                 when l.ref is not null and l.name isnull then l.ref
                #                                                 when l.ref <>'' and l.payment_id is not null then l.ref || '( رقم السند : '|| pm.name ||')'
                #                                                 when   h.type = 'out_invoice' then 'فاتورة مبيعات رقم  '|| h.name
                #
                #                                                 when  h.type = 'out_refund' then 'مردود مبيعات رقم ' || h.name
                #                                                 when   h.type = 'in_invoice' then 'فاتورة مشتريات رقم '  || h.name
                #                                                 when    h.type = 'in_refund' then 'مردود مشتريات رقم ' || h.name
                #                                                 when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية رقم ' || h.name
                #                                                 when   l.payment_id is not null and pm.payment_type ='inbound' then ' رقم سند القبض ( ' || pm.name || ')'
                #                                                 when    l.payment_id is not null and pm.payment_type ='outbound' then 'رقم سند الصرف (' || pm.name || ')'
				# 												 end as ref,
                #
                #                                             h.name as automatic_seq ,
                #                                             case when h.type = 'out_invoice' then 'فاتورة مبيعات'
                #                                                 when  h.type = 'out_refund' then 'مردود مبيعات'
                #                                                 when h.type = 'in_invoice' then 'فاتورة مشتريات'
                #                                                 when  h.type = 'in_refund' then 'مردود مشتريات'
                #                                                 when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية'
                #                                                 when  l.payment_id is not null and pm.payment_type ='inbound' then 'قيد يومية( ' || l.name || ')'
                #                                                 when  l.payment_id is not null and pm.payment_type ='outbound' then 'قيد يومية( ' || l.name || ')'
                #                                                                                     end as type,
                #
                #                                            case when h.type = 'in_invoice' then 1
                #                                             when  h.type = 'in_refund' then 1
                #                                             when  h.type = 'entry' and l.payment_id isnull then 3
                #                                             when  l.payment_id is not null   then 2
                #                                                                                  end as type_seq,
                #                                              case when h.type  not in ('out_invoice','out_refund') then h.sale_notice_no end as haraj_num,
                #
                #                                            h.l10n_sa_delivery_date as delivery_date,
                #                                             l.debit ,
                #                                             l.credit ,
                #                                             l.balance,
                #                                             case when l.amount_currency > 0 then l.amount_currency else 0 end as fc_debit ,
                #                                             case when l.amount_currency < 0 then l.amount_currency *-1 else 0 end as fc_credit,
                #                                             l.amount_currency as fc_balance
                #                                           FROM account_move_line l
                #                                            LEFT JOIN account_account ac ON l.account_id = ac.id
                #                                            LEFT JOIN res_partner p ON l.partner_id = p.id
                #                                                left join account_payment pm on pm.id = l.payment_id
                #
                #                                            JOIN account_move h ON l.move_id = h.id
                #                                            where l.account_id=ac.id
                #                                            and l.partner_id is not null
                #
                #                                            and l.date between '{}' and '{}'
                #                                           """.format(date_start, date_end)
                #         query_payment_detail = """
                #                                   select
                #                                         h.partner_id ,
                #                                         p.name as partner_name,
                #                                         null as analytic_account_id,
                #                                         COALESCE(p.company_id, 1::numeric) as company_id,
                #                                         ac.code,
                #                                         (select a.name from account_account a where a.id=ac.id) as account_name,
                #                                          h.payment_date as doc_date,
                #                                         h.communication  as "ref",
                #
                #                                         h.name as automatic_seq ,
                #                                         case when payment_type='inbound' then 'سند قبض' else 'سند صرف' end as type,
                #                                         2 as type_seq,
                #                                         h.notice_no as haraj_num,
                #                                         h.payment_date as delivery_date,
                #                                         (case when payment_type = 'outbound' then h.amount else 0 end) as debit ,
                #                                         (case when payment_type = 'inbound' then h.amount else 0 end) as credit ,
                #                                         (case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                #                                         0 as fc_debit ,
                #                                         0 as fc_credit,
                #                                         0 as fc_balance
                #
                #                                         FROM account_payment h
                #                                         inner JOIN res_partner p ON h.partner_id = p.id
                #                                          inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac
                #                                         on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end
                #
                #                                         where h.state='draft'
                #
                #                                        and h.payment_date between '{}' and '{}'
                #                                       """.format(date_start, date_end)
                #
                #         if l_currency_id:
                #             l_currency_id1 = l_currency_id[0]
                #             if l_currency_id1 == self.env.company.currency_id.id:
                #                 query_detail += " and l.currency_id is null "
                #                 query_payment_detail += " and h.currency_id is null "
                #
                #             else:
                #                 query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                #                 query_payment_detail += " and h.currency_id = '{}' ".format(l_currency_id1)
        else:
            if l_report_type == 'account':
                if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                        query_summary_init = """
                                      select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                           ,ac.code as code, ac.name as account_name,
                                           '{}' as doc_date,
                                           'رصيد ماقبله' as ref,
                                           null as automatic_seq , 
                                           null as partner_branch_id ,

                                           null as type,
                                           null as type_seq,
                                           null as delivery_date,

                                           sum (debit) as op_debit , 
                                           sum(credit) as op_credit , 
                                           sum (debit - credit) as op_balance,
                                           case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as op_fc_debit , 
                                           case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as op_fc_credit ,
                                           sum (l.amount_currency) as op_fc_balance,
                                           0 as  move_debit , 
                                            0 as move_credit , 
                                            0 as move_balance,
                                           0 as move_fc_debit , 
                                           0 as move_fc_credit ,
                                           0 as move_fc_balance

                                           FROM account_move_line l
                                           LEFT JOIN account_account ac ON l.account_id = ac.id 
                                           LEFT JOIN res_partner p ON l.partner_id = p.id 
                                           JOIN account_move h ON l.move_id = h.id
                                           where l.account_id=ac.id
                                           and l.partner_id is not null

                                            """
                        query_summary_move = """
                                               select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                                   ,ac.code as code, ac.name as account_name,
                                                   '{}' as doc_date,
                                                   'رصيد ماقبله' as ref,
                                                   null as automatic_seq , 
                                                  null as partner_branch_id ,

                                                   null as type,
                                                   null as type_seq,
                                                   null as delivery_date,
                                                   0 as  op_debit , 
                                                    0 as op_credit , 
                                                    0 as op_balance,
                                                   0 as op_fc_debit , 
                                                   0 as op_fc_credit ,
                                                   0 as op_fc_balance,

                                                   sum (debit)  as move_debit , 
                                                   sum (credit) as move_credit , 
                                                   sum (debit - credit) as move_balance,
                                                   case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as move_fc_debit , 
                                                   case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as move_fc_credit ,
                                                   sum (l.amount_currency) as move_fc_balance

                                                   FROM account_move_line l
                                                   LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                   LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                   JOIN account_move h ON l.move_id = h.id
                                                   where l.account_id=ac.id
                                                   and l.partner_id is not null

                                                """
                        query_payment_summary_init = """
                                           select    h.partner_id ,
                                                       p.name as partner_name,
                                                       null as analytic_account_id, 
                                                       COALESCE(p.company_id, 1::numeric)  as company_id,
                                                       ac.code,
                                                       (select a.name from account_account a where a.id=ac.id) as account_name,
                                                       '{}' as doc_date,
                                                       'رصيد ماقبله' as ref,
                                                       null as automatic_seq ,
                                                          null as partner_branch_id ,

                                                       null as type, 
                                                       null as type_seq,
                                                       null as delivery_date,
                                                       sum(case when payment_type = 'outbound' then h.amount else 0 end) as op_debit , 
                                                       sum(case when payment_type = 'inbound' then h.amount else 0 end) as op_credit , 
                                                       sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) op_balance,
                                                       0 as op_fc_debit , 
                                                       0 as op_fc_credit,
                                                       0 as op_fc_balance,
                                                       0 as move_debit , 
                                                        0 as move_credit , 
                                                       0 as move_balance,
                                                       0 as move_fc_debit , 
                                                       0 as move_fc_credit,
                                                       0 as move_fc_balance


                                                       FROM account_payment h
                                                       inner JOIN res_partner p ON h.partner_id = p.id
                                                       inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                       on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                       where h.state='draft'

                                            """
                        query_payment_summary_move = """
                                      select    h.partner_id ,
                                                  p.name as partner_name,
                                                  null as analytic_account_id, 
                                                  COALESCE(p.company_id, 1::numeric)  as company_id,
                                                  ac.code,
                                             (select a.name from account_account a where a.id=ac.id) as account_name,
                                                  '{}' as doc_date,
                                                  'رصيد ماقبله' as ref,
                                                  null as automatic_seq ,
                                                  null as partner_branch_id ,

                                                  null as type, 
                                                  null as type_seq,
                                                  null as delivery_date,

                                                   0 as op_debit , 
                                                   0 as op_credit , 
                                                  0 as op_balance,
                                                  0 as op_fc_debit , 
                                                  0 as op_fc_credit,
                                                  0 as op_fc_balance,

                                                  sum(case when payment_type = 'outbound' then h.amount else 0 end) as move_debit , 
                                                  sum(case when payment_type = 'inbound' then h.amount else 0 end) as move_credit , 
                                                  sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) move_balance,
                                                  0 as move_fc_debit , 
                                                  0 as move_fc_credit,
                                                  0 as move_fc_balance 


                                                  FROM account_payment h
                                                  inner JOIN res_partner p ON h.partner_id = p.id
                                                  inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                  on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                  where h.state='draft'

                                       """
                else:
                    query_summary = """
                       select l.partner_id ,p.name as partner_name,null as analytic_account_id, l.company_id,ac.code as code, ac.name as account_name,
                        '{}' as doc_date,
                              'رصيد ماقبله' as ref,
                             null as automatic_seq ,
                             null as partner_branch_id ,

                             null as type, 
                             null as type_seq,
                            null as delivery_date,

                             case when sum (debit - credit)> 0 then sum (debit - credit)  else 0 end as debit , 
                             case when sum (debit - credit) < 0 then (sum (debit - credit))*-1 else 0 end as credit , 
                             sum (debit - credit) as balance,
                             case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as fc_debit , 
                             case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as fc_credit ,
                             sum (l.amount_currency) as fc_balance

                          FROM account_move_line l
                              LEFT JOIN account_account ac ON l.account_id = ac.id 
                              LEFT JOIN res_partner p ON l.partner_id = p.id 
                              JOIN account_move h ON l.move_id = h.id
                              where l.account_id=ac.id
                              and l.partner_id is not null


                                  """

                    query_payment_summary = """
                                     select  h.partner_id ,
                                             p.name as partner_name,
                                             null as analytic_account_id, 
                                             COALESCE(p.company_id, 1::numeric) as company_id,
                                              ac.code,
                                             (select a.name from account_account a where a.id=ac.id) as account_name,
                                               '{}' as doc_date,
                                             'رصيد ماقبله' as ref,
                                             null as automatic_seq ,
                                                                          null as partner_branch_id ,

                                             null as type, 
                                             null as type_seq,
                                             null as delivery_date,

                                             sum(case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                             sum(case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                             sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                             0 as fc_debit , 
                                             0 as fc_credit,
                                             0 as fc_balance

                                             FROM account_payment h
                                             inner JOIN res_partner p ON h.partner_id = p.id
                                             inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                             on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                             where h.state='draft'

                                              """

                if l_display_type == 'summary':
                    if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                        query_summary_init += " and l.date < '{}' ".format(date_start, date_start)
                        query_payment_summary_init += " and h.payment_date < '{}' ".format(date_start, date_start)

                        query_summary_move += " and l.date between '{}' and '{}' ".format(date_start, date_end,
                                                                                          date_start)
                        query_payment_summary_move += " and h.payment_date between '{}' and '{}' ".format(date_start,
                                                                                                          date_end,
                                                                                                          date_start)

                    else:
                        query_summary += " and l.date <='{}' ".format(date_end, date_end)
                        query_payment_summary += " and h.payment_date <='{}' ".format(date_end, date_end)

                else:
                    query_summary += " and l.date < '{}' ".format(date_start, date_start)
                    query_payment_summary += " and h.payment_date < '{}' ".format(date_start, date_start)

                if l_currency_id:
                    l_currency_id1 = l_currency_id[0]
                    if l_currency_id1 == self.env.company.currency_id.id:
                        if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                            query_summary_init += " and l.currency_id is null "
                            query_payment_summary_init += " and l.currency_id is null "

                            query_summary_move += " and l.currency_id is null "
                            query_payment_summary_move += " and l.currency_id is null "
                        else:
                            query_summary += " and l.currency_id is null "
                            query_payment_summary += " and h.currency_id is null "

                    else:
                        if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                            query_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_payment_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_payment_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)

                        else:

                            query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_payment_summary += " and h.currency_id = '{}' ".format(l_currency_id1)

                if l_display_type == 'detail':
                    query_detail = """
                                          select l.partner_id ,
                                          p.name as partner_name,
                                          l.analytic_account_id,
                                          l.company_id,
                                          ac.code as code,
                                          ac.name as account_name, 
                                          l.analytic_account_id,
                                          l.date as doc_date,
                                            case when l.ref is not null and l.name is not null then l.name || ' - ' || l.ref

                                                        when l.ref isnull and l.name is not null then l.name 
                                                        when l.ref is not null and l.name isnull then l.ref
                                                        when l.ref <>'' and l.payment_id is not null then l.ref || '( رقم السند : '|| pm.name ||')' 
                                                        when   h.type = 'out_invoice' then 'فاتورة مبيعات رقم  '|| h.name 
                
                                                        when  h.type = 'out_refund' then 'مردود مبيعات رقم ' || h.name
                                                        when   h.type = 'in_invoice' then 'فاتورة مشتريات رقم '  || h.name
                                                        when    h.type = 'in_refund' then 'مردود مشتريات رقم ' || h.name
                                                        when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية رقم ' || h.name
                                                        when   l.payment_id is not null and pm.payment_type ='inbound' then ' رقم سند القبض ( ' || pm.name || ')' 
                                                        when    l.payment_id is not null and pm.payment_type ='outbound' then 'رقم سند الصرف (' || pm.name || ')'
                                                         end as ref,
                                                h.name as automatic_seq ,
                                                h.partner_branch_id ,

                                                case when h.type = 'out_invoice' then 'فاتورة مبيعات' 
                                                    when  h.type = 'out_refund' then 'مردود مبيعات' 
                                                    when h.type = 'in_invoice' then 'فاتورة مشتريات' 
                                                    when  h.type = 'in_refund' then 'مردود مشتريات' 
                                                    when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية' 
                                                    when  l.payment_id is not null and pm.payment_type ='inbound' then 'قيد يومية( ' || l.name || ')'
                                                    when  l.payment_id is not null and pm.payment_type ='outbound' then 'قيد يومية( ' || l.name || ')'
                                                                                        end as type,
                                            case   when h.type = 'in_invoice' then 1 
                                                    when  h.type = 'in_refund' then 1
                                                    when  h.type = 'entry' and l.payment_id isnull then 3
                                                    when  l.payment_id is not null   then 2
                                                                                         end as type_seq,
                                           h.l10n_sa_delivery_date as delivery_date,

                                          l.debit , 
                                          l.credit , 
                                          l.balance,
                                          case when l.amount_currency > 0 then l.amount_currency else 0 end as fc_debit , 
                                          case when l.amount_currency < 0 then l.amount_currency *-1 else 0 end as fc_credit,
                                          l.amount_currency as fc_balance
                                          FROM account_move_line l
                                           LEFT JOIN account_account ac ON l.account_id = ac.id 
                                           LEFT JOIN res_partner p ON l.partner_id = p.id 
                                              left join account_payment pm on pm.id = l.payment_id

                                           JOIN account_move h ON l.move_id = h.id
                                           where l.account_id=ac.id
                                           and l.partner_id is not null
                                          and l.date between '{}' and '{}' 

    
                                      """.format(date_start, date_end)
                    query_payment_detail = """
                                    select 
                                        h.partner_id ,
                                        p.name as partner_name,
                                        null as analytic_account_id,
                                        COALESCE(p.company_id, 1::numeric) as company_id,
                                        ac.code,
                                        
                                       (select a.name from account_account a where a.id=ac.id) as account_name,
                                        
                                        null as analytic_account_id,
                                        h.payment_date as doc_date,
                                        h.communication  as "ref",
                                        
                                        h.name as automatic_seq ,
                                        h.partner_branch_id ,

                                        case when payment_type='inbound' then 'سند قبض' else 'سند صرف' end as type,	
                                        2 as type_seq,		
                                         h.payment_date as delivery_date,
                                        (case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                        (case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                        (case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                        0 as fc_debit , 
                                        0 as fc_credit,
                                        0 as fc_balance
                                        
                                        FROM account_payment h
                                        inner JOIN res_partner p ON h.partner_id = p.id
                                        inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end
    
                                        where h.state='draft'
                                      and h.payment_date between '{}' and '{}' 
    
    
                          """.format(date_start, date_end)

                    if l_currency_id:
                        l_currency_id1 = l_currency_id[0]
                        if l_currency_id1 == self.env.company.currency_id.id:
                            query_detail += " and l.currency_id is null "
                            query_payment_detail += " and h.currency_id is null "

                        else:
                            query_detail += " and l.currency_id = '{}' ".format(l_currency_id1)
                            query_payment_detail += " and h.currency_id = '{}' ".format(l_currency_id1)

            else:
                if l_report_type == 'partner':
                    if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                            query_summary_init = """
                                       select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                            ,'' as code, '' as  account_name,
                                            '{}' as doc_date,
                                            'رصيد ماقبله' as ref,
                                            null as automatic_seq , 
                                             null as partner_branch_id ,

                                            null as type,
                                            null as type_seq,
                                            null as delivery_date,
                                            
                                             sum (debit) as op_debit , 
                                            sum (credit) as op_credit , 
                                            sum (debit - credit) as op_balance,
                                            case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as op_fc_debit , 
                                            case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as op_fc_credit ,
                                            sum (l.amount_currency) as op_fc_balance,
                                            0 as  move_debit , 
                                             0 as move_credit , 
                                             0 as move_balance,
                                            0 as move_fc_debit , 
                                            0 as move_fc_credit ,
                                            0 as move_fc_balance
                                            
                                            FROM account_move_line l
                                            LEFT JOIN account_account ac ON l.account_id = ac.id 
                                            LEFT JOIN res_partner p ON l.partner_id = p.id 
                                            JOIN account_move h ON l.move_id = h.id
                                            where l.account_id=ac.id
                                            and l.partner_id is not null
                                             
                                             """
                            query_summary_move = """
                                                select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                                    ,'' as code, '' as  account_name,
                                                    '{}' as doc_date,
                                                    'رصيد ماقبله' as ref,
                                                    null as automatic_seq , 
                                                                                 null as partner_branch_id ,

                                                    null as type,
                                                    null as type_seq,
                                                    null as delivery_date,
                                                    0 as  op_debit , 
                                                     0 as op_credit , 
                                                     0 as op_balance,
                                                    0 as op_fc_debit , 
                                                    0 as op_fc_credit ,
                                                    0 as op_fc_balance,
                                                    
                                                     sum (debit)  as move_debit , 
                                                    sum (credit)  as move_credit , 
                                                    sum (debit - credit) as move_balance,
                                                    case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as move_fc_debit , 
                                                    case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as move_fc_credit ,
                                                    sum (l.amount_currency) as move_fc_balance
                                                     
                                                    FROM account_move_line l
                                                    LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                    LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                    JOIN account_move h ON l.move_id = h.id
                                                    where l.account_id=ac.id
                                                    and l.partner_id is not null
                                                 
                                                 """
                            query_payment_summary_init = """
                                            select    h.partner_id ,
                                                        p.name as partner_name,
                                                        null as analytic_account_id, 
                                                        COALESCE(p.company_id, 1::numeric)  as company_id,
                                                        '' as code, '' as  account_name,
                                                        '{}' as doc_date,
                                                        'رصيد ماقبله' as ref,
                                                        null as automatic_seq ,
                                                                                     null as partner_branch_id ,

                                                        null as type, 
                                                        null as type_seq,
                                                        null as delivery_date,
                                                        sum(case when payment_type = 'outbound' then h.amount else 0 end) as op_debit , 
                                                        sum(case when payment_type = 'inbound' then h.amount else 0 end) as op_credit , 
                                                        sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) op_balance,
                                                        0 as op_fc_debit , 
                                                        0 as op_fc_credit,
                                                        0 as op_fc_balance,
                                                        0 as move_debit , 
                                                         0 as move_credit , 
                                                        0 as move_balance,
                                                        0 as move_fc_debit , 
                                                        0 as move_fc_credit,
                                                        0 as move_fc_balance
                                                        
                                                        
                                                        FROM account_payment h
                                                        inner JOIN res_partner p ON h.partner_id = p.id
                                                        inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end
                                                        
                                                        where h.state='draft'

                                             """
                            query_payment_summary_move = """
                                       select    h.partner_id ,
                                                   p.name as partner_name,
                                                   null as analytic_account_id, 
                                                   COALESCE(p.company_id, 1::numeric)  as company_id,
                                                   '' as code, '' as  account_name,
                                                   '{}' as doc_date,
                                                   'رصيد ماقبله' as ref,
                                                   null as automatic_seq ,
                                                                                null as partner_branch_id ,

                                                   null as type, 
                                                   null as type_seq,
                                                   null as delivery_date,
                                                   
                                                    0 as op_debit , 
                                                    0 as op_credit , 
                                                   0 as op_balance,
                                                   0 as op_fc_debit , 
                                                   0 as op_fc_credit,
                                                   0 as op_fc_balance,

                                                   sum(case when payment_type = 'outbound' then h.amount else 0 end) as move_debit , 
                                                   sum(case when payment_type = 'inbound' then h.amount else 0 end) as move_credit , 
                                                   sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) move_balance,
                                                   0 as move_fc_debit , 
                                                   0 as move_fc_credit,
                                                   0 as move_fc_balance 


                                                   FROM account_payment h
                                                   inner JOIN res_partner p ON h.partner_id = p.id
                                                   inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                   on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                                   where h.state='draft'

                                        """
                    else:
                        query_summary = """
                                    select l.partner_id, p.name as partner_name,null as analytic_account_id, l.company_id
                                          ,'' as code, '' as  account_name,
                                            '{}' as doc_date,
                                       'رصيد ماقبله' as ref,
                                        null as automatic_seq , 
                                                                     null as partner_branch_id ,

                                        null as type,
                                        null as type_seq,
                                        null as delivery_date,

                                        case when sum (debit - credit)> 0 then sum (debit - credit) else 0 end as debit , 
                                        case when sum (debit - credit) < 0 then (sum (debit - credit))*-1 else 0 end as credit , 
                                          sum (debit - credit) as balance,
                                        case when sum (l.amount_currency) > 0 then sum (l.amount_currency)  else 0 end as fc_debit , 
                                        case when sum (l.amount_currency) < 0 then sum (l.amount_currency) *-1  else 0 end as fc_credit ,
                                        sum (l.amount_currency) as fc_balance

                                             FROM account_move_line l
                                                 LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                 LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                 JOIN account_move h ON l.move_id = h.id
                                                 where l.account_id=ac.id
                                                 and l.partner_id is not null
                                         """
                        query_payment_summary = """
                                        select    h.partner_id ,
                                            p.name as partner_name,
                                            null as analytic_account_id, 
                                            COALESCE(p.company_id, 1::numeric)  as company_id,
                                             '' as code, '' as  account_name,
                                             '{}' as doc_date,
                                            'رصيد ماقبله' as ref,
                                            null as automatic_seq ,
                                                                         null as partner_branch_id ,

                                            null as type, 
                                            null as type_seq,
                                            null as delivery_date,


                                            sum(case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                            sum(case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                            sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                            0 as fc_debit , 
                                            0 as fc_credit,
                                            0 as fc_balance

                                            FROM account_payment h
                                            inner JOIN res_partner p ON h.partner_id = p.id
                                             inner join (select distinct ac.id, ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                             on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end

                                            where h.state='draft'

                                         """

                    if l_display_type == 'summary':
                        if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                            query_summary_init += " and l.date < '{}' ".format(date_start, date_start)
                            query_payment_summary_init += " and h.payment_date < '{}' ".format(date_start, date_start)

                            query_summary_move += " and l.date between '{}' and '{}' ".format(date_start,date_end, date_start)
                            query_payment_summary_move += " and h.payment_date between '{}' and '{}' ".format(date_start, date_end,date_start)

                        else:
                            query_summary += " and l.date <='{}' ".format(date_end, date_end)
                            query_payment_summary += " and h.payment_date <='{}' ".format(date_end, date_end)

                    else:
                        query_summary += " and l.date < '{}' ".format(date_start, date_start)
                        query_payment_summary += " and h.payment_date < '{}' ".format(date_start, date_start)

                    if l_currency_id:
                        l_currency_id1 = l_currency_id[0]
                        if l_currency_id1 == self.env.company.currency_id.id:
                            if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                                query_summary_init += " and l.currency_id is null "
                                query_payment_summary_init += " and l.currency_id is null "

                                query_summary_move += " and l.currency_id is null "
                                query_payment_summary_move += " and l.currency_id is null "
                            else:
                                query_summary += " and l.currency_id is null "
                                query_payment_summary += " and h.currency_id is null "

                        else:
                            if l_summary_options == 'detail_balances' and l_display_type == 'summary':

                                query_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary_init += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary_move += " and l.currency_id = '{}' ".format(l_currency_id1)

                            else:

                                query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_summary += " and h.currency_id = '{}' ".format(l_currency_id1)

                    if l_display_type == 'detail':
                        query_detail = """
                                                          select l.partner_id,
                                                          p.name as partner_name,
                                                           l.analytic_account_id,
                                                          l.company_id,
                                                          ac.code as code,
                                                          ac.name as account_name, 
                                                          l.date as doc_date,
                                                        case when l.ref is not null and l.name is not null then l.name || ' - ' || l.ref

                                                                when l.ref isnull and l.name is not null then l.name 
                                                                when l.ref is not null and l.name isnull then l.ref
                                                                when l.ref <>'' and l.payment_id is not null then l.ref || '( رقم السند : '|| pm.name ||')' 
                                                                when   h.type = 'out_invoice' then 'فاتورة مبيعات رقم  '|| h.name 
                        
                                                                when  h.type = 'out_refund' then 'مردود مبيعات رقم ' || h.name
                                                                when   h.type = 'in_invoice' then 'فاتورة مشتريات رقم '  || h.name
                                                                when    h.type = 'in_refund' then 'مردود مشتريات رقم ' || h.name
                                                                when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية رقم ' || h.name
                                                                when   l.payment_id is not null and pm.payment_type ='inbound' then ' رقم سند القبض ( ' || pm.name || ')' 
                                                                when    l.payment_id is not null and pm.payment_type ='outbound' then 'رقم سند الصرف (' || pm.name || ')'
																 end as ref,
                                                            h.name as automatic_seq ,
                                                            h.partner_branch_id ,

                                                            case when h.type = 'out_invoice' then 'فاتورة مبيعات' 
                                                                when  h.type = 'out_refund' then 'مردود مبيعات' 
                                                                when h.type = 'in_invoice' then 'فاتورة مشتريات' 
                                                                when  h.type = 'in_refund' then 'مردود مشتريات' 
                                                                when  h.type = 'entry' and l.payment_id isnull then 'قيد يومية' 
                                                                when  l.payment_id is not null and pm.payment_type ='inbound' then 'قيد يومية( ' || l.name || ')'
                                                                when  l.payment_id is not null and pm.payment_type ='outbound' then 'قيد يومية( ' || l.name || ')'
                                                                                                    end as type,
                                                          
                                                           case when h.type = 'in_invoice' then 1 
                                                            when  h.type = 'in_refund' then 1
                                                            when  h.type = 'entry' and l.payment_id isnull then 3
                                                            when  l.payment_id is not null   then 2
                                                                                                 end as type_seq,					
                                                            h.l10n_sa_delivery_date as delivery_date,
                                                            l.debit , 
                                                            l.credit , 
                                                            l.balance,
                                                            case when l.amount_currency > 0 then l.amount_currency else 0 end as fc_debit , 
                                                            case when l.amount_currency < 0 then l.amount_currency *-1 else 0 end as fc_credit,
                                                            l.amount_currency as fc_balance
                                                          FROM account_move_line l
                                                           LEFT JOIN account_account ac ON l.account_id = ac.id 
                                                           LEFT JOIN res_partner p ON l.partner_id = p.id 
                                                               left join account_payment pm on pm.id = l.payment_id
    
                                                           JOIN account_move h ON l.move_id = h.id
                                                           where l.account_id=ac.id
                                                           and l.partner_id is not null
    
                                                           and l.date between '{}' and '{}' 
                                                          """.format(date_start, date_end)
                        query_payment_detail = """
                                                  select 
                                                        h.partner_id ,
                                                        p.name as partner_name,
                                                        null as analytic_account_id,
                                                        COALESCE(p.company_id, 1::numeric) as company_id,
                                                        ac.code,
                                                        (select a.name from account_account a where a.id=ac.id) as account_name,
                                                         h.payment_date as doc_date,
                                                        h.communication  as "ref",
                                                        
                                                        h.name as automatic_seq ,
                                                        h.partner_branch_id ,

                                                        case when payment_type='inbound' then 'سند قبض' else 'سند صرف' end as type,	
                                                        2 as type_seq,				
                                                         h.payment_date as delivery_date,
                                                        (case when payment_type = 'outbound' then h.amount else 0 end) as debit , 
                                                        (case when payment_type = 'inbound' then h.amount else 0 end) as credit , 
                                                        (case when payment_type = 'outbound' then h.amount else h.amount * -1 end) balance,
                                                        0 as fc_debit , 
                                                        0 as fc_credit,
                                                        0 as fc_balance
                                                        
                                                        FROM account_payment h
                                                        inner JOIN res_partner p ON h.partner_id = p.id
                                                         inner join (select distinct ac.id,ac.code,l.partner_id,ac.internal_type from account_move_line l, account_account ac where ac.id=l.account_id  and ac.internal_type in ('receivable','payable' )) ac 
                                                        on ac.partner_id= h.partner_id and case when h.partner_type ='customer' then ac.internal_type = 'receivable' else  ac.internal_type = 'payable'end
    
                                                        where h.state='draft'
    
                                                       and h.payment_date between '{}' and '{}' 
                                                      """.format(date_start, date_end)

                        if l_currency_id:
                            l_currency_id1 = l_currency_id[0]
                            if l_currency_id1 == self.env.company.currency_id.id:
                                query_detail += " and l.currency_id is null "
                                query_payment_detail += " and h.currency_id is null "

                            else:
                                query_summary += " and l.currency_id = '{}' ".format(l_currency_id1)
                                query_payment_detail += " and h.currency_id = '{}' ".format(l_currency_id1)

        sql_parameters = ''
        sql_payment_parameters = ''

        if move_list:
            select = []
            for m in move_list:
                select.append(m.id)
                select.append(m.reversed_entry_id.id)
            

            if len(select) > 1:
                sql_parameters += " and h.id not in %s " % (tuple(select),)
            else:
                if len(select) == 1:
                    move_list = move_list.ids[0]
                    sql_parameters += " and h.id != %s " % (move_list)
          
 

        if l_company_ids1:
            if len(l_company_ids1) > 1:
                sql_parameters += " and h.company_id in %s " % (tuple(l_company_ids1),)
            else:
                if len(l_company_ids1) == 1:
                    l_company_id = l_company_ids1[0]
                    sql_parameters += " and h.company_id = %s " % (l_company_id)
        else:
            self.env.cr.execute("select cid from res_company_users_rel b where user_id=%s" % self.env.uid)
            rec = self.env.cr.fetchone()
            if not rec:
                raise ValidationError("المستخدم الحالي يجب ان يرتبط بشركة")
        if l_doc_state:
            sql_parameters += " and h.state =  '%s' " % (l_doc_state)
            sql_payment_parameters += " and h.state =  '%s' " % (l_doc_state)
        else:
            sql_parameters += " and h.state !=  'cancel' "
            sql_payment_parameters += " and h.state not in ('cancel','sent','reconciled') "


        if l_branch_id:
            if len(l_branch_id) > 1:
                sql_parameters += " and h.branch_id in %s " % (tuple(l_branch_id),)
                sql_payment_parameters += " and h.branch_id in %s " % (tuple(l_branch_id),)

            else:
                if len(l_branch_id) == 1:
                    l_branch_id1 = l_branch_id[0]
                    sql_parameters += " and h.branch_id = %s " % (l_branch_id1)
                    sql_payment_parameters += " and h.branch_id = %s " % (l_branch_id1)

        else:
            self.env.cr.execute(
                "select count(custom_branches_id) as branch from custom_branches_res_users_rel b where res_users_id=%s" % self.env.uid)
            rec = self.env.cr.fetchone()
            if not rec:
                raise ValidationError("المستخدم الحالي يجب ان يرتبط بفرع")
        
        
        if l_partner_branch_id:
            if len(l_partner_branch_id) > 1:

                sql_parameters += " and h.partner_branch_id in %s " % (tuple(l_partner_branch_id),)
                sql_payment_parameters += " and h.partner_branch_id in %s " % (tuple(l_partner_branch_id),)

            else:
                if len(l_partner_branch_id) == 1:
                    partner_branch_id1 = l_partner_branch_id[0]
                    sql_parameters += " and h.partner_branch_id = %s " % (partner_branch_id1)
                    sql_payment_parameters += " and h.partner_branch_id = %s " % (partner_branch_id1)
    
        
        if l_partner_id:
            sql_parameters += " and l.partner_id=%s " % (l_partner_id)
            sql_payment_parameters += " and h.partner_id=%s " % (l_partner_id)

        else:
         
            if l_sales_man_id:
               
                partners = self.get_partners(l_filter_customers,l_filter_suppliers,l_sales_man_id[0])
              
            else:
                partners = self.get_partners(l_filter_customers, l_filter_suppliers, False)
             
            if len(partners) > 1:
                sql_parameters += " and l.partner_id in %s " % (tuple(partners.ids),)
                sql_payment_parameters += " and h.partner_id in %s " % (tuple(partners.ids),)
            else:
                partner_id = partners.id
                

                sql_parameters += " and l.partner_id = %s " % partner_id
                sql_payment_parameters += " and h.partner_id = %s " % partner_id


        select1 = []
        select2 = []
        partner_rec_acc_ids = []
        partner_pay_acc_ids = []
        if l_partner_id:
            if l_only_customers:
                partner = self.env['res.partner'].search(
                    ['|', ('partner_type', '=', 'customer'), ('partner_type', '=', False),('id','=',l_partner_id)])
                select1 = []
                # for rec in partner:
                select1 = partner.property_account_receivable_id.ids
                partner_rec_acc_ids = partner.property_account_receivable_id.ids
                

                account_move_rec = self.env['account.move.line'].search([('account_internal_type', 'in', ['receivable']),('partner_id','=',l_partner_id)])
                for m in account_move_rec.account_id.ids:
                    select1.append(m)

              

            if l_only_suppliers:
                partner = self.env['res.partner'].search(
                    ['|', ('partner_type', '=', 'vendor'), ('partner_type', '=', False),('id','=',l_partner_id)])
                select2 = []
                for rec in partner:
                    select2.append(rec.property_account_payable_id.id)
                    partner_pay_acc_ids.append(rec.property_account_payable_id.id)

                account_move_pay = self.env['account.move.line'].search([('account_internal_type', 'in', ['payable']),('partner_id','=',l_partner_id)])
                for m in account_move_pay.account_id:
                    select2.append(m.id)

            account_codes = ''
            payment_account_ids =''
            payment_account_codes =[]

            if l_only_customers and l_only_suppliers:
                account_codes = self.env['account.move.line'].search(
                    ['|', ('account_id', 'in', select1), ('account_id', 'in', select2)]).account_id.ids

                payment_account_ids = self.env['account.account'].search(
                    ['|', ('id', 'in', partner_rec_acc_ids), ('id', 'in', partner_pay_acc_ids)]).ids

            else:
                if l_only_customers:
                    account_codes = self.env['account.move.line'].search([('account_id', 'in', select1)]).account_id.ids
                    payment_account_ids = self.env['account.account'].search(
                        [('id', 'in', partner_rec_acc_ids)]).ids

                else:
                    if l_only_suppliers:
                        account_codes = self.env['account.move.line'].search([('account_id', 'in', select2)]).account_id.ids
                        payment_account_ids = self.env['account.account'].search(
                            [('id', 'in', partner_pay_acc_ids)]).ids

            if payment_account_ids:
                payment_account_codes = self.get_account_code(payment_account_ids, l_company_ids1)
           

            if l_analytic_account_ids1:
                if len(l_analytic_account_ids1) > 1:
                    sql_parameters += " and l.analytic_account_id in %s " % (tuple(l_analytic_account_ids1),)
                else:
                    if len(l_analytic_account_ids1) == 1:
                        l_anal_account_id = l_analytic_account_ids1[0]
                        sql_parameters += " and l.analytic_account_id = %s " % (l_anal_account_id)

            if account_codes:
                account_ids = []
                company_ids = []
                # for rec1 in account_codes:
                #     account_ids.append(rec1.account_id)

                l_account_code = self.get_account_code(account_codes, l_company_ids1)

        elif not l_partner_id:
            if l_only_customers:

                partner = self.env['res.partner'].search(
                    ['|', ('partner_type', '=', 'customer'), ('partner_type', '=', False)])
                select1 = []
                # for rec in partner:
                select1 = partner.property_account_receivable_id.ids
                partner_rec_acc_ids = partner.property_account_receivable_id.ids
            

                account_move_rec = self.env['account.move.line'].search(
                    [('account_internal_type', 'in', ['receivable'])])
                for m in account_move_rec.account_id.ids:
                    select1.append(m)

               

            if l_only_suppliers:
                partner = self.env['res.partner'].search(
                    ['|', ('partner_type', '=', 'vendor'), ('partner_type', '=', False)])
                select2 = []
                for rec in partner:
                    select2.append(rec.property_account_payable_id.id)
                    partner_pay_acc_ids.append(rec.property_account_payable_id.id)

                account_move_pay = self.env['account.move.line'].search([('account_internal_type', 'in', ['payable'])])
                for m in account_move_pay.account_id:
                    select2.append(m.id)

            account_codes = ''
            payment_account_ids = ''
            payment_account_codes = []

            if l_only_customers and l_only_suppliers:
                account_codes = self.env['account.move.line'].search(
                    ['|', ('account_id', 'in', select1), ('account_id', 'in', select2)]).account_id.ids

                payment_account_ids = self.env['account.account'].search(
                    ['|', ('id', 'in', partner_rec_acc_ids), ('id', 'in', partner_pay_acc_ids)]).ids

            else:
                if l_only_customers:
                    account_codes = self.env['account.move.line'].search([('account_id', 'in', select1)]).account_id.ids
                    payment_account_ids = self.env['account.account'].search(
                        [('id', 'in', partner_rec_acc_ids)]).ids

                else:
                    if l_only_suppliers:
                        account_codes = self.env['account.move.line'].search([('account_id', 'in', select2)]).account_id.ids
                        payment_account_ids = self.env['account.account'].search(
                            [('id', 'in', partner_pay_acc_ids)]).ids

            if payment_account_ids:
                payment_account_codes = self.get_account_code(payment_account_ids, l_company_ids1)
               

            if l_analytic_account_ids1:
                if len(l_analytic_account_ids1) > 1:
                    sql_parameters += " and l.analytic_account_id in %s " % (tuple(l_analytic_account_ids1),)
                else:
                    if len(l_analytic_account_ids1) == 1:
                        l_anal_account_id = l_analytic_account_ids1[0]
                        sql_parameters += " and l.analytic_account_id = %s " % (l_anal_account_id)

            if account_codes:
                account_ids = []
                company_ids = []
                # for rec1 in account_codes:
                #     account_ids.append(rec1.account_id)

                l_account_code = self.get_account_code(account_codes, l_company_ids1)

        
        if len(l_account_code) > 1:
            sql_parameters += " and ac.code in %s " % (tuple(l_account_code),)

        else:
            if len(l_account_code) == 1:
                account_id = l_account_code[0]
                sql_parameters += " and ac.code = '%s' " % (account_id)


            else:
                raise ValidationError("يجب اختيار حساب ")

        if len(payment_account_codes) > 1:
             sql_payment_parameters += " and ac.code in %s " % (tuple(payment_account_codes),)

        else:
            if len(payment_account_codes) == 1:
                pay_account_id = payment_account_codes[0]
                sql_payment_parameters += " and ac.code = '%s' " % (pay_account_id)


            else:
                raise ValidationError("يجب اختيار حساب ")

        sql_qroup_by = ''
        sql_payment_qroup_by = ''
        sql_order_by = ''
        sql_payment_order_by = ''

        if l_report_type == 'account':
            sql_qroup_by += " group by p.name , code, account_name, l.partner_id , l.company_id "
            sql_payment_qroup_by += " group by p.name , code, account_name, h.partner_id , company_id "

        else:
            if l_report_type == 'partner':
                sql_qroup_by += "  group by p.name, l.partner_id, l.company_id "
                sql_payment_qroup_by += "  group by p.name, h.partner_id, company_id "

        # if l_display_type == 'detail':
        #     if l_sort_type == 'date':
        #         sql_qroup_by += " , l.date, h.name  "
        #     elif l_sort_type == 'doc_no':
        #         sql_qroup_by += " , h.name "

        if l_hide_zero_balance and  l_summary_options == 'final_balances':
            sql_order_by += " having sum(debit - credit) <> 0  "
            sql_payment_order_by += " having sum(case when payment_type = 'outbound' then h.amount else h.amount * -1 end) <> 0  "

        if l_display_type == 'summary' and  l_summary_options == 'final_balances':
            if not l_show_payments_before_posted:
                if l_sort_type == 'balance':
                        
                    sql_order_by += "  order by sum(debit - credit) desc"

                else:
                        
                    sql_order_by += "  order by p.name "

        if l_show_payments_before_posted:
            if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                query_summary_init += sql_parameters
                query_summary_init += sql_qroup_by
                query_summary_move += sql_parameters
                query_summary_move += sql_qroup_by
                # query_summary += sql_order_by

                query_payment_summary_init += sql_payment_parameters
                query_payment_summary_init += sql_payment_qroup_by
                query_payment_summary_move += sql_payment_parameters
                query_payment_summary_move += sql_payment_qroup_by
                # query_payment_summary += sql_payment_order_by
                query_summary = 'select  partner_id, partner_name,analytic_account_id,company_id , code,   account_name,  doc_date,  ref, automatic_seq , partner_branch_id , type,  delivery_date, ' \
                                ' sum(op_debit) as  op_debit, ' \
                                ' sum(op_credit) as  op_credit, ' \
                                ' sum(op_balance) as  op_balance, ' \
                                ' sum(op_fc_debit) as op_fc_debit , ' \
                                ' sum(op_fc_credit) as op_fc_credit , ' \
                                 'sum(op_fc_balance) as op_fc_balance ,' \
                                ' sum(move_debit) as  move_debit, ' \
                                ' sum(move_credit) as  move_credit, ' \
                                ' sum(move_balance) as  move_balance, ' \
                                ' sum(move_fc_debit) as move_fc_debit , ' \
                                ' sum(move_fc_credit) as move_fc_credit , ' \
                                'sum(move_fc_balance) as move_fc_balance from (' + query_summary_init + ' union all ' + query_summary_move + ' union all ' + query_payment_summary_init + ' union all ' + query_payment_summary_move + ') xx  group by partner_id, partner_name,analytic_account_id,company_id' \
                                                                                                                                                               ', code, account_name, doc_date, ref, automatic_seq , partner_branch_id, type, delivery_date  '
                if l_hide_zero_balance:
                    sql_order_by +=  " having (sum(move_balance) + sum(op_balance)) <> 0  "
                    
                if l_sort_type == 'balance':
                    sql_order_by += "  order by (sum(op_balance)+ sum(move_balance)) desc"
                else:
                    sql_order_by += "  order by partner_name"
                    
                query_summary += sql_order_by
              
            else:
                query_summary += sql_parameters
                query_summary += sql_qroup_by
                # query_summary += sql_order_by

                query_payment_summary += sql_payment_parameters
                query_payment_summary += sql_payment_qroup_by
                # query_payment_summary += sql_payment_order_by
                query_summary = 'select  partner_id, partner_name,analytic_account_id,company_id , code,   account_name,  doc_date,  ref, automatic_seq ,partner_branch_id ,  type,  delivery_date, ' \
                                ' ( case when sum(debit) - sum(credit) > 0 then sum(debit) - sum(credit) else 0 end) as  debit, ' \
                                '( case when sum(debit) - sum(credit) < 0 then abs(sum(debit) - sum(credit)) else 0 end) as  credit, ' \
                                ' sum (balance) as balance,sum(fc_debit) as fc_debit , ' \
                                'sum(fc_credit) as fc_credit ,sum (fc_balance) as fc_balance from (' + query_summary + ' union all ' + query_payment_summary + ') xx  group by partner_id, partner_name,analytic_account_id,company_id' \
                                    ', code, account_name, doc_date, ref, automatic_seq , partner_branch_id , type, delivery_date  '
               
               
        else:
            if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                query_summary_init += sql_parameters
                query_summary_init += sql_qroup_by
                query_summary_move += sql_parameters
                query_summary_move += sql_qroup_by
                query_summary = 'select  partner_id, partner_name,analytic_account_id,company_id , code,   account_name,  doc_date,  ref, automatic_seq , partner_branch_id , type,  delivery_date, ' \
                                ' sum(op_debit) as  op_debit, ' \
                                ' sum(op_credit) as  op_credit, ' \
                                ' sum(op_balance) as  op_balance, ' \
                                ' sum(op_fc_debit) as op_fc_debit , ' \
                                ' sum(op_fc_credit) as op_fc_credit , ' \
                                'sum(op_fc_balance) as op_fc_balance ,' \
                                ' sum(move_debit) as  move_debit, ' \
                                ' sum(move_credit) as  move_credit, ' \
                                ' sum(move_balance) as  move_balance, ' \
                                ' sum(move_fc_debit) as move_fc_debit , ' \
                                ' sum(move_fc_credit) as move_fc_credit , ' \
                                'sum(move_fc_balance) as move_fc_balance from (' + query_summary_init + ' union all ' + query_summary_move  + ') xx  group by partner_id, partner_name,analytic_account_id,company_id' \
                                   ', code, account_name, doc_date, ref, automatic_seq , partner_branch_id , type, delivery_date '

                if l_hide_zero_balance:
                    sql_order_by +=  " having (sum(move_balance) + sum(op_balance)) <> 0  "
                    
                if l_sort_type == 'balance':
                    sql_order_by += "  order by (sum(op_balance)+ sum(move_balance)) desc"
                else:
                    sql_order_by += "  order by partner_name"
                query_summary += sql_order_by
              
            else:
               query_summary += sql_parameters
               query_summary += sql_qroup_by
               query_summary += sql_order_by
             

        self.env.cr.execute(query_summary)

        res_summary = self.env.cr.dictfetchall()
   
        move_lines = {}
        if l_report_type == 'account':
            move_lines = {x: [] for x in l_account_code}
        else:
            move_lines = {x: [] for x in l_company_ids1}

        if res_summary:
            if l_report_type == 'account':
                for row in res_summary:
                    move_lines[row.pop('code')].append(row)
            else:
                for row in res_summary:
                    move_lines[row.pop('company_id')].append(row)

     

        if l_display_type == 'detail':
            if l_show_payments_before_posted:
                query_detail += sql_parameters
                # if l_sort_type == 'date':
                #     query_detail += " order by l.date, h.name"
                # elif l_sort_type == 'doc_no':
                #     query_detail += " order by h.name"

                query_payment_detail += sql_payment_parameters

                if l_sort_type == 'date':
                    if check_swailm_fields:
                        query_detail = 'select * from ( ' + query_detail + ' union all  ' + query_payment_detail + ') xx order by doc_date, haraj_num,type_seq,automatic_seq,partner_branch_id '
                    else:
                        query_detail = 'select * from ( ' + query_detail + ' union all  ' + query_payment_detail + ') xx order by doc_date, automatic_seq,partner_branch_id '


                elif l_sort_type == 'doc_no':
                    if check_swailm_fields:
                        query_detail = 'select * from ( ' + query_detail + ' union all  ' + query_payment_detail + ') xx  order by  haraj_num,type_seq,automatic_seq,partner_branch_id '
                    else:
                        query_detail = 'select * from ( ' + query_detail + ' union all  ' + query_payment_detail + ') xx  order by automatic_seq,partner_branch_id  '



         
            else:
                query_detail += sql_parameters
                if l_sort_type == 'date':
                    query_detail += " order by l.date, h.name"
                elif l_sort_type == 'doc_no':
                    query_detail += " order by h.name"

              

            self.env.cr.execute(query_detail)

            res_detail = self.env.cr.dictfetchall()
            
            if res_detail:
                if l_report_type == 'account':
                    # move_lines = {x: [] for x in l_account_code}
                    for row in res_detail:
                        move_lines[row.pop('code')].append(row)
                else:
                    # move_lines = {x: [] for x in l_company_ids1}
                    for row in res_detail:
                        move_lines[row.pop('company_id')].append(row)



        if move_lines:
            
            partner = []

            # # get partner balance customer -supplier =============================================
            # if len(l_account_code) > 1:
            #     sql_query3 = """
            #     select l.partner_id ,p.name as partner_name,sum (debit) as debit , sum (credit) as credit, sum (debit - credit) as balance
            #
            #          FROM account_move_line l
            #              LEFT JOIN res_partner p ON l.partner_id = p.id
            #              JOIN account_move h ON l.move_id = h.id
            #              and l.partner_id is not null
            #              and l.partner_id in (select l.partner_id
            #                                      FROM account_move_line l
            #                                          JOIN account_move h ON l.move_id = h.id
            #                                          and l.partner_id is not null
            #
            #                                         and h.state='posted'
            #                                          and l.date <='{}'
            #                                    {}
            #                                    and l.account_id in {})
            #              and  (l.account_id in {} or l.account_id in {})
            #              and h.state='posted'
            #              and l.date <='{}'
            #
            #       """.format(date_end,sql_parameters,tuple(select1),tuple(select2), date_end)
            #     sql_query3 += sql_parameters
            #     sql_query3 += "  group by l.partner_id ,p.name order by p.name"
            #     self.env.cr.execute(sql_query3)
            #     partner_bal = self.env.cr.dictfetchall()
            #     if partner_bal:
            #         marge_cust_vendor = []
            #
            #         for rec2 in partner_bal:
            #             marge_cust_vendor.append(rec2)
            #         print(marge_cust_vendor)
            # # ====================================================================================
            account_res = []
            sql_query2 = """select distinct code,'[ '|| code || ' ] '|| name || ' ( ' ||string_agg((select name from res_company where id=company_id), ' , ')|| ' )' as name from account_account"""
            if len(l_account_code) > 1:
                sql_query2 += "  where code in %s " % (tuple(l_account_code),)
            else:
                sql_query2 += "  where code = '%s' " % (l_account_code[0])

            if len(l_company_ids1) > 1:
                sql_query2 += "  and company_id in %s " % (tuple(l_company_ids1),)
            else:
                sql_query2 += "  and company_id = %s " % (l_company_ids1[0])

            sql_query2 += "  group by code , name order by code"
            self.env.cr.execute(sql_query2)
            account_ids = self.env.cr.dictfetchall()
           
            l_companys = self.env['res.company'].search([('id', 'in', l_company_ids1)])
            l_partners = self.env['res.partner'].search([('id', '=', l_partner_id)])
            l_currencies = self.env['res.currency'].search([('id', '=', l_currency_id)])
            
            l_partner_branchs = ''
            if l_partner_branch_id:
                # l_partner_branch_id = l_partners.partner_branches.ids
            
                l_partner_branchs = self.env['res.partner.branches'].search([('id','in',l_partner_branch_id)])

            l_branchs = self.env['custom.branches'].search([('id', 'in', l_branch_id)])
            l_analytic_accounts = self.env['account.analytic.account'].search([('id', 'in', l_analytic_account_ids1)])


            if l_report_type == 'account':
                for account in account_ids:
                    if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                        res = dict((fn, 0.0) for fn in ['op_credit', 'op_debit', 'op_cum_balance', 'op_cum_fc_balance',
                                                        'move_credit', 'move_debit', 'move_cum_balance', 'move_cum_fc_balance'])
                        res['code'] = account['code']
                        res['name'] = account['name']
                        res['move_lines'] = move_lines[account['code']]
                        for line in res.get('move_lines'):
                            res['op_debit'] += line['op_debit']
                            res['op_credit'] += line['op_credit']
                            res['op_cum_balance'] += line['op_balance']
                            res['move_debit'] += line['move_debit']
                            res['move_credit'] += line['move_credit']
                            res['move_cum_balance'] += line['move_balance']
                            # if l_currency_id:
                            #     res['cum_fc_balance'] += line['fc_balance']

                        account_res.append(res)
                    else:
                        res = dict((fn, 0.0) for fn in ['credit', 'debit','op_debit','op_credit', 'cum_balance','cum_fc_balance'])
                        res['code'] = account['code']
                        res['name'] = account['name']
                        res['move_lines'] = move_lines[account['code']]
                        for line in res.get('move_lines'):
                            if l_move_total_without_op:
                                if line['type']:
                                    res['debit'] += line['debit']
                                    res['credit'] += line['credit']
                                if not line['type']:
                                    res['op_debit'] += line['debit']
                                    res['op_credit'] += line['credit']

                                res['cum_balance'] += line['balance']

                            else:
                                res['debit'] += line['debit']
                                res['credit'] += line['credit']
                                res['cum_balance'] += line['balance']
                                # if l_currency_id:
                                #     res['cum_fc_balance'] += line['fc_balance']

                        account_res.append(res)
            else:
                for comp in l_companys:
                    if l_summary_options == 'detail_balances' and l_display_type == 'summary':
                        res = dict((fn, 0.0) for fn in ['op_credit', 'op_debit', 'op_cum_balance', 'op_cum_fc_balance',
                                                        'move_credit', 'move_debit', 'move_cum_balance',
                                                        'move_cum_fc_balance'])
                        res['name'] = 'الاجمالي'
                        res['move_lines'] = move_lines[comp['id']]
                        for line in res.get('move_lines'):
                            res['op_debit'] += line['op_debit']
                            res['op_credit'] += line['op_credit']
                            res['op_cum_balance'] += line['op_balance']
                            res['move_debit'] += line['move_debit']
                            res['move_credit'] += line['move_credit']
                            res['move_cum_balance'] += line['move_balance']
                            # if l_currency_id:
                            #     res['cum_fc_balance'] += line['fc_balance']

                        account_res.append(res)

                    else:
                        res = dict((fn, 0.0) for fn in ['credit', 'debit', 'cum_balance','cum_fc_balance','fc_debit','fc_credit','op_debit','op_credit'])
                        res['name'] = 'الاجمالي'
                        res['move_lines'] = move_lines[comp['id']]
                        for line in res.get('move_lines'):
                            if l_move_total_without_op:
                                if line['type']:
                                    res['debit'] += line['debit']
                                    res['credit'] += line['credit']
                                    res['fc_debit'] += line['fc_debit']
                                    res['fc_credit'] += line['fc_credit']

                                if not line['type']:
                                    res['op_debit'] += line['debit']
                                    res['op_credit'] += line['credit']

                                res['cum_balance'] += line['balance']

                            else:
                                res['debit'] += line['debit']
                                res['credit'] += line['credit']
                                res['fc_debit'] += line['fc_debit']
                                res['fc_credit'] += line['fc_credit']

                                res['cum_balance'] += line['balance']
                                # if l_currency_id:
                                #     res['cum_fc_balance'] += line['fc_balance']



                            # res['cum_fc_balance'] += line['fc_balance']

                        account_res.append(res)

            # print (res[1])
            docs = []

            return {
                'doc_ids': data['ids'],
                'doc_model': data['model'],
                'date_start': date_start,
                'date_end': date_end,
                'accounts_list': account_ids,
                'use_custom_seq': l_enable_custom_seq,
                'companys': l_companys,
                'branchs': l_branchs,
                'analytic_accounts': l_analytic_accounts,
                'display_type': l_display_type,
                'partner' : l_partners,
                'filter_suppliers': l_filter_suppliers,
                'filter_customers': l_filter_customers,
                'currency': l_currencies,
                'check_swailm_fields': check_swailm_fields,
                'report_type': l_report_type,
                'summary_options': l_summary_options,
                'move_total_without_op': l_move_total_without_op,
                'partner_branchs': l_partner_branchs,
                'report_setup': l_report_setup,

                'docs': account_res,
            }
        else:
            raise ValidationError(
                "لا توجد بيانات")


class report_lines(models.TransientModel):
    _name = 'partner.report.lines'


    attr_code = fields.Char(string="كود الخاصية")
    attr_name = fields.Char(string="اسم الخاصية")
    att_value =  fields.Char(string="النتيجة")

    header_id = fields.Many2one('partner.summary.report')




