# -*- coding: utf-8 -*-
import os
from os.path import splitext
from odoo.exceptions import Warning
from odoo import models, fields, _, api, SUPERUSER_ID
import io
from io import StringIO
import base64
import csv
from datetime import date
from ..helpers import utilities
import logging
from datetime import datetime
import time
import random

_logger = logging.getLogger(__name__)


class PartnerTemplateInherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def import_partner_ckunk(self):
        #cron Job
        allAttachment = self.env['ir.attachment'].search([('state', '=', 'processing'), ('mimetype','=','application/csv')], order='id asc', limit=1)
        _logger.info("Archivo a procesar por el CRON JOB= %s", allAttachment.name)
        
        if allAttachment:
            for attachment in allAttachment:
                fields, data = utilities._read_csv_attachment(attachment.datas)
                if data: 
                    self.update_seller_price_in_product(data)
                    _logger.info("CRON JOB Finalizado= %s", allAttachment.name)
                    self.unlink_attachment(allAttachment)
                    
        return True

    def unlink_attachment(self, attachments):
        for i, attachment in enumerate(attachments):
            # print("{0} Eliminando= {1}".format(i, attachment.id))
            attachment.unlink()
        
    def update_seller_price_in_product(self, values):
        line_count = 0
        for row in values:
            if line_count == 0:
                line_count += 1
            else:
                name = row[4].strip() #Eliminar espacios en blanco al principio y final
                street_name = row[6].strip() #Eliminar espacios en blanco al principio y final
                search_state = None
                category_ids = None
                
                #########Buscar estado
                if row[10]:
                    city_id_name = row[10]
                    # print("Split city name= ", split_city_name)
                    #Buscar estado 
                    search_state = self.env['res.country.state'].search([('name', '=', city_id_name.upper())]).id
                    print("Estado encontrado=", search_state)
                    if not search_state:
                        search_state_id = self.env['res.country.state'].sudo().create({'name': city_id_name.upper(), 'code': city_id_name[0:3] if city_id_name else random.randint(0,9), 'country_id': row[12] if row[12] else None})
                        search_state = search_state_id.id
                        #print("Información del estado=", search_state)
                
                ##########Buscar categoría
                if row[13]:
                    format_category_ids = ["{}".format(item) for item in row[13].split(', ')]
                    category_ids = self.env['res.partner.category'].search([('name', 'in', format_category_ids)]).ids
                    #print("Información de las categorías= ", category_ids)
                
                ###########Buscar cliente/proveedor
                search_partner = self.env['res.partner'].search([('name', '=', name.upper())], limit=1) 
                print("search_partner: ", search_partner)
               
                #Asignar dirección padre
                if search_partner:
                    search_partner.sudo().write({
                        'parent_id': self.env['res.partner'].search([('name', '=', row[2].strip())]).id if row[2] else None,
                        })
                else:
                    continue
                
                
                # ########## Actualizar o Crear contacto
                # if not search_partner:
                #     info_partner = {
                #         'id': row[0],
                #         'company_type': row[1],
                #         'type': row[3] if row[3] else None,
                #         'name': name.upper() if row[4] else '',
                #         'street': row[6].strip() if row[6] else '',
                #         'street2': row[7].strip() if row[7] != 'FALSE' else '',
                #         'city': row[8].strip() if row[8] else None,
                #         'state_id': search_state if search_state else None,
                #         'zip': row[11] if row[11] != 'FALSE' else '',
                #         'country_id': int(row[12]) if row[12] else None,
                #         'vat': row[5] if row[5] != 'FALSE' else 'XAXX010101000',#"MX"+row[3] if row[3] != 'FALSE' else '',
                #         'phone': row[14] if row[14] != 'FALSE' else '',
                #         'mobile': row[15] if row[15] != 'FALSE' else '',
                #         'email': row[16] if row[16] != 'FALSE' else '',
                #         'lang': row[17] if row[17] else None, #self.env['res.lang'].search([('code', '=', row[17])]).id if row[17] else None,
                #         'category_id': category_ids if category_ids else None,
                #         'customer_rank': 1 if row[18] == 'TRUE' else 0,
                #         'supplier_rank': 1 if row[19] == 'TRUE' else 0,
                #         'user_id': self.env['res.users'].search([('name', '=', row[20])]).id if row[20] else None,
                #         # 'team_id': self.env['crm.team'].search([('name', '=', row[25])]).id if row[25] else None, 
                #         'property_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[24])]).id if row[24] else None,
                #         'property_product_pricelist': self.env['product.pricelist'].search([('name', '=', row[21])]).id if row[21] else None,
                #         'property_account_position_id': self.env['account.fiscal.position'].search([('name', '=', row[28])]).id if row[28] else None,
                #         'property_supplier_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[27])]).id if row[27] else None,
                #         'ref': row[22] if row[22] != 'FALSE' else '',
                #         'industry_id': self.env['res.partner.industry'].search([('name', '=', row[23])]).id if row[23] else None,
                #         'trust': row[25] if row[25] else None,
                #         'credit_limit': float(row[26]),
                #     }
                #     _logger.info("Crear partner= %s", info_partner)
                #     self.env['res.partner'].sudo().create(info_partner)
                # else:
                #     _logger.info("Actualizar partner= %s", search_partner)
                #     search_partner.sudo().write({
                #         'company_type': row[1],
                #         'type': row[3] if row[3] else None,
                #         'name': name.upper() if row[4] else '',
                #         'street': row[6].strip() if row[6] else '',
                #         'street2': row[7].strip() if row[7] != 'FALSE' else '',
                #         'city': row[8].strip() if row[8] else None,
                #         'state_id': search_state if search_state else None,
                #         'zip': row[11] if row[11] != 'FALSE' else '',
                #         'country_id': int(row[12]) if row[12] else None,
                #         'vat': row[5] if row[5] != 'FALSE' else 'XAXX010101000',#"MX"+row[3] if row[3] != 'FALSE' else '',
                #         'phone': row[14] if row[14] != 'FALSE' else '',
                #         'mobile': row[15] if row[15] != 'FALSE' else '',
                #         'email': row[16] if row[16] != 'FALSE' else '',
                #         'lang': row[17] if row[17] else None, #self.env['res.lang'].search([('code', '=', row[17])]).id if row[17] else None,
                #         'category_id': category_ids if category_ids else None,
                #         'customer_rank': 1 if row[18] == 'TRUE' else 0,
                #         'supplier_rank': 1 if row[19] == 'TRUE' else 0,
                #         'user_id': self.env['res.users'].search([('name', '=', row[20])]).id if row[20] else None,
                #         # 'team_id': self.env['crm.team'].search([('name', '=', row[25])]).id if row[25] else None, 
                #         'property_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[24])]).id if row[24] else None,
                #         'property_product_pricelist': self.env['product.pricelist'].search([('name', '=', row[21])]).id if row[21] else None,
                #         'property_account_position_id': self.env['account.fiscal.position'].search([('name', '=', row[28])]).id if row[28] else None,
                #         'property_supplier_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[27])]).id if row[27] else None,
                #         'ref': row[22] if row[22] != 'FALSE' else '',
                #         'industry_id': self.env['res.partner.industry'].search([('name', '=', row[23])]).id if row[23] else None,
                #         'trust': row[25] if row[25] else None,
                #         'credit_limit': float(row[26]),
                #     })
       
        return True

