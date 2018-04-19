odoo.define('hr_attendance_newbiiz.employee_kanban_view_handler', function(require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');

KanbanRecord.include({
    _openRecord: function () {
        if (this.modelName === 'hr.employee' && this.$el.parents('.o_hr_employee_newbiiz_attendance_kanban').length) {

            var action = {
                type: 'ir.actions.client',
                name: 'Confirm',
                tag: 'hr_attendance_newbiiz_kiosk_confirm',
                employee_id: this.record.id.raw_value,
                employee_name: this.record.name.raw_value,
                employee_state: this.record.attendance_state.raw_value,
                employee_text_message: this.record.text_message.raw_value,
            };

            this.do_action(action);

        } else {
            this._super.apply(this, arguments);
        }
    }
});

});