import requests
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# --- .Configuración Centralizada de Chatwoot ---
# URL y Token para el CRM de Propify
CHATWOOT_URL = "https://n8n-propify-chatwoot.qqaetr.easypanel.host"
CHATWOOT_API_TOKEN = "6CFQrb6P4f7hfbZ6ieFsPzkr"
# Este ID se puede encontrar en la URL de Chatwoot: /app/accounts/X/...
# La herramienta de diagnóstico lo puede detectar automáticamente si es incorrecto.
CHATWOOT_ACCOUNT_ID = 2

def _get_headers():
    """Crea los encabezados de autenticación para la API de Chatwoot."""
    return {
        'Content-Type': 'application/json',
        'api_access_token': CHATWOOT_API_TOKEN
    }


def _auto_detect_account_id():
    """
    Intenta detectar automáticamente el Account ID correcto.
    Prueba con IDs del 1 al 10.
    Retorna el primer ID que funcione, o None si ninguno funciona.
    """
    headers = _get_headers()
    
    for account_id in range(1, 11):
        try:
            test_url = f"{CHATWOOT_URL}/api/v1/accounts/{account_id}/agents"
            response = requests.get(test_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                _logger.info(f"✓ Account ID detectado automáticamente: {account_id}")
                return account_id
        except:
            continue
    
    return None

def check_connection():
    """
    Verifica la conexión con la API de Chatwoot.
    Detecta automáticamente el Account ID correcto si el configurado no funciona.
    Lanza UserError en caso de éxito o fracaso para notificar al usuario.
    """
    _logger.info("Chatwoot API: Verificando conexión...")
    
    # Intentar con el Account ID configurado
    test_url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/agents"
    headers = _get_headers()

    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Chatwoot devuelve directamente la lista de agentes, no en 'payload'
        agents_data = response.json()
        agent_count = len(agents_data) if isinstance(agents_data, list) else 0
        
        # Mostrar información de los agentes encontrados
        agent_info = "\n\n✅ Agentes encontrados:\n"
        if isinstance(agents_data, list):
            for agent in agents_data:
                agent_info += f"  • {agent.get('name', 'Sin nombre')} (Email: {agent.get('email', 'N/A')}, ID: {agent.get('id', 'N/A')})\n"
        
        raise UserError(f"🎉 ¡ÉXITO! Conexión correcta con Chatwoot.\n\n"
                        f"📍 URL: {test_url}\n"
                        f"✓ Código: {response.status_code}\n"
                        f"✓ Account ID: {CHATWOOT_ACCOUNT_ID}\n"
                        f"✓ Total de agentes: {agent_count}{agent_info}")

    except requests.exceptions.HTTPError as e:
        # Si es error 404, intentar detectar el Account ID correcto
        if e.response.status_code == 404:
            _logger.warning(f"Account ID {CHATWOOT_ACCOUNT_ID} no funciona, intentando detectar automáticamente...")
            detected_id = _auto_detect_account_id()
            
            if detected_id:
                error_details = f"❌ El ACCOUNT_ID configurado ({CHATWOOT_ACCOUNT_ID}) no existe.\n\n"
                error_details += f"✅ SOLUCIÓN ENCONTRADA:\n"
                error_details += f"   Tu Account ID correcto es: {detected_id}\n\n"
                error_details += f"Cambia esta línea en chatwoot_api.py:\n"
                error_details += f"   CHATWOOT_ACCOUNT_ID = {detected_id}\n"
            else:
                error_details = f"❌ El ACCOUNT_ID {CHATWOOT_ACCOUNT_ID} no existe.\n\n"
                error_details += f"URL intentada: {test_url}\n\n"
                error_details += f"Posibles soluciones:\n"
                error_details += f"1. Ve a tu Chatwoot → Settings → Account Settings\n"
                error_details += f"2. O mira la URL cuando estés en Chatwoot: .../app/accounts/X/...\n"
                error_details += f"3. Ese número 'X' es tu Account ID correcto\n"
        else:
            error_details = f"URL intentada: {test_url}\n"
            error_details += f"Código: {e.response.status_code}\n"
            
            if e.response.status_code == 401:
                error_details += "\n❌ Error: No autorizado.\n"
                error_details += "Solución: Revisa tu 'CHATWOOT_API_TOKEN' en chatwoot_api.py.\n"
                error_details += "Debes usar un token de API válido (no un token de acceso personal)."
            else:
                try:
                    error_details += f"\nRespuesta del servidor:\n{e.response.json()}"
                except:
                    error_details += f"\nRespuesta del servidor:\n{e.response.text}"
        
        raise UserError(f"¡ERROR DE CONEXIÓN! Chatwoot respondió con un error.\n\n{error_details}")

    except requests.exceptions.RequestException as e:
        _logger.error(f"Error de red al conectar con Chatwoot: {e}")
        raise UserError(f"¡ERROR DE RED! No se pudo conectar a Chatwoot.\n\n"
                        f"URL intentada: {test_url}\n"
                        f"Revisa:\n"
                        f"1. La URL base: {CHATWOOT_URL}\n"
                        f"2. La conexión a internet de tu servidor Odoo\n"
                        f"3. Que no haya firewall bloqueando la conexión\n\n"
                        f"Error técnico: {e}")


def get_agent_by_email(email):
    """
    Busca un agente en Chatwoot por su correo electrónico.
    Retorna el ID del agente si lo encuentra, None si no existe.
    """
    _logger.info(f"Chatwoot API: Buscando agente con email '{email}'...")
    
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/agents"
    headers = _get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        agents = response.json()
        
        found_emails = []
        if isinstance(agents, list):
            for agent in agents:
                agent_email = agent.get('email')
                if agent_email:
                    found_emails.append(agent_email)
                    if agent_email.lower() == email.lower():
                        _logger.info(f"✓ Agente encontrado: {agent.get('name')} (ID: {agent.get('id')})")
                        return agent.get('id')
        
        _logger.warning(f"✗ No se encontró ningún agente con el email '{email}'")
        _logger.warning(f"   Emails de agentes disponibles en Chatwoot: {found_emails}")
        return None
        
    except Exception as e:
        _logger.error(f"Error al buscar agente en Chatwoot: {e}")
        return None

def list_agents():
    """
    Lista todos los agentes disponibles en Chatwoot.
    Retorna una lista de diccionarios con datos de los agentes.
    """
    _logger.info("Listando todos los agentes de Chatwoot...")
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/agents"
    headers = _get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        _logger.error(f"Error al listar agentes: {e}")
        return []

def assign_conversation_to_agent(conversation_id, agent_id):
    """
    Asigna una conversación de Chatwoot a un agente específico.
    
    Args:
        conversation_id (int): ID de la conversación en Chatwoot
        agent_id (int): ID del agente en Chatwoot
    
    Returns:
        bool: True si la asignación fue exitosa, False en caso contrario
    """
    _logger.info(f"Chatwoot API: Asignando conversación {conversation_id} al agente {agent_id}...")
    
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/assignments"
    headers = _get_headers()
    
    payload = {
        "assignee_id": agent_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        _logger.info(f"✓ Conversación {conversation_id} asignada exitosamente al agente {agent_id}")
        return True
        
    except requests.exceptions.HTTPError as e:
        _logger.error(f"Error HTTP al asignar conversación: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        _logger.error(f"Error al asignar conversación en Chatwoot: {e}")
        return False

def verificar_conversacion_existe(conversation_id):
    """
    Verifica si una conversación existe y está accesible en Chatwoot.
    
    Returns:
        dict: {
            'existe': bool,
            'inbox_id': int or None,
            'status': str or None,
            'assignee_id': int or None,
            'details': dict
        }
    """
    _logger.info(f"Verificando conversación {conversation_id}...")
    
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}"
    headers = _get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            _logger.warning(f"❌ Conversación {conversation_id} NO EXISTE")
            return {
                'existe': False,
                'inbox_id': None,
                'status': None,
                'assignee_id': None,
                'details': {'error': 'Conversación no encontrada'}
            }
        
        response.raise_for_status()
        data = response.json()
        
        resultado = {
            'existe': True,
            'inbox_id': data.get('inbox_id'),
            'status': data.get('status'),
            'assignee_id': data.get('meta', {}).get('assignee', {}).get('id'),
            'details': data
        }
        
        _logger.info(f"✅ Conversación {conversation_id} existe:")
        _logger.info(f"   Inbox ID: {resultado['inbox_id']}")
        _logger.info(f"   Status: {resultado['status']}")
        _logger.info(f"   Asignado a: {resultado['assignee_id']}")
        
        return resultado
        
    except Exception as e:
        _logger.error(f"Error al verificar conversación: {e}")
        return {
            'existe': False,
            'inbox_id': None,
            'status': None,
            'assignee_id': None,
            'details': {'error': str(e)}
        }


def listar_inboxes():
    """
    Lista todas las inboxes disponibles en la cuenta de Chatwoot.
    
    Returns:
        list: Lista de inboxes con su información
    """
    _logger.info("Listando inboxes de Chatwoot...")
    
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/inboxes"
    headers = _get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # La respuesta de inboxes está en 'payload'
        inboxes = response.json().get('payload', [])
        
        _logger.info(f"✅ Se encontraron {len(inboxes)} inboxes:")
        for inbox in inboxes:
            _logger.info(f"   ID: {inbox.get('id')} - Nombre: {inbox.get('name')} - Canal: {inbox.get('channel_type')}")
        
        return inboxes
        
    except Exception as e:
        _logger.error(f"Error al listar inboxes: {e}")
        return []


def verificar_agente_en_inbox(agent_id, inbox_id):
    """
    Verifica si un agente tiene acceso a una inbox específica.
    
    Returns:
        bool: True si el agente tiene acceso, False si no
    """
    _logger.info(f"Verificando acceso del agente {agent_id} a inbox {inbox_id}...")
    
    url = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/inbox_members/{inbox_id}"
    headers = _get_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # La respuesta es una lista de usuarios (agentes)
        members = response.json()
        agent_ids = [member.get('id') for member in members if isinstance(members, list)]
        
        tiene_acceso = agent_id in agent_ids
        
        if tiene_acceso:
            _logger.info(f"✅ Agente {agent_id} TIENE acceso a inbox {inbox_id}")
        else:
            _logger.warning(f"❌ Agente {agent_id} NO tiene acceso a inbox {inbox_id}")
            _logger.info(f"   Agentes con acceso: {agent_ids}")
        
        return tiene_acceso
        
    except Exception as e:
        _logger.error(f"Error al verificar acceso: {e}")
        return False


def diagnostico_completo_conversacion(conversation_id, agent_email):
    """
    Realiza un diagnóstico completo de por qué una asignación puede estar fallando.
    """
    _logger.info("=" * 60)
    _logger.info("🔍 DIAGNÓSTICO COMPLETO")
    _logger.info("=" * 60)
    
    resultado = {
        'conversacion_existe': False,
        'agente_existe': False,
        'agente_tiene_acceso': False,
        'problemas': [],
        'soluciones': []
    }
    
    # 1. Verificar conversación
    _logger.info("1️⃣ Verificando conversación...")
    conv_info = verificar_conversacion_existe(conversation_id)
    resultado['conversacion_existe'] = conv_info['existe']
    resultado['conversacion_info'] = conv_info
    
    if not conv_info['existe']:
        resultado['problemas'].append(f"La conversación {conversation_id} NO EXISTE en Chatwoot")
        resultado['soluciones'].append(
            "Verifica que el 'ID Conversación' sea correcto. Puede que el chat haya sido eliminado o pertenezca a otra cuenta."
        )
        return resultado
    
    _logger.info(f"✅ Conversación existe en Inbox {conv_info['inbox_id']}")
    
    # 2. Verificar agente
    _logger.info("2️⃣ Verificando agente...")
    agent_id = get_agent_by_email(agent_email)
    resultado['agente_existe'] = bool(agent_id)
    resultado['agent_id'] = agent_id
    
    if not agent_id:
        resultado['problemas'].append(f"No existe agente con email '{agent_email}' en Chatwoot")
        resultado['soluciones'].append(
            f"Verifica que el email '{agent_email}' del vendedor en Odoo esté registrado exactamente igual en Chatwoot (Settings → Agents)."
        )
        return resultado
    
    _logger.info(f"✅ Agente existe con ID {agent_id}")
    
    # 3. Verificar acceso a inbox
    _logger.info("3️⃣ Verificando acceso del agente a la inbox...")
    tiene_acceso = verificar_agente_en_inbox(agent_id, conv_info['inbox_id'])
    resultado['agente_tiene_acceso'] = tiene_acceso
    
    if not tiene_acceso:
        resultado['problemas'].append(
            f"El agente ({agent_email}) NO tiene acceso a la Inbox {conv_info['inbox_id']} donde está la conversación."
        )
        resultado['soluciones'].append(
            f"En Chatwoot: Settings → Inboxes → [Selecciona la inbox con ID {conv_info['inbox_id']}] → "
            "Pestaña 'Collaborators' → Agrega al agente."
        )
        return resultado
    
    _logger.info(f"✅ Agente tiene acceso a la inbox")
    
    # Si llegamos aquí, todo OK
    resultado['problemas'].append("✅ Configuración correcta. La asignación debería funcionar.")
    
    _logger.info("=" * 60)
    
    return resultado