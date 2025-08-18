# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import datetime

class journal_closed(models.Model):
    _inherit = 'account.journal'

    use_pl_close = fields.Boolean(string='دفتر اقفال الارباح والخسائر')


class pl_closed(models.TransientModel):
    _name = 'account.pl.closed'

    _rec_name = 'id'

    pl_journal_id = fields.Many2one('account.journal',required=True,string="دفتر اقفال الارباح والخسائر",domain=[('use_pl_close','=', True)],
                                    default=lambda self: self._default_pl_close()
                                    )
    pl_account_id = fields.Many2one('account.account',required=True,string="حساب الارباح والخسائر", domain=[('internal_group','not in', ['asset','income','expense'])])
    closed_year = fields.Char(string="سنة الاقفال", required=True, default=lambda self: self._default_close_year())
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True,string="الشركة")
    account_move_unposted = fields.One2many('account.pl.closed.lines','header_id', string="المستندات الغير مرحلة")

    def _default_pl_close(self):

        journal_id = self.env['account.journal'].search([('use_pl_close','=', True)],limit=1)
        return journal_id
    def _default_close_year(self):

        return str(date.today().year)
    @api.onchange('closed_year')
    def check_close_year(self):
        if len(self.closed_year) == 4:
            if not self.closed_year.isdigit():
                raise ValidationError(
                    "تنبيه ..سنة الاقفال غير صحيحة [%s]" % self.closed_year)
        else:
            raise ValidationError(
                "تنبيه ..سنة الاقفال غير صحيحة [%s] " % self.closed_year)

    def closed_pl(self):
        self.check_close_year()
        if self.pl_journal_id and self.pl_account_id and self.closed_year:

            end_date = datetime.date(int(self.closed_year),12,31)
            
            print(end_date)

            pl_accounts = self.env['account.account'].search([('internal_group','in', ['income','expense'])],order="internal_group desc, code")
            print("pl_accounts",pl_accounts)

            unposted_moves = self.env['account.move'].search([('date','<=', end_date),('state','not in',['cancel','posted']),('company_id','=', self.company_id.id)])
            if unposted_moves:
                self.account_move_unposted.unlink()
                for l in unposted_moves:
                    self.env['account.pl.closed.lines'].create({'id': l.id,
                                                                'name':l.name,
                                                                'type': l.type,
                                                                'invoice_date': l.invoice_date,
                                                                'partner_id':l.partner_id.id if l.partner_id.id else False,
                                                                'state':l.state,
                                                                'invoice_date_due':l.invoice_date_due,
                                                                'amount_total_un_tax': l.amount_untaxed_signed,
                                                                'amount_total': l.amount_total_signed,
                                                                'header_id': self.id
                                                                })



                print("account_move_unposted", self.account_move_unposted)
                print("unposted_moves", unposted_moves)
                raise ValidationError("تنبيه .. توجد مستندات تحتاج ترحيل .. يجب ترحيلها قبل الاقفال..Un posted Documents must be posted ...")


            else:


                line_ids = []
                for account_id in pl_accounts:
                    moves = self.env['account.move.line'].search([('date','<=', end_date),('account_id','=',account_id.id ),('parent_state','in',['posted']), ('company_id','=', self.company_id.id)])
                    amount = sum(l.balance for l in moves)
                    print("account:", account_id.name + str(amount))

                    if amount > 0:
                            credit_vals = (0, 0, {
                                'name': 'اقفال ارباح وخسائر ' + str(self.closed_year),
                                'amount_currency': 0.0,

                                'company_currency_id': self.company_id.currency_id.id,
                                'debit': 0.0,
                                'credit': amount,
                                # 'balance': payment.local_amount if payment.check_multi_currency else payment.payment_amount,
                                'date': end_date,
                                'date_maturity': end_date,
                                'account_id': account_id.id,
                                'account_internal_type': account_id.internal_type,
                                # 'parent_state': 'posted',
                                'ref': 'تم اقفال ارباح وخسائر سنة '+ str(self.closed_year) + ' في حساب ' + self.pl_account_id.name,
                                'journal_id': self.pl_journal_id.id,
                                'company_id': self.company_id.id,
                                'quantity': 1,

                            })
                            line_ids.append(credit_vals)

                            debit_vals = (0, 0, {
                                'name': 'اقفال ارباح وخسائر لحساب [ '+ str(account_id.code) + ' - ' + account_id.name + ']',
                                'amount_currency': 0.0,

                                'company_currency_id':self.company_id.currency_id.id,
                                'debit': amount,
                                'credit': 0.0,
                                # 'balance': -(line.l_local_amount) if payment.check_multi_currency else -(line.l_payment_amount),
                                'date': end_date,
                                'date_maturity': end_date,
                                'account_id': self.pl_account_id.id,
                                'account_internal_type': self.pl_account_id.internal_type,
                                # 'parent_state': 'posted',
                                'ref': 'اقفال ارباح وخسائر لحساب [ '+ str(account_id.code) + ' - ' + account_id.name + ']',
                                'journal_id': self.pl_journal_id.id,
                                'company_id':self.company_id.id,
                                'quantity': 1,

                            })

                            line_ids.append(debit_vals, )
                    elif amount < 0:
                            debit_vals = (0, 0, {
                                'name': 'اقفال ارباح وخسائر ' + str(self.closed_year),
                                'amount_currency': 0.0,

                                'company_currency_id': self.company_id.currency_id.id,
                                'debit': abs(amount),
                                'credit': 0.0,
                                # 'balance': payment.local_amount if payment.check_multi_currency else payment.payment_amount,
                                'date': end_date,
                                'date_maturity': end_date,
                                'account_id': account_id.id,
                                'account_internal_type': account_id.internal_type,
                                # 'parent_state': 'posted',
                                'ref': 'تم اقفال ارباح وخسائر سنة ' + str(
                                    self.closed_year) + ' في حساب ' + self.pl_account_id.name,
                                'journal_id': self.pl_journal_id.id,
                                'company_id':self.company_id.id,
                                'quantity': 1,

                            })
                            line_ids.append(debit_vals)

                            credit_vals = (0, 0, {
                                'name': 'اقفال ارباح وخسائر لحساب [ ' + str(
                                    account_id.code) + ' - ' + account_id.name + ']',
                                'amount_currency': 0.0,

                                'company_currency_id': self.company_id.currency_id.id,
                                'debit': 0.0,
                                'credit': abs(amount),
                                # 'balance': -(line.l_local_amount) if payment.check_multi_currency else -(line.l_payment_amount),
                                'date': end_date,
                                'date_maturity': end_date,
                                'account_id': self.pl_account_id.id,
                                'account_internal_type': self.pl_account_id.internal_type,
                                # 'parent_state': 'posted',
                                'ref': 'اقفال ارباح وخسائر لحساب [ ' + str(account_id.code) + ' - ' + account_id.name + ']',
                                'journal_id': self.pl_journal_id.id,
                                'company_id': self.company_id.id,
                                'quantity': 1,

                            })

                            line_ids.append(credit_vals, )
                if line_ids:
                    ref = 'اقفال ارباح وخسائر سنة ' + str(self.closed_year)
                    mov_vals = {
                        'date': end_date,
                        'ref': ref,
                        # 'state': 'posted',
                        'type': 'entry',
                        'journal_id': self.pl_journal_id.id,
                        'company_id': self.company_id.id,
                        'currency_id': self.company_id.currency_id.id,
                        # 'amount_total': payment.payment_amount, #if payment.check_multi_currency and (payment.company_id.currency_id.id != line.currency_id.id) else payment.local_amount,
                        # 'amount_total_signed': payment.local_amount, #if payment.check_multi_currency and (payment.company_id.currency_id.id != line.currency_id.id) else payment.local_amount,
                        'invoice_user_id': self.env.uid,
                        'line_ids': line_ids,
                    }

                    print(mov_vals)
                    entry_moves = self.env['account.move'].create(mov_vals)
                    print("entry_moves", entry_moves)
        return True


class pl_closed_lines(models.TransientModel):
    _name = 'account.pl.closed.lines'


    id = fields.Integer()
    name = fields.Char()
    type = fields.Char()
    invoice_date = fields.Date()
    partner_id= fields.Many2one('res.partner')
    state = fields.Char()
    invoice_date_due = fields.Date()
    amount_total_un_tax = fields.Float()
    amount_total = fields.Float()
    header_id = fields.Many2one('account.pl.closed')
