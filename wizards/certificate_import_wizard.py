# -*- coding: utf-8 -*-
import os
import base64
from odoo import models, fields, api
from odoo.tools.config import config

class CertificateImportWizard(models.TransientModel):
    _name = 'certificate.import.wizard'
    _description = 'Importar Certificado DTE'

    cert_file = fields.Binary('Certificado (.crt)', required=True)
    key_file  = fields.Binary('Clave Privada (.key)', required=True)
    key_pass  = fields.Char('Contraseña Clave', required=True)

    def action_import(self):
        # 1) Ruta al data_dir de Odoo (filestore base)
        data_dir = config.get('data_dir') or '/var/lib/odoo'
        # 2) Carpeta de filestore para esta base
        filestore = os.path.join(data_dir, 'filestore', self.env.cr.dbname)
        # 3) Nuestra subcarpeta DTE
        dest = os.path.join(filestore, 'dte')
        os.makedirs(dest, exist_ok=True)

        # 4) Definir rutas de destino
        dbname   = self.env.cr.dbname
        crt_path = os.path.join(dest, f'{dbname}.crt')
        key_path = os.path.join(dest, f'{dbname}.key')

        # 5) Decodificar los binarios y guardar
        with open(crt_path, 'wb') as f:
            f.write(base64.b64decode(self.cert_file))
        with open(key_path, 'wb') as f:
            f.write(base64.b64decode(self.key_file))
        os.chmod(crt_path, 0o600)
        os.chmod(key_path, 0o600)

        # 6) Almacenar en parámetros
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('dte_sv.cert_path', crt_path)
        params.set_param('dte_sv.key_path', key_path)
        params.set_param('dte_sv.key_pass', self.key_pass)

        # 7) Cerrar wizard
        return {'type': 'ir.actions.act_window_close'}

