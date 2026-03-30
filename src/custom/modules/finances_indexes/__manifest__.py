{
    'name': 'Indicadores de Salud Financiera',
    'version': '18.0.1.0.0',
    'summary': 'Tablero con KPIs financieros y semáforos según umbrales configurados',
    'category': 'Accounting',
    'author': 'Simon',
    'depends': ['account', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_financial_kpi_views.xml',
        'views/account_financial_kpi_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'finances_indexes/static/src/js/dashboard.js',
            'finances_indexes/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
