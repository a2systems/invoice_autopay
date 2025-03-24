from odoo import tools, models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    def invoice_autopay(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                param = self.env['ir.config_parameter'].sudo().get_param('journal_invoice_autopay','')
                if param == '':
                    raise ValidationError('No hay parametro journal_invoice_autopay definido')
                if param:
                    journal_id = self.env['account.journal'].search([('code','=',param)])
                    if not journal_id:
                        raise ValidationError('No hay medio de pago para autopago definido')
                if rec.amount_residual:
                    vals_payment = {
                        'partner_id': rec.partner_id.id,
                        'journal_id': journal_id.id,
                        'date': str(date.today()),
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'amount': rec.amount_residual,
                        'ref': rec.display_name,
                        }
                    payment_id = self.env['account.payment'].create(vals_payment)
                    payment_id.action_post()
                    aml_obj = self.env['account.move.line']
                    for move_line in rec.line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    for move_line in payment_id.line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    aml_obj.reconcile()
        return True
