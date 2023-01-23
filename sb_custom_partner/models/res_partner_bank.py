# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartnerBankInherit(models.Model):
    _inherit = 'res.partner.bank'

    sucursal = fields.Char(string=_('Sucursal'))