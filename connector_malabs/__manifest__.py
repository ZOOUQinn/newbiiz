{
    'name': 'Connector To CSV',
    'depends': [
        'connector',
        'sale_malabs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
    ],
    'version': '1.4',
}