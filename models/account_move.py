# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    dte_document_id = fields.One2many(
        'dte.document', 'move_id', string='DTE Documento',
        help="Documento Tributario Electrónico asociado a esta factura"
    )

    def action_post(self):
        """Override de la validación de factura para generar y enviar el DTE."""
        # 1) Llamamos al método original para validar la factura
        res = super().action_post()

        # 2) Por cada factura validada, creamos y enviamos el DTE si es factura de cliente
        for move in self:
            if move.move_type == 'out_invoice' and not move.dte_document_id:
                # Crear el registro dte.document en borrador
                dte = self.env['dte.document'].create({
                    'move_id': move.id,
                    'tipo_documento': '01',      # 01 = Factura
                    'estado_dte': 'borrador',
                })
                try:
                    # Genera JSON, PDF y envía el correo
                    dte.enviar_dte()
                except Exception as e:
                    # Registrar el error en el log del servidor
                    _logger.error('Error al enviar DTE %s: %s', dte.codigo_generacion, e)
                    # Notificar en el chatter de la factura
                    move.message_post(
                        body=f'❌ Error al enviar Documento Electrónico (DTE): {e}'
                    )

        return res

