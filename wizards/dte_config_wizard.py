from odoo import models, fields, api

class DTEConfigWizard(models.TransientModel):
    _name = 'dte.config.wizard'
    _description = 'Configuración DTE'

    api_user       = fields.Char('Usuario API', required=True)
    api_password   = fields.Char('Contraseña API', required=True)
    env_url_prueba = fields.Char('URL Pruebas', required=True)
    env_url_prod   = fields.Char('URL Producción')

    def action_save(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('dte_sv.api_user',       self.api_user)
        params.set_param('dte_sv.api_password',   self.api_password)
        params.set_param('dte_sv.env_url_prueba', self.env_url_prueba)
        params.set_param('dte_sv.env_url_prod',   self.env_url_prod or '')
        return {'type': 'ir.actions.act_window_close'}

