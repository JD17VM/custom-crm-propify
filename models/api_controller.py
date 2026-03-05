from odoo import http
from odoo.http import request
import json

class PropifyController(http.Controller):
    
    @http.route('/api/leads/bot-disabled', type='http', auth='user', methods=['GET'], csrf=False)
    def list_leads_bot_disabled(self, **kwargs):
        """
        URL Directa para ver leads con bot desactivado.
        Acceso: Requiere estar logueado en Odoo (auth='user').
        Ruta: /api/leads/bot-disabled
        """
        # Reutilizamos la lógica que ya creamos en el modelo crm.lead
        result = request.env['crm.lead'].get_leads_with_bot_disabled()
        
        # Devolvemos un JSON formateado para que sea fácil de leer en el navegador
        return request.make_response(
            json.dumps(result, indent=4, ensure_ascii=False),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )

    @http.route('/api/leads/stats-by-user', type='http', auth='user', methods=['GET'], csrf=False)
    def get_leads_stats_by_user(self, **kwargs):
        """
        Retorna JSON con conteo de leads por vendedor y desglose por tipo (Venta/Compra/Nada).
        Ruta: /api/leads/stats-by-user
        """
        result = request.env['crm.lead'].get_leads_stats_by_user()
        
        return request.make_response(
            json.dumps({'success': True, 'data': result}, indent=4, ensure_ascii=False),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )