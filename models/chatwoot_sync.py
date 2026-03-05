"""
Módulo de sincronización entre Odoo CRM y Chatwoot.
"""

import logging
from . import chatwoot_api

_logger = logging.getLogger(__name__)


def sync_assignment_to_chatwoot(lead, new_user):
    """
    Sincroniza la asignación de un vendedor de Odoo a Chatwoot.
    
    Args:
        lead: Objeto crm.lead de Odoo
        new_user: Usuario (vendedor) recién asignado
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'found_agent': bool,
            'agent_id': int or None
        }
    """
    _logger.info(f"🔄 Iniciando sincronización para Lead {lead.id}")
    
    # Validación 1: ¿Tiene ID de conversación?
    if not lead.id_conversacion:
        _logger.warning(f"Lead {lead.id} no tiene ID de conversación")
        return {
            'success': False,
            'message': 'Este lead no tiene ID de conversación de Chatwoot.',
            'found_agent': False,
            'agent_id': None
        }
    
    # Validación 2: ¿Tiene vendedor asignado?
    if not new_user:
        _logger.info(f"Lead {lead.id} fue desasignado (sin vendedor)")
        # No es un error, simplemente no hay nada que sincronizar.
        return {
            'success': True,
            'message': 'El lead fue desasignado. No se sincroniza con Chatwoot.',
            'found_agent': False,
            'agent_id': None
        }
    
    # Validación 3: ¿El vendedor tiene email?
    if not new_user.email:
        _logger.error(f"Vendedor {new_user.name} no tiene email configurado")
        return {
            'success': False,
            'message': f"El vendedor '{new_user.name}' no tiene email configurado en Odoo.",
            'found_agent': False,
            'agent_id': None
        }
    
    # Paso 1: Buscar agente en Chatwoot
    _logger.info(f"🔍 Buscando agente con email: {new_user.email}")
    agent_id = chatwoot_api.get_agent_by_email(new_user.email)
    
    if not agent_id:
        _logger.error(f"❌ No se encontró agente con email: {new_user.email}")
        return {
            'success': False,
            'message': f"No se encontró un agente en Chatwoot con el email '{new_user.email}'.",
            'found_agent': False,
            'agent_id': None
        }
    
    _logger.info(f"✓ Agente encontrado - ID: {agent_id}")
    
    # Paso 2: Asignar conversación
    _logger.info(f"📞 Asignando conversación {lead.id_conversacion} al agente {agent_id}")
    success = chatwoot_api.assign_conversation_to_agent(lead.id_conversacion, agent_id)
    
    if success:
        _logger.info(f"✅ Asignación exitosa")
        return {
            'success': True,
            'message': f"Conversación asignada exitosamente a '{new_user.name}' en Chatwoot.",
            'found_agent': True,
            'agent_id': agent_id
        }
    else:
        _logger.error(f"❌ Error al asignar conversación")
        # Aquí podría haber un problema de permisos del agente en la inbox.
        return {
            'success': False,
            'message': 'Error al asignar la conversación en Chatwoot. Posiblemente el agente no tiene acceso a la inbox del chat.',
            'found_agent': True,
            'agent_id': agent_id
        }