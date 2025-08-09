# -*- coding: utf-8 -*-
{
    'name': 'Facturación Electrónica El Salvador (DTE)',
    'version': '1.0.0',
    'summary': 'Gestión de Documentos Tributarios Electrónicos para El Salvador',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': ['account', 'sale', 'mail'],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',

        # Datos
        'data/ir_sequence_data.xml',
        'data/sat_catalogos.xml',
        'data/ir_cron_data.xml',

        # Acciones que otros menús/vistas referencian
        'views/dte_document_actions.xml',

        # VISTA del wizard (debe cargarse ANTES del menú/acción que la referencia)
        'views/dte_config_views.xml',

        # Menú raíz y acción de configuración (ya puede referenciar la vista del wizard)
        'views/dte_config_menu.xml',

        # Resto de vistas/menús que usan menu_dte_root o actions ya cargadas
        'views/dte_document_views.xml',
        'views/dte_event_views.xml',
        'views/dte_event_menu.xml',
        'views/dte_cert_menu.xml',
        'views/certificate_import_views.xml',

        # Reportes / plantillas
        'reportes/qr_template.xml',
        'views/dte_document_report.xml',
        'views/dte_mail_template.xml',
    ],
    'installable': True,
    'application': True,
}

