odoo.define('l10n_ro_report_D300.l10n_ro_report_d300_widget', function
(require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;

var _t = core._t;

var accountFinancialReportWidget = Widget.extend({
    events: {
        'click .o_l10n_ro_report_d300_web_action': 'boundLink',
        'click .o_l10n_ro_report_d300_web_action_multi': 'boundLinkmulti',
    },
    init: function(parent) {
        this._super.apply(this, arguments);
    },
    start: function() {
        return this._super.apply(this, arguments);
    },
    boundLink: function(e) {
        var res_model = $(e.target).data('res-model')
        var res_id = $(e.target).data('active-id')
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current'
        });
    },
    boundLinkmulti: function(e) {
        var res_model = $(e.target).data('res-model')
        var res_id = $(e.target).data('active-id')        
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: res_model,
            domain: [["id", "in", res_id]],
            views: [[false, "list"], [false, "form"]],
            target: 'current'
        });
    },
});

return accountFinancialReportWidget;

});
