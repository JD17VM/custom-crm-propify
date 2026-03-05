from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from markupsafe import Markup


from . import chatwoot_api
from . import chatwoot_sync
import os

_logger = logging.getLogger(__name__)

class CustomLead(models.Model):
    _inherit = 'crm.lead'

    id_externo = fields.Char(string='ID Transacción')
    metodo_contacto = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Otro')
    ], string='Método de Contacto')

    canal = fields.Selection([
        ('whatsapp_1', 'Whatsapp 1'),
        ('whatsapp_2', 'Whatsapp 2'),
        ('messenger', 'Messenger'),
        ('instagram', 'Instagram'),

        ('manual', 'Manual'),
    ], string="Canal", default='manual')

    canal_icon_html = fields.Html(
        string='Ícono del Canal',
        compute='_compute_canal_icon_html',
        sanitize=False,
        store=False
    )

    @api.depends('canal')
    def _compute_canal_icon_html(self):
        
        icon_map = {
            'whatsapp_1': '/custom_crm_propify/static/src/img/whatsapp-logo_num_1.png',
            'whatsapp_2': '/custom_crm_propify/static/src/img/whatsapp-logo_num_2.png',
            
            
            'messenger': '/custom_crm_propify/static/src/img/facebook-logo.png',
            'instagram': '/custom_crm_propify/static/src/img/instagram-logo.png',
            'manual': '/custom_crm_propify/static/src/img/notas-manuales-logo.png',

            
        }
        
        for record in self:
            if record.canal and record.canal in icon_map:
                record.canal_icon_html = f'''
                    <img src="{icon_map[record.canal]}" 
                         alt="{record.canal}"/>
                '''
            else:
                record.canal_icon_html = ''


    es_activo_propify_bot = fields.Boolean(
        string="Propibot IA", 
        default=True  
    )

    id_conversacion = fields.Integer(string="ID Conversación", index=True)

    tipo = fields.Selection([
        ('compra', 'Compra'),
        ('venta', 'Venta'),
    ], string="Tipo de Lead")

    ubicacion = fields.Text(string="Ubicación")
    requerimientos = fields.Text(string="Requerimientos")

    ultimo_autor_mensaje = fields.Char(string="Autor Último Mensaje")
    ultima_fecha_mensaje = fields.Datetime(string="Hora Último Mensaje")

    ultimo_autor_tipo = fields.Selection([
        ('visitor', 'Cliente'),
        ('agent', 'Agente'),
        ('bot', 'Bot'),
    ], string="Tipo Autor Último Mensaje", default='visitor')

    ultimo_autor_icon_html = fields.Html(
        string='Icono Autor',
        compute='_compute_ultimo_autor_icon_html',
        sanitize=False,
        store=False
    )

    @api.depends('ultimo_autor_tipo')
    def _compute_ultimo_autor_icon_html(self):
        for record in self:
            tipo = record.ultimo_autor_tipo or 'visitor'

            if tipo == 'visitor':
                record.ultimo_autor_icon_html = Markup(
                    '<img src="/custom_crm_propify/static/src/img/visitor.png" '
                    'style="width:100%; height:100%; object-fit:contain;" '
                    'alt="Cliente" title="Cliente"/>'
                )

            elif tipo == 'bot':
                record.ultimo_autor_icon_html = Markup(
                    '<img src="/custom_crm_propify/static/src/img/bot.png" '
                    'style="width:100%; height:100%; object-fit:contain;" '
                    'alt="Bot" title="Bot"/>'
                )

            elif tipo == 'agent':
                record.ultimo_autor_icon_html = Markup(
                    '<img src="/custom_crm_propify/static/src/img/agent.png" '
                    'style="width:100%; height:100%; object-fit:contain;" '
                    'alt="Agente" title="Agente"/>'
                )

            else:
                
                record.ultimo_autor_icon_html = Markup(
                    '<img src="/custom_crm_propify/static/src/img/visitor.pgm" '
                    'style="width:100%; height:100%; object-fit:contain;" '
                    'alt="Desconocido" title="Tipo desconocido"/>'
                )


    prompt_id = fields.Many2one('crm.prompt', string="Pieza de Conocimiento")

    @api.model
    def desactivar_propibot(self, lead_id):
        """
        Endpoint para desactivar el bot de IA en un lead específico desde n8n/API.
        """
        try:
            lead_id = int(lead_id)
            lead = self.browse(lead_id)
            if lead.exists():
                lead.es_activo_propify_bot = False
                return {'success': True, 'message': f'Bot desactivado para Lead {lead_id}'}
            return {'success': False, 'message': f'Lead {lead_id} no encontrado'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @api.model
    def check_propibot_status(self, lead_id):
        """
        Endpoint seguro para consultar el estado del bot.
        Retorna un diccionario con claves fijas para evitar errores de posición en n8n.
        """
        try:
            lead_id = int(lead_id)
            lead = self.browse(lead_id)
            if lead.exists():
                return {
                    'success': True,
                    'es_activo_propify_bot': lead.es_activo_propify_bot,
                    'lead_id': lead.id
                }
            return {'success': False, 'message': f'Lead {lead_id} no encontrado', 'es_activo_propify_bot': False}
        except Exception as e:
            return {'success': False, 'message': str(e), 'es_activo_propify_bot': False}

    @api.model
    def get_leads_with_bot_disabled(self):
        """
        Endpoint para obtener todos los leads que tienen el bot desactivado.
        Retorna: Lista de diccionarios con {lead_id, name, id_conversacion}
        """
        try:
            
            leads = self.search([('es_activo_propify_bot', '=', False)])
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            
            result = []
            for lead in leads:
                
                lead_url = f"{base_url}/web

                result.append({
                    'lead_id': lead.id,
                    'name': lead.name or 'Sin nombre',
                    'id_conversacion': lead.id_conversacion or 0,
                    'odoo_link': lead_url,
                    'stage_id': lead.stage_id.id,
                    'stage_name': lead.stage_id.name or '',
                    'is_not_interested': lead.stage_id.id == 5
                })
                
            return {
                'success': True,
                'count': len(result),
                'leads': result
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'leads': []
            }

    @api.model
    def get_leads_stats_by_user(self):
        """
        Retorna estadísticas de leads asignados por usuario y tipo (Venta, Compra, Nada).
        """
        
        
        groups = self.read_group(
            domain=[], 
            fields=['user_id', 'tipo'], 
            groupby=['user_id', 'tipo'], 
            lazy=False
        )
        
        stats = {}
        
        for group in groups:
            user_tuple = group.get('user_id')
            
            
            if not user_tuple:
                user_id = 0
                user_name = "Sin Asignar"
            else:
                user_id = user_tuple[0]
                user_name = user_tuple[1]
                
            if user_id not in stats:
                stats[user_id] = {'user_id': user_id, 'user_name': user_name, 'total': 0, 'venta': 0, 'compra': 0, 'sin_tipo': 0}
            
            count = group.get('__count', 0)
            tipo = group.get('tipo')
            
            stats[user_id]['total'] += count
            
            if tipo == 'venta':
                stats[user_id]['venta'] += count
            elif tipo == 'compra':
                stats[user_id]['compra'] += count
            else:
                stats[user_id]['sin_tipo'] += count
                
        return list(stats.values())

    @api.model
    def get_openai_api_key(self):
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        return {
            'success': True,
            'api_key': api_key
        }

    def action_reload_view(self):
        """
        Acción para refrescar la vista actual sin recargar la página completa (F5).
        Útil para ver cambios hechos por automatizaciones (n8n) o compañeros.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    
    
    

    @api.model_create_multi
    def create(self, vals_list):
        """
        SOBREESCRITO: Al crear, si ya viene el 'tipo', lo movemos al pipeline correcto.
        Soporta creación masiva (listas) y única, ideal para integraciones con n8n.
        """
        for vals in vals_list:
            pass

        leads = super(CustomLead, self).create(vals_list)
        
        for lead in leads:
            if lead.tipo:
                lead.action_redistribute_lead_by_type()
        return leads

    def write(self, vals):
        """
        SOBREESCRITO:
        Detecta cuando cambia el vendedor ('user_id') y sincroniza la
        asignación con Chatwoot.
        """
        result = super(CustomLead, self).write(vals)
        
        
        if 'user_id' in vals:
            for record in self.sudo():
                _logger.info(f"Cambio de vendedor detectado en Lead {record.id}. Sincronizando con Chatwoot...")
                sync_result = chatwoot_sync.sync_assignment_to_chatwoot(
                    lead=record,
                    new_user=record.user_id
                )
                record._notify_sync_result(sync_result)
        
        
        if 'tipo' in vals:
            self.action_redistribute_lead_by_type()

        
        
        if 'stage_id' in vals:
            for record in self:
                
                if record.stage_id.name == 'Lead Entrante':
                    team_principal = self.env['crm.team'].search(['|', ('name', '=', 'Principal (Recepción)'), ('name', '=', 'Ventas')], limit=1)
                    if team_principal and record.team_id.id != team_principal.id:
                        _logger.info(f"🔧 Auto-corrigiendo equipo para Lead {record.id} (Lead Entrante -> Principal)")
                        record.write({'team_id': team_principal.id})
        
        return result

    def _notify_sync_result(self, result):
        """
        Muestra un mensaje claro en el chatter sobre el resultado de la sincronización.
        """
        self.ensure_one()
        
        if result.get('success'):
            
            if result.get('agent_id'):
                
                body = Markup(
                    f"<b>✅ Asignación sincronizada con Chatwoot</b><br/>"
                    f"<strong>Vendedor:</strong> {self.user_id.name}<br/>"
                    f"<strong>ID Conversación:</strong> {self.id_conversacion}<br/>"
                    f"<strong>ID Agente Chatwoot:</strong> {result['agent_id']}"
                )
            else:
                
                body = Markup(f"ℹ️ <b>Sincronización Chatwoot:</b> {result.get('message', 'Operación completada.')}")
        else:
            
            if result.get('found_agent'):
                icon = "⚠️"
                title = "Error de asignación en Chatwoot"
            else:
                icon = "❌"
                title = "Error crítico de sincronización"
            
            error_msg = result.get('message', 'Error desconocido.')

            body = Markup(
                f"<b>{icon} {title}</b><br/>"
                f"<strong>Error:</strong> {error_msg}<br/><br/>"
                f"<strong>Detalles del intento:</strong><br/>"
                f"<strong>Vendedor:</strong> {self.user_id.name if self.user_id else 'Sin asignar'}<br/>"
                f"<strong>Email:</strong> {self.user_id.email if self.user_id and self.user_id.email else 'No configurado'}<br/>"
                f"<strong>ID Conversación:</strong> {self.id_conversacion or 'No disponible'}"
            )

        self.message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_note'
        )

    

    def test_chatwoot_connection(self):
        """
        Botón para probar la conexión con Chatwoot usando la configuración
        centralizada en `chatwoot_api.py`.
        """
        chatwoot_api.check_connection()

    def test_manual_sync(self):
        """
        Botón para forzar una sincronización manual del lead actual.
        Útil para probar si una asignación específica funciona.
        """
        self.ensure_one()
        _logger.info(f"🧪 Forzando sincronización manual para Lead {self.id}")
        
        if not self.user_id:
            raise UserError("❌ Este lead no tiene vendedor asignado. No se puede sincronizar.")
        
        if not self.id_conversacion:
            raise UserError("❌ Este lead no tiene ID de conversación de Chatwoot.")
        
        
        sync_result = chatwoot_sync.sync_assignment_to_chatwoot(
            lead=self,
            new_user=self.user_id
        )
        
        
        self._notify_sync_result(sync_result)
        
        
        raise UserError(f"✅ Prueba de sincronización completada.\n\n{sync_result['message']}\n\nRevisa el chatter para ver los detalles.")

    def diagnostico_completo_lead(self):
        """
        Botón para ejecutar un diagnóstico completo y descubrir por qué
        una asignación podría estar fallando.
        """
        self.ensure_one()
        
        if not self.user_id or not self.user_id.email:
            raise UserError("❌ No se puede diagnosticar. El vendedor asignado no tiene un email configurado en Odoo.")
        
        if not self.id_conversacion:
            raise UserError("❌ No se puede diagnosticar. Este lead no tiene un ID de conversación de Chatwoot.")
        
        resultado = chatwoot_api.diagnostico_completo_conversacion(
            conversation_id=self.id_conversacion,
            agent_email=self.user_id.email
        )
        
        
        if resultado.get('soluciones'):
            resumen = "❌ PROBLEMAS ENCONTRADOS"
            detalle = "\n".join([f"• {p}" for p in resultado['problemas']])
            solucion = "\n\n💡 SOLUCIÓN:\n" + "\n".join([f"• {s}" for s in resultado['soluciones']])
        else:
            resumen = "✅ TODO CORRECTO"
            detalle = "No se detectaron problemas de configuración. La asignación debería funcionar."
            solucion = ""
        
        raise UserError(f"{resumen}\n\n{detalle}{solucion}")

    def action_list_chatwoot_agents(self):
        """
        Botón para listar los agentes de Chatwoot y facilitar la corrección de emails.
        """
        agents = chatwoot_api.list_agents()
        
        if not agents:
            raise UserError("❌ No se pudieron obtener agentes de Chatwoot.\n\nVerifica que la conexión sea correcta usando el botón de diagnóstico.")
            
        msg = "📋 AGENTES ENCONTRADOS EN CHATWOOT\n"
        msg += "====================================\n\n"
        
        for agent in agents:
            email = agent.get('email', '')
            name = agent.get('name', 'Sin Nombre')
            
            msg += f"👤 {name}\n"
            msg += f"   📧 {email}\n"
            msg += f"   🆔 ID: {agent.get('id')} ({agent.get('role')})\n"
            
            if email:
                odoo_user = self.env['res.users'].search([('email', '=ilike', email)], limit=1)
                if odoo_user:
                    msg += f"   ✅ MATCH ODOO: Vinculado al usuario '{odoo_user.name}'\n"
                else:
                    msg += f"   ❌ SIN MATCH: Ningún usuario en Odoo tiene este email.\n"
            
            msg += "------------------------------------\n"
            
        raise UserError(msg)

    def action_open_chatwoot_conversation(self):
        """
        Botón 'Abrir Chat' que abre la conversación de Chatwoot en una nueva pestaña.
        """
        self.ensure_one()
        
        if not self.id_conversacion:
            raise UserError("Este lead no tiene un ID de conversación de Chatwoot.")
        
        
        url = f"{chatwoot_api.CHATWOOT_URL}/app/accounts/{chatwoot_api.CHATWOOT_ACCOUNT_ID}/conversations/{self.id_conversacion}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    
    
    

    def action_move_to_compradores(self):
        """ Mueve el lead al equipo Compradores y resetea su etapa """
        self.ensure_one()
        
        
        team = self.env.ref('custom_crm_propify.crm_team_propify_owners', raise_if_not_found=False)
        if not team:
            
            team = self.env['crm.team'].search([('name', '=', 'Compradores')], limit=1)
        
        
        stage = self.env['crm.stage'].search([('team_ids', 'in', [team.id])], order='sequence asc', limit=1)
        
        vals = {'team_id': team.id}
        if stage:
            vals['stage_id'] = stage.id
            
        self.write(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Movido a Compradores!',
                'message': 'El lead ahora está en el embudo de Compradores.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_move_to_propietarios(self):
        """ Mueve el lead al equipo Propietarios y resetea su etapa """
        self.ensure_one()
        
        
        team = self.env.ref('custom_crm_propify.crm_team_propify_custom', raise_if_not_found=False)
        if not team:
            
            team = self.env['crm.team'].search([('name', '=', 'Propietarios')], limit=1)
        
        
        stage = self.env['crm.stage'].search([('team_ids', 'in', [team.id])], order='sequence asc', limit=1)
        
        vals = {'team_id': team.id}
        if stage:
            vals['stage_id'] = stage.id
            
        self.write(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Movido a Propietarios!',
                'message': 'El lead ahora está en el embudo de Propietarios.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_redistribute_lead_by_type(self):
        """
        Método para ser llamado desde n8n o automatizaciones.
        Lee el campo 'tipo' y mueve el lead al pipeline correspondiente.
        """
        for lead in self:
            if not lead.tipo:
                
                continue
            
            if lead.tipo == 'compra':
                lead.action_move_to_compradores()
            elif lead.tipo == 'venta':
                lead.action_move_to_propietarios()
        return True

    @api.model
    def action_tool_migrate_principal_to_compradores(self):
        """
        Herramienta de migración para mover etapas y leads del equipo Principal al de Compradores
        sin perder la posición de los leads.
        """
        
        team_principal = self.env['crm.team'].search(['|', ('name', '=', 'Principal (Recepción)'), ('name', '=', 'Ventas')], limit=1)
        
        
        team_compradores = self.env.ref('custom_crm_propify.crm_team_propify_owners', raise_if_not_found=False)
        if not team_compradores:
            team_compradores = self.env['crm.team'].search([('name', '=', 'Compradores')], limit=1)

        if not team_principal or not team_compradores:
            raise UserError("Error: No se encontraron los equipos 'Principal (Recepción)' o 'Compradores'.")

        
        
        etapas_fijas = ['Nuevo', 'No Interesado', 'New', 'Not Interested', 'No interesado', 'nuevo']

        
        etapas = self.env['crm.stage'].search([('team_ids', 'in', [team_principal.id])])

        log = []
        leads_movidos_total = 0

        for stage in etapas:
            
            if stage.name == 'Lead Entrante':
                continue

            
            if stage.name in etapas_fijas:
                if team_compradores.id not in stage.team_ids.ids:
                    stage.write({'team_ids': [(4, team_compradores.id)]})
                    log.append(f"✅ Etapa '{stage.name}': Ahora compartida con Compradores.")
                continue

            
            
            leads = self.env['crm.lead'].search([
                ('stage_id', '=', stage.id),
                ('team_id', '=', team_principal.id)
            ])
            
            if leads:
                
                
                leads.write({'team_id': team_compradores.id})
                leads_movidos_total += len(leads)
                log.append(f"📦 Leads: {len(leads)} leads en '{stage.name}' pasados a Compradores.")

            
            stage.write({
                'team_ids': [
                    (4, team_compradores.id), 
                    (3, team_principal.id)    
                ]
            })
            log.append(f"🚚 Etapa '{stage.name}': Movida a Compradores.")

        
        
        mensaje = f"MIGRACIÓN COMPLETADA. Leads movidos: {leads_movidos_total}"
        _logger.info(mensaje + "\n" + "\n".join(log))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Migración Exitosa',
                'message': f"{mensaje}. (Revisa el log del servidor para más detalles)",
                'type': 'success',
                'sticky': True,
            }
        }

    
    
    def action_fix_prop_2_stage(self):
        """
        Método dummy para evitar error de validación de vista si el botón aún existe en el XML.
        """
        return True

    def action_diagnose_prop_2_anomaly(self):
        """
        Método dummy para evitar error de validación de vista.
        """
        return True

    def action_diagnose_ai_config(self):
        """
        Botón de diagnóstico para verificar qué configuración de IA se está detectando
        para cada tipo de flujo (Venta, Compra, Principal).
        """
        
        configs = self.env['crm.ai.config'].search([])
        
        msg = f"🔍 DIAGNÓSTICO DE CONFIGURACIÓN IA\n"
        msg += f"================================\n"
        msg += f"📂 Registros encontrados en BD: {len(configs)}\n"
        
        if not configs:
            msg += "❌ NO HAY REGISTROS. Debes crear al menos uno en Configuración > Prompts IA.\n"
        else:
            for c in configs:
                msg += f"- ID {c.id}: '{c.name}' -> Tipo: {c.tipo}\n"
        
        msg += f"\n🧪 SIMULACIÓN DE RESPUESTAS (Lo que recibe n8n):\n"
        msg += f"--------------------------------\n"
        
        prompt_model = self.env['crm.prompt']
        
        
        res_venta = prompt_model.get_all_prompts_json(tipo_flujo='venta')
        p_venta = res_venta.get('prompt', '')
        msg += f"1. Si n8n pide 'venta'     -> {p_venta[:40]}... ({'✅ OK' if p_venta else '⚠️ VACÍO'})\n"
        
        
        res_compra = prompt_model.get_all_prompts_json(tipo_flujo='compra')
        p_compra = res_compra.get('prompt', '')
        msg += f"2. Si n8n pide 'compra'    -> {p_compra[:40]}... ({'✅ OK' if p_compra else '⚠️ VACÍO'})\n"
        
        
        res_principal = prompt_model.get_all_prompts_json(tipo_flujo='principal')
        p_principal = res_principal.get('prompt', '')
        msg += f"3. Si n8n pide 'principal' -> {p_principal[:40]}... ({'✅ OK' if p_principal else '⚠️ VACÍO'})\n"
        
        raise UserError(msg)

    def action_fix_ai_config_duplicates(self):
        """
        Repara la configuración de IA:
        1. Elimina duplicados de tipo 'principal'.
        2. Crea registros para 'venta' y 'compra' si no existen.
        3. Asegura que solo haya 1 de cada tipo.
        """
        Config = self.env['crm.ai.config']
        log = []

        
        principales = Config.search([('tipo', '=', 'principal')], order='id asc')
        if len(principales) > 1:
            
            primero = principales[0]
            resto = principales[1:]
            resto.unlink()
            log.append(f"✅ Se eliminaron {len(resto)} configuraciones 'Principal' duplicadas.")
            primero.name = 'Configuración Principal'
        elif not principales:
            Config.create({'name': 'Configuración Principal', 'tipo': 'principal'})
            log.append("✅ Se creó la configuración 'Principal'.")

        
        ventas = Config.search([('tipo', '=', 'venta')])
        if not ventas:
            Config.create({
                'name': 'Configuración Venta (Propietarios)', 
                'tipo': 'venta',
                'prompt_principal': 'Eres un experto inmobiliario ayudando a propietarios...'
            })
            log.append("✅ Se creó la configuración 'Venta'.")
        elif len(ventas) > 1:
            ventas[1:].unlink()
            log.append("✅ Se eliminaron configuraciones 'Venta' duplicadas.")

        
        compras = Config.search([('tipo', '=', 'compra')])
        if not compras:
            Config.create({
                'name': 'Configuración Compra (Compradores)', 
                'tipo': 'compra',
                'prompt_principal': 'Eres un experto inmobiliario ayudando a compradores...'
            })
            log.append("✅ Se creó la configuración 'Compra'.")
        elif len(compras) > 1:
            compras[1:].unlink()
            log.append("✅ Se eliminaron configuraciones 'Compra' duplicadas.")

        if not log:
            log.append("Todo estaba correcto. No se hicieron cambios.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Configuración IA Reparada',
                'message': '\n'.join(log),
                'type': 'success',
                'sticky': True,
            }
        }

    def action_emergency_fix_pipelines(self):
        """
        CORRECCIÓN DE EMERGENCIA (VERSIÓN 2 - FUERZA BRUTA):
        1. Fuerza nombres de equipos.
        2. Fuerza asignación de etapas a equipos (crucial para que se muevan visualmente).
        3. Mueve leads por tipo.
        """
        
        
        team_owners_real = self.env.ref('custom_crm_propify.crm_team_propify_custom', raise_if_not_found=False)
        
        team_buyers_real = self.env.ref('custom_crm_propify.crm_team_propify_owners', raise_if_not_found=False)

        if not team_owners_real or not team_buyers_real:
            raise UserError("No se encontraron los equipos. Asegúrate de actualizar el módulo primero.")

        log = []

        
        if team_owners_real.name != 'Propietarios':
            team_owners_real.name = 'Propietarios'
            log.append("✅ Equipo 'Custom' renombrado a 'Propietarios'.")
        
        if team_buyers_real.name != 'Compradores':
            team_buyers_real.name = 'Compradores'
            log.append("✅ Equipo 'Owners' renombrado a 'Compradores'.")

        
        
        stages_owners_data = []
        
        for xml_id, name in stages_owners_data:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                updates = {}
                if stage.name != name:
                    updates['name'] = name
                
                
                
                if team_owners_real.id not in stage.team_ids.ids or len(stage.team_ids) > 1:
                    updates['team_ids'] = [(6, 0, [team_owners_real.id])]
                
                if updates:
                    stage.write(updates)
                    log.append(f"✅ Etapa '{name}' asignada correctamente a Propietarios.")

        
        stages_buyers_data = [
            ('custom_crm_propify.stage_propify_owners_1', 'Interesado en compra'),
            ('custom_crm_propify.stage_propify_owners_2', 'Visita Agendada'),
            ('custom_crm_propify.stage_propify_owners_3', 'Requerimiento definido'),
            ('custom_crm_propify.stage_propify_owners_4', 'En visitas'),
            ('custom_crm_propify.stage_propify_owners_5', 'Propuesta/Negociación'),
            ('custom_crm_propify.stage_propify_owners_6', 'Propuesta aceptada/Documentos'),
            ('custom_crm_propify.stage_propify_owners_7', 'Compra realizada'),
            ('custom_crm_propify.stage_propify_owners_8', 'Seguimiento activo')
        ]

        for xml_id, name in stages_buyers_data:
            stage = self.env.ref(xml_id, raise_if_not_found=False)
            if stage:
                updates = {}
                if stage.name != name:
                    updates['name'] = name
                
                
                if team_buyers_real.id not in stage.team_ids.ids or len(stage.team_ids) > 1:
                    updates['team_ids'] = [(6, 0, [team_buyers_real.id])]
                
                if updates:
                    stage.write(updates)
                    log.append(f"✅ Etapa '{name}' asignada correctamente a Compradores.")

        
        
        leads_venta_mal = self.env['crm.lead'].search([
            ('tipo', '=', 'venta'),
            ('team_id', '!=', team_owners_real.id)
        ])
        if leads_venta_mal:
            leads_venta_mal.write({'team_id': team_owners_real.id})
            log.append(f"📦 {len(leads_venta_mal)} leads de VENTA movidos a Propietarios.")

        
        leads_compra_mal = self.env['crm.lead'].search([
            ('tipo', '=', 'compra'),
            ('team_id', '!=', team_buyers_real.id)
        ])
        if leads_compra_mal:
            leads_compra_mal.write({'team_id': team_buyers_real.id})
            log.append(f"📦 {len(leads_compra_mal)} leads de COMPRA movidos a Compradores.")

        
        if not log:
            log.append("Todo estaba correcto. No se hicieron cambios.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Corrección Total Ejecutada',
                'message': '\n'.join(log),
                'type': 'success',
                'sticky': True,
            }
        }

    def action_fix_lead_entrante_stage(self):
        """
        Acción para corregir la etapa 'Lead Entrante' que aparece duplicada o global.
        Le asigna explícitamente el equipo 'Principal (Recepción)' para que no salga en otros lados.
        """
        
        stage = self.env['crm.stage'].search([('name', '=', 'Lead Entrante')], limit=1)
        if not stage:
            
            stage = self.env['crm.stage'].search([('name', '=', 'Nuevo')], limit=1)
        
        if not stage:
            raise UserError("No se encontró ninguna etapa llamada 'Lead Entrante' o 'Nuevo'.")

        
        team_principal = self.env['crm.team'].search(['|', ('name', '=', 'Principal (Recepción)'), ('name', '=', 'Ventas')], limit=1)
        if not team_principal:
            raise UserError("No se encontró el equipo 'Principal (Recepción)'.")

        
        
        leads_desubicados = self.env['crm.lead'].search([
            ('stage_id', '=', stage.id),
            ('team_id', '!=', team_principal.id)
        ])
        cantidad_movida = len(leads_desubicados)
        if leads_desubicados:
            leads_desubicados.write({'team_id': team_principal.id})

        
        stage.write({'team_ids': [(6, 0, [team_principal.id])]})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '¡Etapa Corregida!',
                'message': f"La etapa '{stage.name}' ahora es exclusiva del equipo '{team_principal.name}'.\nSe movieron {cantidad_movida} leads al equipo Principal.",
                'type': 'success',
                'sticky': True,
            }
        }