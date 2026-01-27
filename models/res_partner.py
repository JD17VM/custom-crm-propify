from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    chatwoot_contact_id = fields.Char(string='Chatwoot Contact ID', help="ID of the contact in Chatwoot")