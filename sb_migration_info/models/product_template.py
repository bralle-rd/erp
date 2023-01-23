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


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    @api.model
    def import_product_template_chunk(self):
        #cron Job
        allAttachment = self.env['ir.attachment'].search([('state', '=', 'processing'), ('mimetype','=','application/csv')], order='id asc', limit=1)
        _logger.info("Lote de producto a procesar por el CRON JOB= %s", allAttachment.name)
        
        if allAttachment:
            for attachment in allAttachment:
                fields, data = utilities._read_csv_attachment(attachment.datas)
                if data: 
                    self.import_product(data)
                    _logger.info("CRON JOB Finalizado= %s", allAttachment.name)
                    self.unlink_attachment(allAttachment)
                    
        return True

    def unlink_attachment(self, attachments):
        for i, attachment in enumerate(attachments):
            attachment.unlink()
        
    def import_product(self, values):
        line_count = 0
        record_count = 0
        for row in values:
            if line_count == 0:
                line_count += 1
            else:
                default_code = row[0].strip() #Referencia interna
                product_name = row[1].strip() #Nombre del producto
                product_supplier = row[2].strip() #Proveedor del producto
                product_price_supplier = row[3].strip() #Precio del proveedor
                product_currency_supplier = row[4].strip() #Moneda del proveedor
                product_brand = row[5].strip()#Marca del producto
                product_coste = row[6].strip()#Coste del producto
                product_price = row[7].strip()#Precio del producto
                product_currency = row[8].strip()#Moneda del producto
                product_currency_coste = row[9].strip()#Moneda del costo del producto
                sale_ok = row[10]#Puede ser vendido
                is_published = row[11]#Publicado en el website
                
                product_brand_id = None
                
                product_brand_id = self.env['product.brand'].search([('name', '=', product_brand.upper())]).id
                #########Buscar categoria del producto
                # search_categ_id = None
                # if product_categ:
                #     if " / " in product_categ:
                #         split_categ = product_categ.split('/ ')
                #         print("split categ =", split_categ)
                #         product_categ = split_categ[len(split_categ) - 1]
                
                #     #Buscar categoría
                #     search_categ_id = self.env['product.category'].search([('name', '=', product_categ)], limit=1)
                #     print("Información de categoría=", search_categ_id)
                
           
                # print("Marca del producto encontrado: ", product_brand_id)
                
                ###########Buscar producto
                search_product = self.env['product.template'].search([('default_code', '=', default_code),('brand_id', '=', product_brand_id),('name', '!=', product_name)], limit=1) 
                
                # print("search_product: ", search_product)
                record_count += 1
                # print("Count record: ", record_count)
                
                if not search_product:
                    info_product = {
                        'default_code': default_code if default_code else '',
                        'name': product_name,
                        'type': 'product',
                        # 'categ_id': search_categ_id.id if search_categ_id else None,
                        'brand_id': product_brand_id if product_brand_id else None,#self.env['product.brand'].search([('name', '=', product_brand)]).id if product_brand else None,
                        'standard_price': product_coste if product_coste else '',
                        'list_price': product_price if product_price else '',
                        'currency_id': self.env['res.currency'].search([('name', '=', product_currency)], limit=1).id,
                        'cost_currency_id': self.env['res.currency'].search([('name', '=', product_currency_coste)], limit=1).id,
                        'sale_ok': True, #if sale_ok == 'TRUE' else False,
                        'is_published': True #if is_published == 'TRUE' else False,
                    }
                    # _logger.info("Crear producto= %s", info_product)
                    product_id = self.env['product.template'].sudo().create(info_product)
                    
                    ####Crear tarifa de proveedor
                    supplierinfo = {
                        'partner_id': self.env['res.partner'].search([('name', '=', product_supplier)], limit=1).id,
                        'currency_id': self.env['res.currency'].search([('name', '=', product_currency_supplier)], limit=1).id,
                        'price': product_price_supplier,
                        'product_tmpl_id': product_id.id
                    }
                    self.env['product.supplierinfo'].sudo().create(supplierinfo)
                else:
                    info_product = {
                        'default_code': default_code if default_code else '',
                        'name': product_name,
                        'type': 'product',
                        # 'categ_id': search_categ_id.id if search_categ_id else None,
                        'brand_id': product_brand_id if product_brand_id else None, #self.env['product.brand'].search([('name', '=', product_brand)]).id if product_brand else None,
                        'standard_price': product_coste if product_coste else '',
                        'list_price': product_price if product_price else '',
                        'currency_id': self.env['res.currency'].search([('name', '=', product_currency)], limit=1).id,
                        'cost_currency_id': self.env['res.currency'].search([('name', '=', product_currency_coste)], limit=1).id,
                        'sale_ok': True, #if sale_ok == 'TRUE' else False,
                        'is_published': True,# if is_published == 'TRUE' else False,
                    }
                    _logger.info("Actualizar producto= %s", info_product)
        return True
