{
    'name': 'Helpdesk Timesheet Weekly Report',
    'version': '1.0',
    'depends': ['helpdesk', 'hr_timesheet', 'mail','report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
        'data/mail_template.xml',
        'data/cron.xml',
    ],
    'installable': True,
}