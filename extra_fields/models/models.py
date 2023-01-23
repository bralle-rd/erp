# -*- coding: utf-8 -*-

from odoo import models, fields, api


class productTemplate(models.Model):
    _inherit = 'product.template'
    muestra = fields.Char(string="Muestra")
    campo_libre = fields.Char(string="Campo libre")
    utilidad = fields.Float(string="Utilidad")

