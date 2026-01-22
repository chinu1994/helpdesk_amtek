# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def _send_stage_notify_emails(self):
        for ticket in self:
            stage = ticket.stage_id
            if not stage:
                continue

            # 🔑 Use existing stage template_id
            template = stage.template_id
            if not template:
                _logger.info(
                    "No template defined on stage: %s", stage.name
                )
                continue

            if not stage.notify_emails:
                _logger.info(
                    "No notify_emails defined on stage: %s", stage.name
                )
                continue

            email_list = [
                email.strip()
                for email in stage.notify_emails.split(',')
                if email.strip()
            ]

            for email in email_list:
                template.send_mail(
                    ticket.id,
                    email_values={
                        'email_to': email,
                    },
                    force_send=True,
                    raise_exception=False
                )

    @api.model
    def create(self, vals):
        ticket = super().create(vals)
        ticket._send_stage_notify_emails()
        return ticket

    def write(self, vals):
        old_stage_map = {t.id: t.stage_id.id for t in self}
        res = super().write(vals)

        if 'stage_id' in vals:
            for ticket in self:
                if old_stage_map.get(ticket.id) != ticket.stage_id.id:
                    ticket._send_stage_notify_emails()

        return res

