{
    'name': 'Facturación Electrónica El Salvador (DTE)',
    'version': '1.0.0',
    'summary': 'Gestión de Documentos Tributarios Electrónicos para El Salvador',
    'description': 'Permite generar, firmar y enviar DTEs a la DGII desde Odoo.',
    'category': 'Accounting',
    'author': 'Tu Nombre o Empresa',
    'website': 'https://tusitio.com',
    'depends': ['account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/dte_mail_template.xml',
        'views/dte_document_actions.xml',
        'views/dte_document_views.xml',
        'views/dte_document_report.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

