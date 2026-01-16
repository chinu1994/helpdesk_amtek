# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'  # Adjust based on your model name

    @api.model
    def create(self, vals):
        """Override create to set new stage and send notification"""
        # Get the "New" stage (first stage in sequence or by name)
        new_stage = self.env['helpdesk.stage'].search([
            ('name', '=', 'New')
        ], limit=1)

        # If "New" stage not found, try to get the first stage by sequence
        if not new_stage:
            new_stage = self.env['helpdesk.stage'].search([], order='sequence asc', limit=1)

        # Set the stage to "New" if not already set
        if new_stage and 'stage_id' not in vals:
            vals['stage_id'] = new_stage.id

        ticket = super(HelpdeskTicket, self).create(vals)

        # Send email notification for the initial stage
        if ticket.stage_id and ticket.stage_id.notify_emails:
            ticket._send_stage_change_email(None, ticket.stage_id)

        return ticket

    def write(self, vals):
        """Override write to detect stage changes"""
        # Check if stage is being changed
        if 'stage_id' in vals:
            for ticket in self:
                old_stage = ticket.stage_id
                result = super(HelpdeskTicket, ticket).write(vals)
                new_stage = ticket.stage_id

                # Send email notification if stage changed and notify emails exist
                if old_stage != new_stage and new_stage.notify_emails:
                    ticket._send_stage_change_email(old_stage, new_stage)

                return result

        return super(HelpdeskTicket, self).write(vals)

    def _send_stage_change_email(self, old_stage, new_stage):
        """Send simple stage-wise email notification in English"""
        self.ensure_one()

        notify_emails = new_stage.notify_emails
        if not notify_emails:
            return

        email_list = [e.strip() for e in notify_emails.split(',') if e.strip()]
        if not email_list:
            return

        mail_server = self.env['ir.mail_server'].search([], limit=1)
        if not mail_server:
            raise UserError('No outgoing mail server configured.')

        email_from = mail_server.smtp_user or self.env.user.email or 'noreply@example.com'

        stage_name = (new_stage.name or '').lower()
        ticket_no = self.ticket_ref
        description = self.description or 'N/A'
        assigned_to = self.user_id.name if self.user_id else 'Not Assigned'

        # -------------------------
        # SUBJECT & BODY (STAGE WISE)
        # -------------------------

        if stage_name == 'new':
            subject = f'Ticket Created - {ticket_no}'
            body = f"""
            <p>A new helpdesk ticket has been created.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            <p><b>Description:</b> {description}</p>
            <p>The ticket will be resolved within 24 hours.</p>
            """

        elif stage_name == 'in progress':
            subject = f'Ticket In Progress - {ticket_no}'
            body = f"""
            <p>The ticket is now <b>In Progress</b>.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            <p><b>Assigned To:</b> {assigned_to}</p>
            <p><b>Description:</b> {description}</p>
            """

        elif stage_name == 'on hold':
            subject = f'Ticket On Hold - {ticket_no}'
            body = f"""
            <p>The ticket is currently <b>On Hold</b>.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            <p><b>Description:</b> {description}</p>
            """

        elif stage_name == 'doubt':
            subject = f'Ticket Requires Clarification - {ticket_no}'
            body = f"""
            <p>The ticket has a <b>Query / Doubt</b>.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            <p><b>Description:</b> {description}</p>
            """

        elif stage_name in ['solved', 'resolved']:
            subject = f'Ticket Resolved - {ticket_no}'
            body = f"""
            <p>🎉 The ticket has been <b>Resolved</b>.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            """

        elif stage_name == 'cancel':
            subject = f'Ticket Cancelled - {ticket_no}'
            body = f"""
            <p>❌ The ticket has been <b>Cancelled</b>.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            """

        else:
            subject = f'Ticket Update - {ticket_no}'
            body = f"""
            <p>The ticket status has been updated.</p>
            <p><b>Ticket No:</b> {ticket_no}</p>
            <p><b>Current Stage:</b> {new_stage.name}</p>
            """

        # -------------------------
        # FINAL HTML
        # -------------------------
        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            {body}
            <br/>
            <p>Please check the helpdesk system for further details.</p>
          </body>
        </html>
        """

        # -------------------------
        # SEND MAIL
        # -------------------------
        for email in email_list:
            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': body_html,
                'email_from': email_from,
                'email_to': email,
                'mail_server_id': mail_server.id,
            }).send()
