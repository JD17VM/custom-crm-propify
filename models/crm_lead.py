from odoo import models, fields

class CustomLead(models.Model):
    _inherit = 'crm.lead'

    id_externo = fields.Char(string='ID Transacción')