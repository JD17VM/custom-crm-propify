from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CrmAiConfig(models.Model):
    _name = 'crm.ai.config'
    _description = 'Configuración IA (Prompt Global)'

    name = fields.Char(string='Nombre', default='Configuración Principal', required=True)
    
    tipo = fields.Selection([
        ('principal', 'Principal / Global'),
        ('venta', 'Flujo Venta (Propietarios)'),
        ('compra', 'Flujo Compra (Compradores)')
    ], string="Tipo de Flujo", default='principal', required=True, help="Define para qué flujo se usará este prompt.")

    prompt_principal = fields.Text(string='Instrucciones del Prompt', help="Escribe aquí el prompt para este flujo específico.")
    
    respuestas_recomendadas = fields.Text(string='Respuestas Recomendadas (Global)', help="Texto con las respuestas sugeridas generales.")
    instrucciones_finales = fields.Text(string='Instrucciones Finales (Global)', help="Instrucciones generales que aplican al final del proceso.")

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    instrucciones_ia = fields.Text(string="Instrucciones IA", help="Instrucciones específicas para la IA en esta etapa.")

    def write(self, vals):
        """
        SOBREESCRIBIR: Guardián de Integridad.
        Impide que las etapas críticas se muevan de equipo accidentalmente.
        """
        # 1. Ejecutar el cambio solicitado normalmente
        res = super(CrmStage, self).write(vals)
        
        # 2. VERIFICACIÓN Y AUTO-CORRECCIÓN INMEDIATA
        for stage in self:
            # CASO B: 'Lead Entrante' debe ser SIEMPRE de Principal
            if stage.name == 'Lead Entrante':
                team_principal = self.env['crm.team'].search(['|', ('name', '=', 'Principal (Recepción)'), ('name', '=', 'Ventas')], limit=1)
                # Si el equipo no es Principal...
                if team_principal and (len(stage.team_ids) != 1 or team_principal.id not in stage.team_ids.ids):
                    _logger.info(f"🛡️ GUARDIÁN: Bloqueando intento de mover 'Lead Entrante'. Restaurando a Principal.")
                    super(CrmStage, stage).write({'team_ids': [(6, 0, [team_principal.id])]})
        
        return res

class CrmPrompt(models.Model):
    _name = 'crm.prompt'
    _description = 'Pieza de Conocimiento (Prompt)'
    _rec_name = 'name'

    name = fields.Char(string='Título del Prompt', required=True)
    contenido = fields.Text(string='Pieza de Conocimiento', required=True)
    active = fields.Boolean(string="Activo", default=True)

    @api.model
    def get_all_prompts_json(self, tipo_flujo=False):
        """
        Retorna un JSON con 3 campos separados:
        1. piezas_de_conocimiento: Lista de todas las piezas.
        2. prompt: El prompt específico según el flujo (Venta, Compra o Principal).
        3. respuestas_recomendadas: Las respuestas únicas globales.
        4. etapas: Lista de etapas filtradas por el flujo solicitado.
        """
        # 1. Obtener todas las piezas de conocimiento
        prompts = self.search([])
        piezas_list = [{'id': p.id, 'titulo': p.name, 'contenido': p.contenido or ""} for p in prompts]

        # 2. Obtener la configuración global. Se usa .sudo() para que la llamada
        # desde la API (n8n) pueda leer la configuración sin importar los
        # permisos del usuario de la API, que por defecto son restringidos.
        
        # LÓGICA MULTI-REGISTRO: Buscamos el registro específico según el tipo
        domain_config = [('tipo', '=', 'principal')] # Por defecto buscamos el principal
        
        if tipo_flujo == 'venta':
            domain_config = [('tipo', '=', 'venta')]
        elif tipo_flujo == 'compra':
            domain_config = [('tipo', '=', 'compra')]
            
        # Buscamos la configuración específica
        config = self.env['crm.ai.config'].sudo().search(domain_config, limit=1)
        
        # Si no encuentra la específica (ej. no creaste la de venta), busca la principal como respaldo
        if not config and tipo_flujo in ['venta', 'compra']:
            config = self.env['crm.ai.config'].sudo().search([('tipo', '=', 'principal')], limit=1)
        
        prompt_sistema = ""
        respuestas = ""
        instrucciones_finales = ""
        
        if config:
            respuestas = config.respuestas_recomendadas or ""
            instrucciones_finales = config.instrucciones_finales or ""
            # Ahora el prompt siempre está en el campo 'prompt_principal' del registro encontrado
            prompt_sistema = config.prompt_principal or ""

        # 3. Obtener configuración de etapas (FILTRADAS POR EQUIPO)
        domain = [('name', '!=', 'Nuevo')] # Mantenemos la exclusión de 'Nuevo' si así estaba
        
        if tipo_flujo == 'venta':
            # Equipo Propietarios
            team = self.env.ref('custom_crm_propify.crm_team_propify_custom', raise_if_not_found=False)
            if team:
                domain.append(('team_ids', 'in', [team.id]))
                
        elif tipo_flujo == 'compra':
            # Equipo Compradores
            team = self.env.ref('custom_crm_propify.crm_team_propify_owners', raise_if_not_found=False)
            if team:
                domain.append(('team_ids', 'in', [team.id]))
                
        else: # Principal (o si no se especifica flujo)
            team = self.env['crm.team'].search(['|', ('name', '=', 'Principal (Recepción)'), ('name', '=', 'Ventas')], limit=1)
            if team:
                domain.append(('team_ids', 'in', [team.id]))

        stages = self.env['crm.stage'].sudo().search(domain, order='sequence')
        etapas_list = [{'id': s.id, 'name': s.name, 'instrucciones': s.instrucciones_ia or ""} for s in stages]

        # 4. Obtener Propiedades (Inventario)
        # Enviamos SIEMPRE las propiedades para que la IA tenga contexto del inventario
        # independientemente de si el flujo dice 'compra' o no.
        props = self.env['crm.property'].sudo().search([])
        propiedades_list = [{
            'id': p.id,
            'nombre': p.name,
            'descripcion': p.description or "",
            'mensaje_captacion': p.mensaje_captacion or ""
        } for p in props]

        return {
            'piezas_de_conocimiento': piezas_list,
            'prompt': prompt_sistema,
            'respuestas_recomendadas': respuestas,
            'etapas': etapas_list,
            'instrucciones_finales': instrucciones_finales,
            'propiedades': propiedades_list
        }

class CrmProperty(models.Model):
    _name = 'crm.property'
    _description = 'Propiedad Inmobiliaria'

    name = fields.Char(string='Nombre de la Propiedad', required=True)
    description = fields.Text(string='Descripción')
    mensaje_captacion = fields.Text(string='Mensaje de Recepción', 
                                    help="Copia aquí el mensaje predeterminado con el que llega el lead desde el anuncio (ej. 'Hola, vi esto en Facebook...').")