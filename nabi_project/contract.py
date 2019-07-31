# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class purchase_contract(osv.osv):
    _name = "purchase.contract"
    _description = "Project"
    _inherits = {'account.analytic.account': "analytic_account_id",
                 }
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _columns={
        'analytic_account_id' : fields.many2one('account.analytic.account','Compte'),
        
    
    }

class purchase_contract_price(osv.osv):
    _name="purchase.contract.price"
