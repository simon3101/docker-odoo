{
    'name': 'Stock Critical Alert',
    'version': '18.0.1.0.0',
    'summary': 'Alertas automáticas cuando el stock cae por debajo del mínimo configurado',
    'category': 'Inventory',
    'author': 'Simon',
    'depends': ['stock', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_critical_alert_cron.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_critical_alert/static/src/js/dashboard.js',
            'stock_critical_alert/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
