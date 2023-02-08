# -*- coding: utf-8 -*-
{
    'name': "Migrar información",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Josué Flores Osorio [josueflores.05@gmail.com]",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/res_partner.xml',
        'views/ir_attachment.xml',
        'wizard/message_wizard.xml',
    ],
    # only loaded in demonstration mode
}
