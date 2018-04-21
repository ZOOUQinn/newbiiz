odoo.define('hr_attendance_newbiiz.kiosk_confirm', function (require) {
"use strict";

var KioskConfirm = require('hr_attendance.kiosk_confirm')
var core = require('web.core');
var Session = require('web.session');

var KioskNewbiizConfirm = KioskConfirm.extend({

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.next_action = 'hr_attendance.hr_attendance_action_kiosk_mode';
        this.employee_id = action.employee_id;
        this.employee_name = action.employee_name;
        this.employee_state = action.employee_state;
        this.employee_image = Session.url('/web/image', {model: 'hr.employee', id: action.employee_id, field: 'image_medium',});
        this.employee_text_message = action.employee_text_message;
        this.employee_barcode = action.employee_barcode;
        this.employee_department = action.employee_department;
        this.employee_group = action.employee_group;
    },

});

core.action_registry.add('hr_attendance_newbiiz_kiosk_confirm', KioskNewbiizConfirm);

return KioskNewbiizConfirm;

});