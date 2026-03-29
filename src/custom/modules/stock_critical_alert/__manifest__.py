{
    'name': 'Stock Critical Alert',
    'version': '18.0.1.0.0',
    'summary': 'Alertas automáticas cuando el stock cae por debajo del mínimo configurado',
    'category': 'Inventory',
    'author': 'enrique.simon801@gmail.com',
    'depends': ['stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_critical_alert_cron.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}