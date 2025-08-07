# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class DteEvents(models.Model):
    _name = 'dte.events'
    _description = 'Eventos DTE (Anulación, Contingencia)'

    name         = fields.Char('Evento', default='Evento DTE')
    date_event   = fields.Datetime('Fecha Evento', default=fields.Datetime.now)
    dte_id       = fields.Many2one('dte.document', string='DTE')
    event_type   = fields.Selection([('contingencia','Contingencia'),('invalidation','Invalidación')], string='Tipo Evento')
    description  = fields.Text('Descripción')

    @api.model
    def send_contingency(self, dte_record):
        """Registrar evento de contingencia cuando MH no está disponible."""
        ev = self.create({
            'dte_id':     dte_record.id,
            'event_type': 'contingencia',
            'description': 'Se marcó en contingencia por indisponibilidad del servicio MH.',
        })
        _logger.info('Evento contingencia creado para DTE %s', dte_record.codigo_generacion)
        dte_record.message_post(body=f'⚠️ DTE en Contingencia (evento #{ev.id}).')
        return True

    @api.model
    def send_invalidation(self, dte_record):
        """Construye y envía evento de invalidación (a implementar)."""
        ev = self.create({
            'dte_id':     dte_record.id,
            'event_type': 'invalidation',
            'description': 'Evento de invalidación enviado.',
        })
        _logger.info('Evento invalidación creado para DTE %s', dte_record.codigo_generacion)
        dte_record.message_post(body=f'ℹ️ Evento de invalidación (#{ev.id}) procesado.')
        return True

