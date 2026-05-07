from odoo import models, fields, api
from datetime import timedelta
import base64
from io import BytesIO
import xlsxwriter


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket")

class HelpdeskTimesheetReport(models.TransientModel):
    _name = 'helpdesk.timesheet.report'
    _description = 'Helpdesk Timesheet Report'

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)

    def action_generate_report(self):

        # clear old records
        self.env['helpdesk.timesheet.report.line'].search([]).unlink()

        # fetch timesheets
        timesheets = self.env['account.analytic.line'].search([
            ('ticket_id', '!=', False),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date)
        ])

        # create report lines
        for ts in timesheets:

            self.env['helpdesk.timesheet.report.line'].create({
                'ticket_ref': ts.ticket_id.ticket_ref or '',
                'ticket_name': ts.ticket_id.name or '',
                'stage': ts.ticket_id.stage_id.name or '',
                'employee': ts.employee_id.name or '',
                'date': ts.date,
                'description': ts.name or '',
                'time': ts.unit_amount,
            })

        # open separate tree view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Timesheet Report',
            'res_model': 'helpdesk.timesheet.report.line',
            'view_mode': 'list',
            'target': 'current',
        }


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def send_weekly_report(self):

        today = fields.Date.today()

        # Previous Monday
        start_date = today - timedelta(days=today.weekday() + 7)

        # Previous Sunday
        end_date = start_date + timedelta(days=6)

        timesheets = self.env['account.analytic.line'].search([
            ('ticket_id', '!=', False),
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        # =====================================================
        # CREATE XLSX
        # =====================================================

        output = BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Weekly Report')

        bold = workbook.add_format({'bold': True})

        headers = [
            'Ticket Ref',
            'Ticket Name',
            'Stage',
            'Employee',
            'Date',
            'Description',
            'Time'
        ]

        row = 0

        for col, header in enumerate(headers):
            sheet.write(row, col, header, bold)

        row += 1

        total_time = 0

        for ts in timesheets:
            total_time += ts.unit_amount

            sheet.write(row, 0, ts.ticket_id.ticket_ref or '')
            sheet.write(row, 1, ts.ticket_id.name or '')
            sheet.write(row, 2, ts.ticket_id.stage_id.name or '')
            sheet.write(row, 3, ts.employee_id.name or '')
            sheet.write(row, 4, str(ts.date))
            sheet.write(row, 5, ts.name or '')
            sheet.write(row, 6, ts.unit_amount)

            row += 1

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Weekly_Helpdesk_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # =====================================================
        # SEND EMAIL
        # =====================================================

        body = f'''
               <p>Hello,</p>

               <p>
                   Please find attached the weekly helpdesk report.
               </p>

               <p>
                   <b>Report Period:</b>
                   {start_date} to {end_date}
               </p>

               <p>
                   <b>Total Entries:</b>
                   {len(timesheets)}
               </p>

               <p>
                   <b>Total Hours:</b>
                   {total_time}
               </p>

               <br/>
               <p>Regards</p>
           '''

        email_to = self.env['ir.config_parameter'].sudo().get_param(
            'helpdesk_timesheet_report.email_to'
        )

        if not email_to:
            return

        mail_values = {
            'subject': f'Weekly Helpdesk Report ({start_date} to {end_date})',
            'body_html': body,
            'email_to': email_to,
            'attachment_ids': [(4, attachment.id)],
        }

        mail = self.env['mail.mail'].create(mail_values)
        mail.send()


class HelpdeskTimesheetReportLine(models.TransientModel):
    _name = 'helpdesk.timesheet.report.line'
    _description = 'Helpdesk Timesheet Report Line'

    ticket_ref = fields.Char()
    ticket_name = fields.Char()
    stage = fields.Char()

    employee = fields.Char()
    date = fields.Date()

    description = fields.Char()

    time = fields.Float()