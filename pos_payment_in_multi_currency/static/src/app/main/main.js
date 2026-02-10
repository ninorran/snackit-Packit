/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { formatFloat, roundDecimals as round_di } from "@web/core/utils/numbers";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
ClosePosPopup.props.push("currency_amount?")

patch(PosStore.prototype, {
    async processServerData() {
        var self = this;
        await super.processServerData(...arguments);
        const currencies = self.config.multi_currency_ids
        if (currencies) {     
            self.currencies = false
            self.config.currencie_data = false;
            self.config.currencie_data = self.currency;
            if (self.config.enable_multi_currency && self.config.multi_currency_ids) {
                self.currencies = []
                self.currency_by_id = {}
                currencies.forEach(function (currencie) {
                    if (self.config.currency_id.id != currencie.id) {
                        self.currencies.push(currencie)
                        self.currency_by_id[currencie.id] = currencie
                    }
                    if (self.config.currency_id.id == currencie.id) {
                        self.currencies.push(currencie)
                        self.currency_by_id[currencie.id] = currencie
                    }
                    if (currencie.rate == 1) {
                        self.base_currency = currencie
                    }
                });
            }
        }
    },

    formating(amount, currency) {
        if (currency) {
            var currency = currency
        }
        else {
          var currency = this.currency;
        }
        if (currency.position === 'after') {
          return amount + ' ' + (currency.symbol || '');
        } else {
          return (currency.symbol || '') + ' ' + amount;
        }
    },

    format_currency_n_symbol(amount, precisson) {
        if (typeof amount === 'number') {
          var decimals = 4;
          amount = round_di(amount, decimals)
          amount = formatFloat(round_di(amount, decimals), {
            digits: [69, decimals],
          });
        }
        return amount;
  
    },

    get_other_currency_amount(line) {
        var self = this;
        if (line && line.currency_id) {
            var amt = (self.currency_by_id[line.currency_id].rate * line.otc_amount) / self.currency.rate
            var res = round_di(amt, 2)
            return res;
        }
        else {
            line.other_currency_amount = 0.0;
            return 0.0;
        }
    },
    
    get_change_mc(change, paymentline) {
        let order = this.getOrder();
        if (order.use_multi_currency && paymentline && paymentline.other_currency_id) {
            var amt = (this.currency_by_id[paymentline.currency_id].rate * change) / this.currency.rate
            amt = parseFloat(round_di(amt, 4));
            return amt
        } else {
            return Math.max(0, change);
        }
    },

    changeTextmc() {
        let order = this.getOrder();
        let payment_ids = order.payment_ids.filter((p) => !p.is_change);
        if (this.config.enable_multi_currency && payment_ids.length == 1 && payment_ids[0].other_currency_id) {
            var amt = (payment_ids[0].other_currency_id.rate * order.change) / this.currency.rate
            amt = parseFloat(round_di(amt, 4));
            amt = this.format_currency_n_symbol(amt, 0.0001);
            var currency_id = payment_ids[0].other_currency_id;
            return this.formating(amt, currency_id)
        }
        else {
            return this.env.utils.formatCurrency(order.change);
        }
    },
});

patch(PosOrder, {
    extraFields: {
        ...(PosOrder.extraFields || {}),
        use_multi_currency: {
            model: "pos.order",
            name: "use_multi_currency",
            type: "boolean",
            local: true,
        },
        
        is_multi_currency_payment: {
            model: "pos.order",
            name: "is_multi_currency_payment",
            type: "boolean",
            local: true,
        },

        reprint: {
            model: "pos.order",
            name: "reprint",
            type: "boolean",
            local: true,
        },
    },
});


patch(PosOrder.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        var self = this;
        self.use_multi_currency = self.use_multi_currency || false;
        self.multi_payment_lines = self.multi_payment_lines || [];
        self.is_multi_currency_payment = self.is_multi_currency_payment || false;
        self.reprint = self.reprint || true;
        self.currencie_data = self.currencie_data || {}
    },
});

patch(PosPayment, {
    extraFields: {
        ...(PosPayment.extraFields || {}),
        currency_id: {
            model: "pos.payment",
            name: "currency_id",
            type: "number",
            local: true,
        },

        otc_amount: {
            model: "pos.payment",
            name: "otc_amount",
            type: "float",
            local: true,
        },
    },
});


patch(PosPayment.prototype, {
    setup(vals) {
        super.setup(...arguments);
        var self = this;
        self.currency_id = vals.currency_id || false;
        self.other_currency_id = vals.other_currency_id ? self.models['res.currency'].getBy('id',vals.other_currency_id) : false;
        self.other_currency_rate = vals.other_currency_rate || false;
        self.other_currency_amount = vals.other_currency_amount || 0.0;
        self.is_multi_currency_payment = vals.is_multi_currency_payment || false;
        self.otc_amount = vals.otc_amount || 0;
    },
});
