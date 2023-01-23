# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import Warning
import random
from odoo.tools import float_is_zero
from datetime import date, datetime


class InheritAttachment(models.Model):
    _inherit = 'ir.attachment'

    type = fields.Selection(selection_add=[('csv', 'CSV')], ondelete={'csv': 'set default'})
    state = fields.Selection([('open', 'Abierto'), ('processing', 'Procesar'), ('close', 'Cerrado'), ('error', 'Error')], 'Estatus', copy=False, default='close', help="")