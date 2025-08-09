# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DTEConfigWizard(models.TransientModel):
    _name = 'dte.config.wizard'
    _description = 'Configuración DTE (SV)'

    # Campos que usas en la vista
    api_user       = fields.Char(string='Usuario API')
    api_password   = fields.Char(string='Contraseña API')
    env_url_prueba = fields.Char(string='URL Sandbox')
    env_url_prod   = fields.Char(string='URL Producción')
    firmador_url   = fields.Char(string='URL Firmador (Docker)')
    key_pass       = fields.Char(string='Clave privada del .crt')

    @api.model
    def default_get(self, fields_list):
        """Precarga valores desde ir.config_parameter."""
        res = super().default_get(fields_list)
        ICP = self.env['ir.config_parameter'].sudo()
        res.update({
            'api_user':       ICP.get_param('dte_sv.api_user') or '',
            'api_password':   ICP.get_param('dte_sv.api_password') or '',
            'env_url_prueba': ICP.get_param('dte_sv.env_url_prueba') or '',
            'env_url_prod':   ICP.get_param('dte_sv.env_url_prod') or '',
            'firmador_url':   ICP.get_param('dte_sv.firmador_url') or '',
            'key_pass':       ICP.get_param('dte_sv.key_pass') or '',
        })
        return res

    def action_save(self):
        """Guarda parámetros en ir.config_parameter."""
        self.ensure_one()
        vals = {
            'dte_sv.api_user':       (self.api_user or '').strip(),
            'dte_sv.api_password':   self.api_password or '',
            'dte_sv.env_url_prueba': (self.env_url_prueba or '').strip().rstrip('/'),
            'dte_sv.env_url_prod':   (self.env_url_prod or '').strip().rstrip('/'),
            'dte_sv.firmador_url':   (self.firmador_url or '').strip().rstrip('/'),
            'dte_sv.key_pass':       self.key_pass or '',
        }
        ICP = self.env['ir.config_parameter'].sudo()
        for k, v in vals.items():
            ICP.set_param(k, v)
        return {'type': 'ir.actions.act_window_close'}

