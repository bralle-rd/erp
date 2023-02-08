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
                name = row[2].strip()
                street_name = row[4].strip()
                search_colony = None
                category_ids = None
                
                # _logger.info("Actualizando = %s", name)
                
                ##########Buscar colonia
                if row[8]:
                    city_id_name = row[8].strip()
                    split_city_name = city_id_name.split(", ")
                    # print("Split city name= ", split_city_name)
                    #Buscar colonia 
                    search_colony = self.env['colony.catalogues'].search_read([('name', '=', split_city_name[0]), ('zip','=', row[11])], ['name','zip','city_id','state_id','country_id'])
                # print("Información de la colonia=", search_colony)
                
                ##########Buscar categoría
                if row[13]:
                    format_category_ids = ["{}".format(item) for item in row[13].split(', ')]
                    category_ids = self.env['res.partner.category'].search([('name', 'in', format_category_ids)]).ids
                #print("Información de las categorías= ", category_ids)
                
                ###########Buscar cliente/proveedor
                search_partner = self.env['res.partner'].search([('name', '=', name)], limit=1) 
                print("search_partner: ", search_partner)
               
                if not search_partner:
                    info_partner = {
                        'id': row[0],
                        'company_type': row[1],
                        'name': name,
                        'street_name': street_name if street_name else '',
                        'street_number': row[5] if row[5] != 'FALSE'else '',
                        'street_number2': row[6] if row[6] != 'FALSE' else '',
                        'l10n_mx_edi_colony': search_colony[0]['id'] if search_colony else None,
                        'city_id': search_colony[0]['city_id'][0] if search_colony and search_colony[0]['city_id'] else None,
                        'state_id': search_colony[0]['state_id'][0] if search_colony and search_colony[0]['state_id'] else None,
                        'zip': row[11] if row[11] != 'FALSE' else '',
                        'country_id': search_colony[0]['country_id'][0] if search_colony else 156,
                        'vat': row[3] if row[3] != 'FALSE' else 'XAXX010101000',#"MX"+row[3] if row[3] != 'FALSE' else '',
                        'How_do_you_know_us': row[14] if row[14] != 'Otro' and row[14] != 'FALSE' else None,
                        'code_plus': row[15] if row[15] != 'FALSE' else '',
                        'phone': row[16] if row[16] != 'FALSE' else '',
                        'mobile': row[17] if row[17] != 'FALSE' else '',
                        'email': row[18] if row[18] != 'FALSE' else '',
                        'lang': row[19] if row[19] else None,
                        'category_id': category_ids if category_ids else None,
                        'purchasing_manager': self.env['res.partner'].search([('name', '=', row[20])]).id if row[20] else None,
                        'customer_rank': 1 if row[22] == 'TRUE' else 0,
                        'supplier_rank': 1 if row[23] == 'TRUE' else 0,
                        'user_id': self.env['res.users'].search([('name', '=', row[25])]).id if row[25] else None,
                        'property_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[33])]).id if row[33] else None,
                        'property_product_pricelist': self.env['product.pricelist'].search([('name', '=', row[29])]).id if row[29] else None,
                        'property_account_position_id': self.env['account.fiscal.position'].search([('name', '=', row[39])]).id if row[39] else None,
                        'property_supplier_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[38])]).id if row[38] else None,
                        'ref': row[30] if row[30] != 'FALSE' else '',
                        'industry_id': self.env['res.partner.industry'].search([('name', '=', row[31])]).id if row[31] else None,
                        'trust': row[34] if row[34] else None,
                        'credit_limit': float(row[36]),
                    }
                    _logger.info("Crear partner= %s", info_partner)
                    self.env['res.partner'].sudo().create(info_partner)
                else:
                    _logger.info("Actualizar partner= %s", search_partner)
                    search_partner.sudo().write({
                        'company_type': row[1],
                        'name': name,
                        'street_name': street_name if street_name else '',
                        'street_number': row[5] if row[5] != 'FALSE'else '',
                        'street_number2': row[6] if row[6] != 'FALSE' else '',
                        'l10n_mx_edi_colony': search_colony[0]['id'] if search_colony else None,
                        'city_id': search_colony[0]['city_id'][0] if search_colony and search_colony[0]['city_id'] else None,
                        'state_id': search_colony[0]['state_id'][0] if search_colony and search_colony[0]['state_id'] else None,
                        'zip': row[11] if row[11] else '',
                        'country_id': search_colony[0]['country_id'][0] if search_colony else 156,
                        'vat': row[3] if row[3] != 'FALSE' else 'XAXX010101000',#"MX"+row[3] if row[3] != 'FALSE' else '',
                        'How_do_you_know_us': row[14] if row[14] != 'Otro' and row[14] != 'FALSE' else None,
                        'code_plus': row[15] if row[15] != 'FALSE' else '',
                        'phone': row[16] if row[16] != 'FALSE' else '',
                        'mobile': row[17] if row[17] != 'FALSE' else '',
                        'email': row[18] if row[18] != 'FALSE' else '',
                        'lang': row[19] if row[19] else None,
                        'category_id': category_ids if category_ids else None,
                        'purchasing_manager': self.env['res.partner'].search([('name', '=', row[20])]).id if row[20] else None,
                        'customer_rank': 1 if row[22] == 'TRUE' else 0,
                        'supplier_rank': 1 if row[23] == 'TRUE' else 0,
                        'user_id': self.env['res.users'].search([('name', '=', row[25])]).id if row[25] else None,
                        # 'team_id': self.env['crm.team'].search([('name', '=', row[25])]).id if row[25] else None, 
                        'property_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[33])]).id if row[33] else None,
                        'property_product_pricelist': self.env['product.pricelist'].search([('name', '=', row[29])]).id if row[29] else None,
                        'property_account_position_id': self.env['account.fiscal.position'].search([('name', '=', row[39])]).id if row[39] else None,
                        'property_supplier_payment_term_id': self.env['account.payment.term'].search([('name', '=', row[38])]).id if row[38] else None,
                        'ref': row[30] if row[30] != 'FALSE' else '',
                        'industry_id': self.env['res.partner.industry'].search([('name', '=', row[31])]).id if row[31] else None,
                        'trust': row[34] if row[34] else None,
                        'credit_limit': float(row[36]),
                    })
       
        return True

