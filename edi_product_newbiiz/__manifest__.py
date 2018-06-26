{
    'name': "EDI for Products",
    'version': '0.1',
    'depends': ['edi', 'product_newbiiz'],
    'website': "http://www.newbiiz.com",
    'author': "ZOOU Qinn <qinn.zou@newbiiz.com>",
    'category': "Extra Tools",
    'data': [
        'views/edi_product_views.xml',
        'views/edi_product_malabscad_views.xml',
        'data/edi_product_data.xml',
        'data/edi_product_malabscad_data.xml',
        'security/ir.model.access.csv',
    ],
}
