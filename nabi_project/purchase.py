# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
from datetime import datetime
from dateutil import parser
import time

class purchase_order(osv.osv):
    _inherit="purchase.order"
    _columns={
        "projet":               fields.many2one('project.project','Projet'),
        "analytic_account_id" : fields.related('projet','analytic_account_id',readonly=True,type="many2one", relation="account.analytic.account",string=_("Compte analytique"),store=True),         
        "demande_achat" :       fields.char(_("demande achat")), 
        "odt" :                 fields.many2one('project.ods',string=_("Numéro de travail")), 
        "addresse" :            fields.related('odt','address',readonly=True,type="many2one", relation="project.address",string=_("Addresse de livraison"),store=True), 

    
    
    }
    
class purchase_order_line(osv.osv):
    _inherit="purchase.order.line"
    _columns={
        "odt" :           fields.many2one('project.ods',string=_("Numéro de travail")), 
    }    
