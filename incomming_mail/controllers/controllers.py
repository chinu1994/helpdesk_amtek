# -*- coding: utf-8 -*-
# from odoo import http


# class Task2(http.Controller):
#     @http.route('/task_2/task_2', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/task_2/task_2/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('task_2.listing', {
#             'root': '/task_2/task_2',
#             'objects': http.request.env['task_2.task_2'].search([]),
#         })

#     @http.route('/task_2/task_2/objects/<model("task_2.task_2"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('task_2.object', {
#             'object': obj
#         })

