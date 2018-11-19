{
    'name': 'Connector To CSV',
    'depends': [
        'connector',
        'product_malabs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/ir_attachment_views.xml',
    ]
}