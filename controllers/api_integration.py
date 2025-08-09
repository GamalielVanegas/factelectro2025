# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class DTEIntegration(http.Controller):
    """
    Endpoints de integración:
      - /dte_sv/auth    : Obtiene y guarda JWT del sandbox (PARAMS: dte_sv.api_user, dte_sv.api_password, dte_sv.env_url_prueba)
      - /dte_sv/firmar  : Proxy al microservicio firmador (POST JsonDTE/dteJson como OBJETO)
    """

    # ------------------------------------------------------------------
    # AUTH: obtiene token del sandbox y lo guarda en ir.config_parameter
    # ------------------------------------------------------------------
    @http.route('/dte_sv/auth', type='json', auth='none', methods=['POST'])
    def authenticate(self, **kwargs):
        params   = request.env['ir.config_parameter'].sudo()
        base_url = (params.get_param('dte_sv.env_url_prueba') or '').rstrip('/')
        user     = (params.get_param('dte_sv.api_user') or '').strip()
        pwd      = params.get_param('dte_sv.api_password') or ''
        url      = f"{base_url}/seguridad/auth"

        if not base_url or not user or not pwd:
            return {'status': 'ERROR', 'body': 'Faltan parámetros: env_url_prueba / api_user / api_password'}

        sess = requests.Session()
        sess.headers.update({'Accept': 'application/json'})

        # 1) Preferido por sandbox: FORM user/pwd
        try:
            r = sess.post(url, data={'user': user, 'pwd': pwd}, timeout=60)
            j = {}
            try:
                j = r.json()
            except Exception:
                pass
            token = (j.get('body') or {}).get('token') or j.get('token') or ''
            if token and token.startswith('Bearer '):
                token = token[len('Bearer '):]
            if r.status_code == 200 and token:
                params.set_param('dte_sv.jwt_token', token)
                return {'status': 'ok', 'token': token}
        except requests.RequestException as e:
            _logger.warning("Auth FORM error: %s", e)

        # 2) Fallback: JSON {user, pwd}
        try:
            r = sess.post(url, json={'user': user, 'pwd': pwd}, timeout=60)
            j = {}
            try:
                j = r.json()
            except Exception:
                pass
            token = (j.get('body') or {}).get('token') or j.get('token') or ''
            if token and token.startswith('Bearer '):
                token = token[len('Bearer '):]
            if r.status_code == 200 and token:
                params.set_param('dte_sv.jwt_token', token)
                return {'status': 'ok', 'token': token}
            # Reporte de error útil
            body_dbg = j or r.text
            return {'status': 'ERROR', 'http': r.status_code, 'body': body_dbg}
        except requests.RequestException as e:
            return {'status': 'ERROR', 'body': f'Fallo de red autenticando: {e}'}

    # ------------------------------------------------------------------
    # FIRMAR: envía el DTE al microservicio firmador
    # ------------------------------------------------------------------
    @http.route('/dte_sv/firmar', type='json', auth='none', methods=['POST'])
    def sign_document(self, **kwargs):
        """
        Proxy al microservicio firmador. Espera en kwargs:
          - nit (string, 14 dígitos)             -> debe coincidir con el .crt
          - passwordPri (string)                 -> clave privada (p.ej. renta2025$)
          - JsonDTE (objeto JSON del DTE)        -> objeto, NO string
        Compatibilidad: si llega 'dteJson' como objeto, se convierte a 'JsonDTE'.
        """
        params = request.env['ir.config_parameter'].sudo()
        base   = (params.get_param('dte_sv.firmador_url') or '').rstrip('/')
        if not base:
            return {'status': 'ERROR', 'body': 'Falta dte_sv.firmador_url'}
        url = f"{base}/firmardocumento/"

        # Normalizar payload: usar 'JsonDTE' objeto
        payload = dict(kwargs or {})
        if 'JsonDTE' not in payload and 'dteJson' in payload:
            # Si dteJson viene como objeto → renombrar; si viene como string y parece JSON → parsear
            d = payload.pop('dteJson')
            if isinstance(d, str):
                try:
                    d = json.loads(d)
                except Exception:
                    # lo dejamos como string; algunos builds lo aceptan, pero preferimos objeto
                    pass
            payload['JsonDTE'] = d

        # Validaciones rápidas
        if 'nit' not in payload or not str(payload.get('nit', '')).strip():
            return {'status': 'ERROR', 'body': {'codigo': '809', 'mensaje': ['NIT es requerido']}}
        if 'passwordPri' not in payload or not str(payload.get('passwordPri', '')).strip():
            return {'status': 'ERROR', 'body': {'codigo': '809', 'mensaje': ['Clave privada es requerida']}}
        if 'JsonDTE' not in payload:
            return {'status': 'ERROR', 'body': {'codigo': '809', 'mensaje': ['JsonDTE es requerido']}}

        try:
            resp = requests.post(url, json=payload, timeout=120)
            # Si no es 200, intentamos diagnosticar
            if resp.status_code != 200:
                try:
                    return {'status': 'ERROR', 'http': resp.status_code, 'body': resp.json()}
                except Exception:
                    return {'status': 'ERROR', 'http': resp.status_code, 'body': resp.text}
            # OK → devolver JSON del firmador tal cual
            return resp.json()
        except requests.RequestException as e:
            return {'status': 'ERROR', 'body': {'codigo': 'HTTP', 'mensaje': str(e)}}

