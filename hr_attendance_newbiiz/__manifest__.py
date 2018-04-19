# -*- coding: utf-8 -*-
{
    'name': "hr_attendance_newbiiz",

    'summary': "",

    'description': "",

    'author': "ERP Group, Newbiiz",
    'website': "http://www.newbiiz.com",

    'category': 'hr',
    'version': '0.1',

    'depends': ['hr_attendance'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/web_asset_backend_template.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        "static/src/xml/attendance.xml",
    ],
}