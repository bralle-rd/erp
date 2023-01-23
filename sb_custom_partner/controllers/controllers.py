# -*- coding: utf-8 -*-
# from odoo import http


# class SbCustomPartner(http.Controller):
#     @http.route('/sb_custom_partner/sb_custom_partner', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sb_custom_partner/sb_custom_partner/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sb_custom_partner.listing', {
#             'root': '/sb_custom_partner/sb_custom_partner',
#             'objects': http.request.env['sb_custom_partner.sb_custom_partner'].search([]),
#         })

#     @http.route('/sb_custom_partner/sb_custom_partner/objects/<model("sb_custom_partner.sb_custom_partner"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sb_custom_partner.object', {
#             'object': obj
#         })
