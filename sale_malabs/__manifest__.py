{
    'name': 'Sale Malabs',
    'version': '1.4',
    'category': 'Extra Tools',
    'description': '',
    'author': 'ZOOU Qinn <qinn.zou@newbiiz.com>',
    'depends': [
        'sale_margin', 'product_malabs', 'purchase_malabs',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/global.xml',
        'data/rma.xml',
        'views/view.xml',
        'views/view_from_studio.xml',
        'views/report_invoice.xml',
        'views/report_rma.xml',
    ],
    'website': "http://www.newbiiz.com",
}