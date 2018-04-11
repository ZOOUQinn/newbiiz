# -*- coding: utf-8 -*-
from odoo import http

# class HrAttendanceNewbiiz(http.Controller):
#     @http.route('/hr_attendance_newbiiz/hr_attendance_newbiiz/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_attendance_newbiiz/hr_attendance_newbiiz/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_attendance_newbiiz.listing', {
#             'root': '/hr_attendance_newbiiz/hr_attendance_newbiiz',
#             'objects': http.request.env['hr_attendance_newbiiz.hr_attendance_newbiiz'].search([]),
#         })

#     @http.route('/hr_attendance_newbiiz/hr_attendance_newbiiz/objects/<model("hr_attendance_newbiiz.hr_attendance_newbiiz"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_attendance_newbiiz.object', {
#             'object': obj
#         })