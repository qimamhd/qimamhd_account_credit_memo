# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
 
class partner_summary_xlsx(models.TransientModel):
    _inherit = 'account.move'
   
    hide_credit_note_report = fields.Boolean(string="اخفاء من تقرير الحسابات")


    @api.constrains('hide_credit_note_report')
    def check_fully_credit_note(self):
        for rec in self:
            if rec.type == 'out_refund':
                if rec.hide_credit_note_report:
                    if round(rec.amount_total,2) != round(rec.reversed_entry_id.amount_total,2):
                           raise ValidationError("تنبيه: فاتورة المرتجع غير مطابقة للفاتورة" % exception_move)
        

