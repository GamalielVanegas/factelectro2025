from odoo import models, fields, api
import logging
import json
import base64

logger = logging.getLogger(__name__)

class DteDocument(models.Model):
    _name = 'dte.document'
    _description = 'Documento Tributario Electrónico'
    _rec_name = 'codigo_generacion'

    move_id = fields.Many2one('account.move', string='Factura', required=True, ondelete='cascade')
    tipo_documento = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Comprobante de Retención'),
        ('08', 'Nota de Crédito'),
    ], string='Tipo de Documento', required=True)
    codigo_generacion = fields.Char(string='Código de Generación', size=36)
    numero_control = fields.Char(string='Número de Control', size=31)
    sello_recepcion = fields.Char(string='Sello de Recepción', size=40)
    json_dte = fields.Binary(string='Archivo JSON Firmado')
    version_legible_pdf = fields.Binary(string='Versión Legible PDF')
    estado_dte = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('validado', 'Validado por DGII'),
        ('rechazado', 'Rechazado'),
        ('invalidado', 'Invalidado'),
    ], string='Estado DTE', default='borrador')
    fecha_envio = fields.Datetime(string='Fecha de Envío')
    modelo_facturacion = fields.Selection([
        ('previo', 'Previo'),
        ('definitivo', 'Definitivo'),
    ], string='Modelo de Facturación')
    tipo_transmision = fields.Selection([
        ('normal', 'Normal'),
        ('contingencia', 'Contingencia'),
    ], string='Tipo de Transmisión')
    condicion_operacion = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ], string='Condición de la Operación')
    observaciones = fields.Text(string='Observaciones')
    valor_letras = fields.Char(string='Valor en Letras')

    @api.model
    def create(self, vals):
        if not vals.get('codigo_generacion'):
            vals['codigo_generacion'] = self.env['ir.sequence'].next_by_code('dte.document') or 'DTE-TEST-001'
        return super().create(vals)

    def enviar_dte(self):
        for record in self:
            # Crear contenido simulado del JSON del DTE
            json_data = {
                'codigo_generacion': record.codigo_generacion,
                'numero_control': record.numero_control or 'NC-00001',
                'tipo_documento': record.tipo_documento,
                'modelo_facturacion': record.modelo_facturacion,
                'tipo_transmision': record.tipo_transmision,
                'condicion_operacion': record.condicion_operacion,
                'estado': 'enviado',
                'fecha_envio': fields.Datetime.now().isoformat(),
                'observaciones': record.observaciones or '',
                'valor_letras': record.valor_letras or '',
            }

            # Guardar JSON como base64
            json_bytes = json.dumps(json_data, indent=4).encode('utf-8')
            record.json_dte = base64.b64encode(json_bytes)

            # Generar PDF de forma segura usando el servicio de reportes
            report_service = self.env['ir.actions.report']
            pdf_content, _ = report_service.with_context(active_ids=[record.id])._render_qweb_pdf('dte_sv.report_dte_document_pdf')
            record.version_legible_pdf = base64.b64encode(pdf_content)

            # Actualizar estado
            record.estado_dte = 'enviado'
            record.fecha_envio = fields.Datetime.now()

            # Log del evento
            self.env['ir.logging'].create({
                'name': 'DTE Enviado',
                'type': 'server',
                'level': 'info',
                'dbname': self._cr.dbname,
                'message': f'DTE {record.codigo_generacion} enviado y PDF generado.',
                'path': 'dte.document',
                'func': 'enviar_dte',
                'line': '0',
            })

