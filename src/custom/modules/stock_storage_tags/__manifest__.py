{
    'name': 'Etiquetas Inteligentes de Almacenamiento',
    'version': '18.0.1.0.0',
    'summary': 'Etiquetas dinámicas para mejorar la organización de productos en almacenes',
    'category': 'Inventory',
    'author': 'Simon',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_product_tag_wizard_views.xml',
        'views/stock_storage_tag_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
