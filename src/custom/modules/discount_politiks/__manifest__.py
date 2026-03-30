
{

    'name': 'Políticas de Descuento en Facturas',
    'version': '18.0.1.0.0',
    'summary': 'Descuentos automáticos en facturas según el tipo de cliente',
    'category': 'Accounting',
    'author': 'Simon',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_discount_rule_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

