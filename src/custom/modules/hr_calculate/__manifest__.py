{
    'name': 'Cálculo Automático de Beneficios',
    'version': '18.0.1.0.0',
    'summary': 'Beneficios laborales automáticos según tipo de contrato usando reglas salariales nativas',
    'category': 'Payroll',
    'author': 'Simon',
    'depends': ['hr_payroll', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'views/hr_benefit_config_views.xml',
        'views/hr_contract_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
