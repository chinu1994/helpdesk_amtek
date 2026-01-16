# # -*- coding: utf-8 -*-

from odoo import models, fields


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'  # Adjust based on your model name

    notify_emails = fields.Text(
        string='Notify Emails',
        help='Comma-separated email addresses to notify when a ticket reaches this stage'
    )
