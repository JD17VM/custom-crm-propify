from odoo import models, fields

class CustomLead(models.Model):
    _inherit = 'crm.lead'

    id_externo = fields.Char(string='ID Transacción')
    metodo_contacto = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Otro')
    ], string='Método de Contacto')