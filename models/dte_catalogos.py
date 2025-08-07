# -*- coding: utf-8 -*-
from odoo import models, fields

class DteCatalogos(models.Model):
    _name = 'dte.catalogos'
    _description = 'Catálogos SAT dinámicos'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Descripción', required=True)
    catalog_type = fields.Selection([
        ('CAT-001','Ambiente de destino'),
        ('CAT-002','Tipo de Documento'),
        ('CAT-003','Modelo de Facturación'),
        ('CAT-004','Tipo de Transmisión'),
        ('CAT-005','Tipo de Contingencia'),
        ('CAT-006','Retención IVA MH'),
        ('CAT-007','Tipo de Generación del Documento'),
        ('CAT-008','Catálogo eliminado'),
        ('CAT-009','Tipo de establecimiento'),
        ('CAT-010','Código tipo de Servicio (Médico)'),
        ('CAT-011','Tipo de ítem'),
        ('CAT-012','Departamento'),
        ('CAT-013','Municipio'),
        ('CAT-014','Unidad de Medida'),
        ('CAT-015','Tributos'),
        ('CAT-016','Condición de la Operación'),
        ('CAT-017','Forma de Pago'),
        ('CAT-018','Plazo'),
        ('CAT-019','Código de Actividad Económica'),
        ('CAT-020','País'),
        ('CAT-021','Otros Documentos Asociados'),
        ('CAT-022','Tipo de identificación del Receptor'),
        ('CAT-023','Tipo de Documento en Contingencia'),
        ('CAT-024','Tipo de Invalidación'),
        ('CAT-025','Título de remisión de bienes'),
        ('CAT-026','Tipo de Donación'),
        ('CAT-027','Recinto fiscal'),
        ('CAT-028','Régimen'),
        ('CAT-029','Tipo de persona'),
        ('CAT-030','Transporte'),
        ('CAT-031','INCOTERMS'),
        ('CAT-032','Domicilio Fiscal'),
    ], string='Catálogo', required=True)

