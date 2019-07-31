# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class category(osv.osv):
    _inherit="product.category"
    def get_code(self,cr,uid,categ_id):
        o_categ = self.pool['product.category']
        pref = ''
        for c in o_categ.browse(cr,uid,categ_id):
            print "###################  categ #####################"
            print c.parent_id.id
            pref = c['code'] or ''
            if c.parent_id :
                ppref =  o_categ.get_code(cr,uid,c.parent_id.id) or False
                pref =  ppref and (ppref +'-'+pref) or pref
        return pref or ''
        
    _columns={
        'code'    : fields.char('Code' , size=3 , required= True),
        'article' : fields.one2many('product.template','categ_id','Articles'),
        'ss_categ' : fields.one2many('product.category','parent_id',u'Sous-catégories'),
        'active':   fields.boolean('Actif',default=True),
    }
        
class article(osv.osv):
    _inherit="product.template"
    def gen_code(self,cr,uid,id,cat_ids, cur_code):
        cat_id = cat_ids or False
        code = ''

      
        if  cat_id  :
            print "##################### categ_id ######################"
            print cat_ids
            o_categ = self.pool['product.category']
            prefixe=''
            prefixe = o_categ.get_code(cr,uid,cat_id)
            cr.execute("""
                select  right(default_code,5) 
                from    product_template t, product_product p
                where   categ_id = """+str(cat_id)+""" 
                    and default_code is not null
                    and t.id = p.product_tmpl_id
                
                order by right(default_code,5)  desc
                limit 1
            
            """)
            inc = cr.fetchone() or [0]
            inc0 = int(inc[0]) or 0

            answer = None
            while True:
                suffix = '0000%s' % (inc0 + 1)
                code = prefixe and (prefixe + "-" + suffix[-5:]) or False
                print "##################### code = %s ######################" % code
                 
                if self.pool['product.template'].search(cr,uid,[('default_code','=',code)]):
                    inc0 = inc0 + 1 or 1
                    
                else: break
                
            
                
                

        return {'value':{'default_code':code}}
