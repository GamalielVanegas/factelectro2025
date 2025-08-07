# -*- coding: utf-8 -*-
import requests
from odoo import http
from odoo.http import request

class DTEIntegration(http.Controller):
    @http.route('/dte_sv/auth', type='json', auth='none', methods=['POST'])
    def authenticate(self, **kwargs):
        # Leer configuración
        params   = request.env['ir.config_parameter'].sudo()
        base_url = params.get_param('dte_sv.env_url_prueba') or ''
        base_url = base_url.rstrip('/')                                 # <-- evito doble slash/path
        user     = params.get_param('dte_sv.api_user')
        pwd      = params.get_param('dte_sv.api_password')

        # Llamada HTTP al sandbox
        url  = f"{base_url}/seguridad/auth"                              # <-- construyo bien la URL
        resp = requests.post(url, json={'usuario': user, 'password': pwd})
        resp.raise_for_status()                                          # <-- ahora arroja excepción si falla
        token = resp.json().get('token')

        # Guardar token y vencimiento
        params.set_param('dte_sv.jwt_token', token)
        return {'status': 'ok', 'token': token}

