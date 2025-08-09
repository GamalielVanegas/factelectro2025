# -*- coding: utf-8 -*-
import logging
import json
import base64
import uuid
import requests
from requests.exceptions import HTTPError
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class DteDocument(models.Model):
    _name = 'dte.document'
    _description = 'Documento Tributario Electrónico'
    _rec_name = 'codigo_generacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # <- para usar message_post en chatter

    move_id             = fields.Many2one('account.move', string='Factura', required=True, ondelete='cascade')
    tipo_documento      = fields.Selection([
        ('01', 'Factura'),
        ('03', 'Comprobante de Crédito Fiscal'),
        ('04', 'Comprobante de Retención'),
        ('08', 'Nota de Crédito'),
    ], string='Tipo de Documento', required=True)
    codigo_generacion   = fields.Char(string='Código de Generación', size=36)
    numero_control      = fields.Char(string='Número de Control', size=31)
    sello_recepcion     = fields.Char(string='Sello de Recepción', size=64)
    json_dte            = fields.Binary(string='Documento Firmado (JSON)')
    version_legible_pdf = fields.Binary(string='Versión Legible PDF')
    estado_dte          = fields.Selection([
        ('borrador', 'Borrador'),
        ('enviado', 'Enviado'),
        ('validado', 'Validado por DGII'),
        ('rechazado', 'Rechazado'),
        ('invalidado', 'Invalidado'),
    ], string='Estado DTE', default='borrador')
    fecha_envio         = fields.Datetime(string='Fecha de Envío')
    modelo_facturacion  = fields.Selection([('previo','Previo'),('definitivo','Definitivo')], string='Modelo de Facturación', default='definitivo')
    tipo_transmision    = fields.Selection([('normal','Normal'),('contingencia','Contingencia')], string='Tipo de Transmisión', default='normal')
    condicion_operacion = fields.Selection([('contado','Contado'),('credito','Crédito')], string='Condición de la Operación', default='contado')
    observaciones       = fields.Text(string='Observaciones')
    valor_letras        = fields.Char(string='Valor en Letras')

    @api.model
    def create(self, vals):
        if not vals.get('codigo_generacion'):
            vals['codigo_generacion'] = str(uuid.uuid4()).upper()
        if not vals.get('numero_control'):
            # 31 chars: prefijo simple + relleno
            vals['numero_control'] = ('DTE-01-' + (vals.get('codigo_generacion') or '')).replace('-', '')[:31].ljust(31,'0')
        return super().create(vals)

    # -------------------------- Helpers -------------------------- #

    def _log_note(self, body):
        """Postea al chatter si está disponible; si no, registra en log."""
        try:
            return self.message_post(body=body)
        except Exception:
            _logger.info("NOTE DTE %s: %s", self.ids, body)
            return False

    def _company_nit(self):
        # Debe coincidir con el .crt usado por el firmador
        nit = (self.move_id.company_id.vat or '').replace('-', '').replace(' ', '').strip()
        if not nit or len(nit) != 14 or not nit.isdigit():
            raise UserError(_('El NIT de la compañía debe tener 14 dígitos (sin guiones).'))
        return nit

    def _build_dte_01(self):
        """Construye un DTE FE tipo 01 mínimo válido (ambiente 00) desde account.move."""
        self.ensure_one()
        move = self.move_id
        company = move.company_id
        partner = move.partner_id

        # Totales simples (asumo IVA 13% cuando el impuesto de la línea es 13)
        lines = []
        total_grav = 0
        total_iva  = 0
        idx = 1
        for l in move.invoice_line_ids.filtered(lambda x: not x.display_type):
            qty = float(l.quantity or 0.0)
            pu  = float(l.price_unit or 0.0)
            sub = round(qty * pu, 2)
            has_iva = any(abs(t.amount - 13) < 0.001 for t in l.tax_ids)
            iva = round(sub * 0.13, 2) if has_iva else 0.0
            grav = sub if has_iva else 0.0
            total_grav += grav
            total_iva  += iva
            lines.append({
                'numItem': idx, 'tipoItem': 'B',
                'descripcion': l.name or l.product_id.display_name or 'Item',
                'cantidad': qty, 'precioUni': pu, 'montoDescu': 0,
                'ventaNoSuj': 0, 'ventaExenta': 0, 'ventaGravada': grav,
                'tributos': (['20'] if has_iva else []), 'psv': 0, 'noGravado': 0,
            })
            idx += 1

        total_pagar = round(total_grav + total_iva, 2)
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        fec = now.strftime('%Y-%m-%d')
        hor = now.strftime('%H:%M:%S')

        dte = {
            'identificacion': {
                'version': 2, 'ambiente': '00', 'tipoDoc': '01',
                'tipoModelo': 1, 'tipoOperacion': 1, 'tipoContingencia': 0,
                'codigoGeneracion': self.codigo_generacion,
                'numeroControl': self.numero_control,
                'fecEmi': fec, 'horEmi': hor, 'tipoMoneda': (move.currency_id.name or 'USD'),
            },
            'emisor': {
                'nit': self._company_nit(),
                'nrc': company.company_registry or '123456-7',
                'nombre': company.name, 'nombreComercial': company.name,
                'codActividad': getattr(company, 'sv_cod_actividad', '62010'),
                'descActividad': getattr(company, 'sv_desc_actividad', 'DESARROLLO DE SOFTWARE'),
                'tipoEstablecimiento': '01',
                'telefono': company.phone or '22223333',
                'correo': company.email or 'info@example.com',
                'direccion': {
                    'departamento': '01', 'municipio': '01',
                    'complementoDireccion': company.street or 'DIRECCION',
                },
            },
            'receptor': {
                'tipoDocumento': '13',
                'numDocumento': (partner.vat or self._company_nit()).replace('-', ''),
                'nombre': partner.name or 'CLIENTE',
                'correo': partner.email or 'cliente@example.com',
                'telefono': partner.phone or '77777777',
                'direccion': {
                    'departamento': '01', 'municipio': '01',
                    'complementoDireccion': partner.street or 'DIR CLIENTE',
                },
            },
            'cuerpoDocumento': lines,
            'resumen': {
                'totalNoSuj': 0, 'totalExenta': 0,
                'totalGravada': round(total_grav, 2),
                'subTotalVentas': round(total_grav, 2),
                'descu': 0,
                'tributos': ([{'codigo': '20', 'descripcion': 'IVA', 'valor': round(total_iva, 2)}] if total_iva else []),
                'totalIva': round(total_iva, 2),
                'totalPagar': total_pagar,
                'totalLetras': self.valor_letras or 'PENDIENTE',
                'saldoFavor': 0, 'condicionOperacion': (1 if self.condicion_operacion != 'credito' else 2),
                'pagos': [{'codigo': '01', 'montoPago': total_pagar, 'referencia': 'EFECTIVO'}],
            },
            'extension': {'nombEntrega': '-', 'docEntrega': '-', 'nombRecibe': '-', 'docRecibe': '-'},
            'apendice': [{'campo':'Observaciones','etiqueta':'Obs','valor': self.observaciones or 'Factura FE 01'}],
        }
        return dte

    # -------------------------- Flujo principal -------------------------- #

    def enviar_dte(self):
        """Genera DTE 01, firma vía microservicio y transmite a MH (ambiente de pruebas)."""
        params        = self.env['ir.config_parameter'].sudo()
        firmador_base = (params.get_param('dte_sv.firmador_url') or '').rstrip('/')
        firmador_url  = f"{firmador_base}/firmardocumento/"
        mh_url_base   = (params.get_param('dte_sv.env_url_prueba') or '').rstrip('/')
        token_mh      = params.get_param('dte_sv.jwt_token') or ''
        key_pass      = params.get_param('dte_sv.key_pass') or ''

        for record in self:
            # 1) Construir DTE FE 01
            dte_obj = record._build_dte_01()

            # 2) Firmar (JsonDTE objeto). Fallback a dteJson si el servicio lo exige.
            payload = {
                'nit':         record._company_nit(),
                'activo':      True,
                'passwordPri': key_pass,
                'JsonDTE':     dte_obj,
            }
            try:
                r = requests.post(firmador_url, json=payload, timeout=120)
                r.raise_for_status()
                jr = r.json()
                if isinstance(jr, dict) and jr.get('status') == 'ERROR':
                    # Fallback a dteJson (algunas builds)
                    payload.pop('JsonDTE')
                    payload['dteJson'] = dte_obj
                    r2 = requests.post(firmador_url, json=payload, timeout=120)
                    r2.raise_for_status()
                    jr = r2.json()
                if not isinstance(jr, dict) or jr.get('status') == 'ERROR':
                    raise UserError(_('Firmador devolvió ERROR: %s') % (jr,))
                # Convención más frecuente: documento firmado en 'body'
                firmado = jr.get('body') if isinstance(jr.get('body'), str) else json.dumps(jr.get('body'), ensure_ascii=False)
            except Exception as e:
                _logger.exception('Error al firmar DTE %s', record.codigo_generacion)
                record._log_note(f'❌ Error al firmar DTE: {e}')
                raise

            # 3) Guardar firmado (string JSON) en binario
            record.json_dte = base64.b64encode((firmado or '').encode('utf-8'))

            # 4) Enviar a MH (sandbox). Algunos endpoints esperan el JSON firmado como body crudo.
            sello = False
            try:
                headers = {'Authorization': f'Bearer {token_mh}', 'Content-Type': 'application/json'}
                # Ejemplo: /recepcion/dte (ajusta si tu sandbox usa otra ruta)
                r3 = requests.post(f"{mh_url_base}/recepcion/dte", data=firmado, headers=headers, timeout=120)
                r3.raise_for_status()
                jr3 = r3.json() if r3.content else {}
                sello = jr3.get('sello_recepcion') or jr3.get('sello') or False
            except HTTPError as he:
                _logger.warning('MH no disponible p/DTE %s: %s', record.codigo_generacion, he)
                # Si tienes un modelo de eventos/contingencia, puedes llamarlo aquí.
                record.tipo_transmision = 'contingencia'
                record._log_note('⚠️ MH no disponible, marcado en contingencia.')
            except Exception as e:
                _logger.exception('Error enviando a MH DTE %s', record.codigo_generacion)
                record._log_note(f'⚠️ Error al transmitir a MH: {e}')

            # 5) Actualizar estado
            record.write({
                'sello_recepcion': sello or '',
                'estado_dte': 'enviado',
                'fecha_envio': fields.Datetime.now(),
            })

            # 6) Generar PDF (plantilla QWeb ya incluida)
            try:
                pdf_content, _ = self.env['ir.actions.report'].with_context(active_ids=[record.id])._render_qweb_pdf('dte_sv.report_dte_document_pdf')
                record.version_legible_pdf = base64.b64encode(pdf_content)
            except Exception as e:
                _logger.warning('No se pudo generar PDF para DTE %s: %s', record.codigo_generacion, e)

            # 7) Enviar correo (si hay email de cliente)
            recipient = (record.move_id.partner_id.email or record.move_id.invoice_partner_id.email or record.move_id.commercial_partner_id.email or '').strip()
            if recipient:
                template = self.env.ref('dte_sv.email_template_dte_document', raise_if_not_found=False)
                attachments = [
                    (0, 0, {'name': f'{record.move_id.name}.pdf', 'datas': record.version_legible_pdf, 'mimetype': 'application/pdf'}),
                    (0, 0, {'name': f'DTE_{record.codigo_generacion}.json', 'datas': record.json_dte, 'mimetype': 'application/json'}),
                ]
                if template:
                    try:
                        template.send_mail(
                            record.id,
                            force_send=True,
                            email_values={
                                'email_from': record.env.company.email,
                                'email_to': recipient,
                                'subject': f"Factura {record.move_id.name} y DTE {record.codigo_generacion}",
                                'attachment_ids': attachments
                            }
                        )
                    except Exception as e:
                        _logger.warning('No se pudo enviar correo DTE %s: %s', record.codigo_generacion, e)
                else:
                    record._log_note('⚠️ Plantilla de correo no encontrada: dte_sv.email_template_dte_document')
            else:
                # account.move suele heredar mail.thread, pero por si acaso:
                try:
                    record.move_id.message_post(body='ℹ️ Cliente sin email; no se envió correo.')
                except Exception:
                    _logger.info("Factura %s sin email de cliente; no se envió correo.", record.move_id.name)

