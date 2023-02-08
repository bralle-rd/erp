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

_logger = logging.getLogger(__name__)


class ResPartnerInfoImportWizard(models.TransientModel):
    _name = 'import.partner.info'
    _description = 'import.partner.info'
   
    option = fields.Selection([('csv', 'CSV')], default='csv', string="Import File Type")
    operation = fields.Selection([('create_or_update', 'Crear o Actualizar'), ('related_parent', 'Relacionar padre')], string="Operación")
    model = fields.Selection([('partner', 'Contactos'), ('product', 'Producto Plantilla')], string="Modelo")
    file = fields.Binary(string="Archivo", required=True)
   
    def import_file_csv_xlsx(self):
        """ Function to import product or update from csv or xlsx file """
        
        row_size = 1000
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
                print("Aquí todo bien= ", res)
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
        for row in values:
            default_code = row[0].strip() #Referencia interna
            name_supplier = row[1].strip() #Nombre del proveedor
            code_supplier = row[2].strip() #Código del proveedor
            
            
            #Buscar el producto
            product_id = self.env['product.template'].search([('default_code', '=', default_code)], limit=1)
            
            #Buscar proveedor
            supplier_id = self.env['res.partner'].search([('name', '=', name_supplier)], limit=1).id

            _logger.info("Información del producto = %s", product_id)
            _logger.info("Resultado de la búsqueda de proveedor= %s", supplier_id)
            
            #Producto y proveedor encontrado
            if product_id and supplier_id:
                
                #Buscar proveedor en el producto
                search_seller = next((item for item in product_id.seller_ids if item.partner_id.id == supplier_id), None)
                
                #El producto esta asignado a éste proveedor
                if search_seller is not None:
                    vals = {
                            'partner_id': supplier_id,
                            'product_code': code_supplier,
                            'product_tmpl_id':product_id.id
                        }
                    search_seller.sudo().write(vals)
                else: #El producto no esta asignado a éste proveedor
                    supplierinfo = {
                            'partner_id': supplier_id,
                            'product_code': code_supplier,
                            'product_tmpl_id':product_id.id
                        }
                    print("Crear proveedor de precio= ", supplierinfo)
                    self.env['product.supplierinfo'].sudo().create(supplierinfo)
            else:
                continue
                
        # et = time.time()
        # elapsed_time = (et - st)/60
        # print("Tiempo en terminar la ejecución", elapsed_time, "Min")
                
        return {}

