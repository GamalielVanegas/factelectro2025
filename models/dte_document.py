# -*- coding: utf-8 -*-
import logging
import json
import base64
import requests
from requests.exceptions import HTTPError

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class DteDocument(models.Model):
    _name = 'dte.document'
    _description = 'Documento Tributario Electrónico'
    _rec_name = 'codigo_generacion'

    move_id             = fields.Many2one('account.move', string='Factura', required=True, ondelete='cascade')
    tipo_documento      = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Comprobante de Retención'),
        ('08', 'Nota de Crédito'),
    ], string='Tipo de Documento', required=True)
    codigo_generacion   = fields.Char(string='Código de Generación', size=36)
    numero_control      = fields.Char(string='Número de Control', size=31)
    sello_recepcion     = fields.Char(string='Sello de Recepción', size=40)
    json_dte            = fields.Binary(string='Archivo JSON Firmado')
    version_legible_pdf = fields.Binary(string='Versión Legible PDF')
    estado_dte          = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('validado', 'Validado por DGII'),
        ('rechazado', 'Rechazado'),
        ('invalidado', 'Invalidado'),
    ], string='Estado DTE', default='borrador')
    fecha_envio         = fields.Datetime(string='Fecha de Envío')
    modelo_facturacion  = fields.Selection([('previo','Previo'),('definitivo','Definitivo')], string='Modelo de Facturación')
    tipo_transmision    = fields.Selection([('normal','Normal'),('contingencia','Contingencia')], string='Tipo de Transmisión')
    condicion_operacion = fields.Selection([('contado','Contado'),('credito','Crédito')], string='Condición de la Operación')
    observaciones       = fields.Text(string='Observaciones')
    valor_letras        = fields.Char(string='Valor en Letras')

    @api.model
    def create(self, vals):
        if not vals.get('codigo_generacion'):
            vals['codigo_generacion'] = (
                self.env['ir.sequence'].next_by_code('dte.document')
                or 'DTE-TEST-001'
            )
        return super().create(vals)

    def enviar_dte(self):
        """Genera JSON, llama API MH, maneja contingencia, genera PDF y envía correo."""
        for record in self:
            # 1) Generar JSON interno
            json_data = {
                'codigo_generacion':  record.codigo_generacion,
                'numero_control':     record.numero_control or 'NC-00001',
                'tipo_documento':     record.tipo_documento,
                'modelo_facturacion': record.modelo_facturacion,
                'tipo_transmision':   record.tipo_transmision,
                'condicion_operacion':record.condicion_operacion,
                'estado':             'enviado',
                'fecha_envio':        fields.Datetime.now().isoformat(),
                'observaciones':      record.observaciones or '',
                'valor_letras':       record.valor_letras or '',
            }
            record.json_dte = base64.b64encode(
                json.dumps(json_data, indent=2).encode('utf-8')
            )

            # 2) Llamada HTTP al sandbox del MH
            params   = self.env['ir.config_parameter'].sudo()
            base_url = (params.get_param('dte_sv.env_url_prueba') or '').rstrip('/')
            url      = f"{base_url}/recepcion/dte"
            token    = params.get_param('dte_sv.jwt_token')
            headers  = {
                'Authorization': f'Bearer {token}',
                'Content-Type':  'application/json',
            }
            mode = 'normal'
            sello = False
            try:
                resp = requests.post(url, data=record.json_dte.decode('utf-8'), headers=headers)
                resp.raise_for_status()
                resultado = resp.json()
                sello = resultado.get('sello_recepcion')
            except HTTPError as e:
                # Modo contingencia si el servicio no está disponible
                mode = 'contingencia'
                _logger.warning('MH no disponible para DTE %s: %s', record.codigo_generacion, e)
                # Registrar evento de contingencia
                self.env['dte.events'].send_contingency(record)

            # 3) Actualizar registro con estado, sello, modo y fecha
            record.write({
                'sello_recepcion':   sello,
                'tipo_transmision':  mode,
                'estado_dte':         'enviado',
                'fecha_envio':        fields.Datetime.now(),
            })

            # 4) Generar PDF QWeb
            pdf_content, _ = self.env['ir.actions.report'] \
                                  .with_context(active_ids=[record.id]) \
                                  ._render_qweb_pdf('dte_sv.report_dte_document_pdf')
            pdf_b64 = base64.b64encode(pdf_content)
            record.write({'version_legible_pdf': pdf_b64})

            # 5) Registrar en log interno
            _logger.info('DTE %s procesado en modo %s', record.codigo_generacion, mode)

            # 6) Enviar correo con adjuntos (siempre)
            recipient = (
                record.move_id.partner_id.email
                or record.move_id.invoice_partner_id.email
                or record.move_id.commercial_partner_id.email
            )
            if not recipient:
                record.move_id.message_post(body='❌ Cliente sin email, no se envió DTE.')
                continue
            template = self.env.ref('dte_sv.email_template_dte_document')
            attachments = [
                (0, 0, {
                    'name':     f'{record.move_id.name}.pdf',
                    'datas':    pdf_b64,
                    'mimetype': 'application/pdf',
                }),
                (0, 0, {
                    'name':     f'DTE_{record.codigo_generacion}.json',
                    'datas':    record.json_dte,
                    'mimetype': 'application/json',
                }),
            ]
            template.send_mail(
                record.id,
                force_send=True,
                email_values={
                    'email_from':     record.env.company.email,
                    'email_to':       recipient,
                    'subject':        f"Factura {record.move_id.name} y DTE {record.codigo_generacion}",
                    'attachment_ids': attachments,
                }
            )

