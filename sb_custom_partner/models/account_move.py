# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AcountMoveInherit(models.Model):
    _inherit = 'account.move'
    
    forma_pago = fields.Selection(
        selection=[('01', 'Efectivo'), 
                   ('02', 'Cheque nominativo'), 
                   ('03', 'Transferencia electrónica de fondos'),
                   ('04', 'Tarjeta de Crédito'), 
                   ('05', 'Monedero electrónico'),
                   ('06', 'Dinero electrónico'), 
                   ('08', 'Vales de despensa'), 
                   ('12', 'Dación en pago'), 
                   ('13', 'Pago por subrogación'), 
                   ('14', 'Pago por consignación'), 
                   ('15', 'Condonación'), 
                   ('17', 'Compensación'), 
                   ('23', 'Novación'), 
                   ('24', 'Confusión'), 
                   ('25', 'Remisión de deuda'), 
                   ('26', 'Prescripción o caducidad'), 
                   ('27', 'A satisfacción del acreedor'), 
                   ('28', 'Tarjeta de débito'), 
                   ('29', 'Tarjeta de servicios'), 
                   ('30', 'Aplicación de anticipos'), 
                   ('31', 'Intermediario pagos'),
                   ('99', 'Por definir')],
        string=_('Forma de pago'),
        compute="_onchange_partner_id",
        inverse="_pass",
        store=True,
    )
    
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),
                   ('PPD', _('Pago en parcialidades o diferido'))],
        string=_('Método de pago'), 
        compute="_onchange_partner_id",
        inverse="_pass",
        store=True,
    )
    uso_cfdi = fields.Selection(
        selection=[('G01', _('Adquisición de mercancías')),
                   ('G02', _('Devoluciones, descuentos o bonificaciones')),
                   ('G03', _('Gastos en general')),
                   ('I01', _('Construcciones')),
                   ('I02', _('Mobiliario y equipo de oficina por inversiones')),
                   ('I03', _('Equipo de transporte')),
                   ('I04', _('Equipo de cómputo y accesorios')),
                   ('I05', _('Dados, troqueles, moldes, matrices y herramental')),
                   ('I06', _('Comunicacion telefónica')),
                   ('I07', _('Comunicación Satelital')),
                   ('I08', _('Otra maquinaria y equipo')),
                   ('D01', _('Honorarios médicos, dentales y gastos hospitalarios')),
                   ('D02', _('Gastos médicos por incapacidad o discapacidad')),
                   ('D03', _('Gastos funerales')),
                   ('D04', _('Donativos')),
                   ('D07', _('Primas por seguros de gastos médicos')),
                   ('D08', _('Gastos de transportación escolar obligatoria')),
                   ('D10', _('Pagos por servicios educativos (colegiaturas)')),
                   ('P01', _('Por definir'))],
        string=_('Uso CFDI (cliente)'),
        compute="_onchange_partner_id",
        inverse="_pass",
        store=True,
    )
    
    def _pass(self):
        pass
    
    @api.depends('partner_id')
    def _onchange_partner_id(self):
        for move in self:
            if move.partner_id.forma_pago:
                move.forma_pago = move.partner_id.forma_pago
                move.l10n_mx_edi_payment_method_id = self.env['l10n_mx_edi.payment.method'].search([('code', '=', move.forma_pago)]).id if move.forma_pago else None
            else:
                move.forma_pago = '99'
                move.l10n_mx_edi_payment_method_id = self.env['l10n_mx_edi.payment.method'].search([('name', '=', 'Por definir')]).id 
                
            if move.partner_id.methodo_pago:
                move.methodo_pago = move.partner_id.methodo_pago
                move.l10n_mx_edi_payment_policy = move.methodo_pago
            else:
                move.methodo_pago = False
                move.l10n_mx_edi_payment_policy = False
                
            if move.partner_id.uso_cfdi:
                move.uso_cfdi = move.partner_id.uso_cfdi
                move.l10n_mx_edi_usage = move.uso_cfdi
            else:
                move.uso_cfdi = 'P01'
                move.l10n_mx_edi_usage = 'P01'
    
    