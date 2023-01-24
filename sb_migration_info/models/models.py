# -*- coding: utf-8 -*-
import tempfile
import binascii
import base64
import xlrd
import io
from io import StringIO
import os
from os.path import splitext
import csv
from odoo.exceptions import Warning
from odoo import models, fields, _, api, SUPERUSER_ID, registry
import logging
from ..helpers import utilities
from datetime import date
import random


_logger = logging.getLogger(__name__)


class ResPartnerInfoImportWizard(models.TransientModel):
    _name = 'import.partner.info'
    _description = 'import.partner.info'
   
    option = fields.Selection([('csv', 'CSV')], default='csv', string="Import File Type")
    file = fields.Binary(string="Archivo", required=True)
    model = fields.Selection([('partner', 'Contacto'), ('template', 'Producto plantilla'), ('variant', 'Producto variante')], default='partner', string="Modelo")
    
    
    def import_file_csv_xlsx(self):
        """ Function to import product or update from csv or xlsx file """
        
        row_size = 2000
        warn_msg = ''
        #Read file type .csv
        if self.option == 'csv':
            try:
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                file_reader.extend(csv_reader)
            except:
                raise Warning(_("El archivo no es de tipo '%s'" % self.option))


            number_lines = sum(1 for row in file_reader)
            if number_lines > row_size:
                #Split file 
                res = self.split_xlsx_or_csv(self.option, self.file, row_size)
                #print("Aquí todo bien= ", res)
                warn_msg = _("El archivo contiene %s registros. \nSe crearon %s archivos con %s registros en cada archivo. \nEl CRON se encargará de procesar de forma automática.") % (
                                number_lines,
                                len(res),
                                row_size
                )
                
                if warn_msg:
                    message_id = self.env['migration.message.wizard'].create({'message': warn_msg})
                    return {
                        'name': 'Message',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'migration.message.wizard',
                        'res_id': message_id.id,
                        'target': 'new'
                    }    
            else:
                if file_reader:
                    if self.model == 'partner':
                        res = self.update_seller_price_in_product(file_reader)
                    elif self.model == 'template':
                        res = self.import_product(file_reader)
                    else:
                        res = self.update_seller_price_in_product(file_reader)
                    
                    if not warn_msg:
                        message_id = self.env['migration.message.wizard'].create({'message': 'Se actualizó/importó de forma exitosa.'})
                        return {
                            'name': 'Message',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'migration.message.wizard',
                            'res_id': message_id.id,
                            'target': 'new'
                        }
        else:
            raise Warning(_("Por favor selecciona un archivo con formato .csv"))
        
        return res

    @api.returns("ir.attachment")
    def _create_csv_attachment(self, f, file_name):
        encoding = "utf-8"
        datas = base64.encodebytes(f.getvalue().encode(encoding))
        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name, 
                "res_model": self._name, 
                'res_id': self.id,
                'mimetype': 'application/csv',
                "type": "binary", 
                "datas": datas, 
                "state": "processing"
            }
        )
        
        print("ID attachment= ", attachment)
        return attachment
    

    def split_xlsx_or_csv(self, type_file, file, size_row):
        """
        Función para trozar el excel en batch
        """
        
        if type_file == 'csv':
            fields, data = utilities._read_csv_attachment(file)
            file_name="Lote.csv"
            root, ext = splitext(file_name)
            header = fields
            rows = [row for row in data]
            pages = []
            allAttachment = []
            
            row_count = len(rows)
            start_index = 0
            
            while start_index < row_count:
                pages.append(rows[start_index: start_index+size_row])
                start_index += size_row
            
            for i, page in enumerate(pages):
                # print("Página =", i)
                f = StringIO()
                writer = csv.writer(f, delimiter=',', quotechar='"')
                writer.writerow(header)
                for row in page:
                    writer.writerow(row)
                attachment = self._create_csv_attachment(f, file_name=root + "_" + str(i+1) + ext)
                allAttachment.append(attachment.id)
                
        return allAttachment
    
        
    def update_seller_price_in_product(self, values,):
        line_count = 0
        for row in values:
            if line_count == 0:
                line_count += 1
            else:
                ref = row[0].strip()#Referencia interna
                name = row[1].strip() #Nombre
                vat = row[2].strip() #RFC
                street = row[3].strip() #Calle
                street_number2 = row[4].strip() #Número interior
                street_number = row[5].strip() #Número exterior
                l10n_mx_edi_colony = row[6].strip() #Colonía
                zip = row[7].strip() #Código postal
                l10n_mx_edi_locality = row[8].strip() #Localidad
                city_id = row[9].strip() #Municipio
                state_id = row[10].strip() #Estado
                country_id = row[12].strip() #País
                phone = row[13].strip() #Teléfono
                
                website = row[15].strip() #Página web
                l10n_mx_edi_curp = row[16].strip()#Curp
                
                email = row[27].strip()#Correo electrónico
                con_credito = row[17].strip()#Con crédito
                dias_credito = row[18].strip()#Días de crédito
                credit_limit = row[19].strip()#Límite de crédito
                tip_tercero = row[20].strip()#
                tip_opera = row[21].strip()#
                forma_pago = row[22].strip()#Forma de pago
                bank_id = row[23].strip()#Banco
                sucursal_bank = row[24].strip()#Sucursal del banco
                account_bank = row[25].strip()#Número de cuenta de banco
                clabe_bank = row[26].strip()#Clabe de banco
                property_account_position_id = row[28].strip()#Registro fiscal
                
                search_city = None
                
                # #########Buscar ciudad
                if city_id:
                    #Buscar estado 
                    search_city = self.env['res.city'].search([('name', '=', city_id)], limit=1).id
                    print("Ciudad encontrado=", search_city)
                    if not search_city:
                        search_city_id = self.env['res.city'].sudo().create({
                            'name': city_id.lower(), 
                            'state_id': self.env['res.country.state'].search([('name', '=', state_id)], limit=1).id if state_id else None,
                            'country_id': self.env['res.country'].search([('name', '=', country_id)], limit=1).id if country_id else 156})
                        search_city = search_city_id.id
                        print("Información de ciudad creada=", search_city)
    
                
                ###########Buscar cliente/proveedor
                search_partner = self.env['res.partner'].search([('name', '=', name.upper())], limit=1) 
                print("search_partner: ", search_partner)
                
                if not search_partner:
                    info_partner = {
                        'ref': ref, 
                        'company_type': 'person' if len(vat) == 13 else 'company',
                        'name': name,
                        'vat': vat,
                        'street_name': street,
                        'street_number2': street_number2, 
                        'street_number': street_number,
                        'l10n_mx_edi_colony': l10n_mx_edi_colony,
                        'zip': zip,
                        'l10n_mx_edi_locality': l10n_mx_edi_locality,
                        'city_id': search_city,
                        'state_id': self.env['res.country.state'].search([('name', '=', state_id)], limit=1).id if state_id else None, 
                        'country_id': self.env['res.country'].search([('name', '=', country_id)], limit=1).id if country_id else 156,
                        'phone': phone,
                        'website': website,
                        'l10n_mx_edi_curp': l10n_mx_edi_curp,
                        'email': email,
                        'con_credito': con_credito,
                        'dias_credito': dias_credito,
                        'credit_limit': credit_limit,
                        # 'tip_tercero': tip_tercero,
                        'l10n_mx_type_of_operation': tip_opera if tip_opera else None, #self.env['res.partner.industry'].search([('name', '=', tip_opera)], limit=1).id if tip_opera else None,
                        'forma_pago': forma_pago,
                        'property_account_position_id': property_account_position_id,
                        'supplier_rank': 1,
                        'lang': 'es_MX'
                    }
                    _logger.info("Crear partner= %s", info_partner)
                    partner_id = self.env['res.partner'].sudo().create(info_partner)
                    
                    # if bank_id:
                    #     partner_id.write({
                    #         'bank_ids': [(0,0, {
                    #             'bank_id': self.env['res.bank'].search([('name', '=', bank_id)], limit=1).id if bank_id else None,
                    #             'sucursal': sucursal_bank,
                    #             'acc_number': account_bank,
                    #             'l10n_mx_edi_clabe': clabe_bank
                    #         })]
                    #     })
                    # else:
                    #     pass
                    
                else:
                    pass
                
        return {}
    
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




