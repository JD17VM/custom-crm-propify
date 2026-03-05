# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def test_res_partner_works(self):
        _logger.info(">>> El archivo res_partner.py y su función han sido llamados correctamente.")
        return True