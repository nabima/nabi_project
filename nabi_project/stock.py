from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
import time
import logging
_logger = logging.getLogger(__name__)

class stock(osv.osv):
    _inherit="stock.picking.type"

    _columns={        
        "nature" : fields.selection(string="Nature", selection=[(1,'Entree'),(-1,'sortie')], required=True),
    
    }

class stock_picking(osv.osv):
    _inherit="stock.picking"

    _columns={        
        "analytic_account_id" : fields.many2one("project.project",'Projet'         ),
        "camion" :              fields.char('Camion'),
        "conducteur" :          fields.char('Conducteur'),        
        "no_bl" :               fields.char('Bon de livraison'),
        "odt" :                 fields.many2one('project.ods','Ordre de travail'),
    
    }    

class stock_pack_operation(osv.osv):
    _inherit="stock.pack.operation"
    
        
        
    def _calc_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for o in self.browse(cr,uid,ids,context=context):  
            res[o.id] = { 'qte':0.0, 'analytic_account_id': False,
                'camion': '',
                'conducteur':'',
                'no_bl':'',
                'partner_id':False,
                #'nature':0,
                'qte1':0.0, 
                                
                }          
            res[o.id]['analytic_account_id']    = o.picking_id.analytic_account_id.id or False 
            res[o.id]['camion']                 = o.picking_id.camion or False
            res[o.id]['conducteur']             = o.picking_id.conducteur or False 
            res[o.id]['no_bl']                  = o.picking_id.no_bl or False 
            res[o.id]['partner_id']             = o.picking_id.partner_id.id or False 
            res[o.id]['qte']                    = (o.product_qty or 0.0) * ( o.nature or 0)    
            _logger.info('##### %s <-- %s <-- %s' , res[o.id]['qte'], o.nature, o.product_qty )
                 
        return res

    _columns={        
    
        "analytic_account_id" : fields.function(_calc_all   ,string='Projet',          type="many2one",relation="project.project"	,multi="all" ,store=True),
        "camion" :              fields.function(_calc_all   ,string='Camion',          type="char"	    ,multi="all" ,store=True),
        "conducteur" :          fields.function(_calc_all   ,string='Conducteur',      type="char"	    ,multi="all" ,store=True),        
        "no_bl" :               fields.function(_calc_all   ,string='Bon de livraison',type="char"	    ,multi="all" ,store=True),
        "partner_id" :          fields.function(_calc_all   ,string='Fournisseur',     type="many2one"  ,relation="res.partner"	,multi="all" ,store=True),
        "nature" :              fields.related('picking_id','picking_type_id','nature'   ,string="Nature",          type='selection' ,selection=[(1,'Entree'),(-1,'sortie')]),
        "qte" :                 fields.function(_calc_all   ,string='Quant'          ,type="float"     , multi="all", default=0.0, store= True),
        "prix":                 fields.related('product_id','product_tmpl_id','standard_price',type="float", string=_("Prix") ,store=True), 
        


        
    
    }    
    
    
