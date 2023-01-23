# -*- coding: utf-8 -*-
# from odoo import http


# class ExtraFields(http.Controller):
#     @http.route('/extra_fields/extra_fields', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/extra_fields/extra_fields/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('extra_fields.listing', {
#             'root': '/extra_fields/extra_fields',
#             'objects': http.request.env['extra_fields.extra_fields'].search([]),
#         })

#     @http.route('/extra_fields/extra_fields/objects/<model("extra_fields.extra_fields"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('extra_fields.object', {
#             'object': obj
#         })
