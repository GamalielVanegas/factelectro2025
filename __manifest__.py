# -*- coding: utf-8 -*-
{
    'name': 'Facturación Electrónica El Salvador (DTE)',
    'version': '1.0.0',
    'summary': 'Gestión de Documentos Tributarios Electrónicos para El Salvador',
    'description': 'Permite generar, firmar y enviar DTEs a la DGII desde Odoo.',
    'category': 'Accounting',
    'author': 'Tu Nombre o Empresa',
    'website': 'https://tusitio.com',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'sale',
        'mail',
    ],
    'data': [
        # Seguridad y datos maestros
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'data/sat_catalogos.xml',
        'data/ir_cron_data.xml',

        # Vistas de configuración y eventos
        'views/dte_config_views.xml',
        'views/certificate_import_views.xml',
        'views/dte_event_views.xml',

        # Vistas de documentos y acciones
        'views/dte_document_views.xml',
        'views/dte_document_actions.xml',

        # Menús
        'views/dte_config_menu.xml',
        'views/dte_event_menu.xml',
        'views/dte_cert_menu.xml',

        # Plantillas y reportes
        'views/dte_mail_template.xml',
        'views/dte_document_report.xml',
        'reportes/qr_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

