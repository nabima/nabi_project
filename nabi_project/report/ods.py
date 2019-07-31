# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class project_ods(osv.osv):
    _inherit = "project.ods"

    def _get_ods_prod_id(self, cr,uid,ids,context=None):
        return [s.lot.id for s in self.browse(cr, uid, ids, context=context)]

    def _get_ods_prod_line_id(self, cr,uid,ids,context=None):
        #if not isinstance(ids, (int, long)):
            #[ids] = ids
        return [s.parent.lot.id for s in self.browse(cr, uid, ids, context=context)]
                               
    def _get_ods_rh_id(self, cr,uid,ids,context=None):
        return [s.ods.id for s in self.browse(cr, uid, ids, context=context)]
        
    def _get_ods_attach_id(self, cr,uid,ids,context=None):
        return [s.ods.id for s in self.browse(cr, uid, ids, context=context)]  

    def _get_ods_achat_id(self, cr,uid,ids,context=None):
        return [s.odt.id for s in self.browse(cr, uid, ids, context=context) ]  
    
    def _get_ods_parc_id(self, cr,uid,ids,context=None):
        return [s.odt.id for s in self.browse(cr, uid, ids, context=context) ]  
    
    
    
    
    def ca_calc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for o in self.browse(cr,1,ids,context=context):    
            res[o.id] =     {'ca_enc_prod'  :0.0,
                            'ca_prod'       :0.0,
                            'ca_enc_attache':0.0,
                            'ca_attachement':0.0,
                            'ca_facture'    :0.0,  
                            'paiement'      :0.0,  
                            'cout_matiere'  :0.0,
                            'cout_service'  :0.0,
                            'cout_materiel' :0.0,
                            'cout_soutraitance':0.0,
                            'cout_rh'       :0.0,
                            'cout_parc'     :0.0,
                            'cout_indirecte':0.0,
                            'cout_complet'  :0.0,
                            'marge'         :0.0,
                            'avancement'    :0.0,
                                       
                            } 
                                   
            ca_enc_prod     = 0.0
            ca_prod         = 0.0
            ca_enc_attache  = 0.0
            ca_attachement  = 0.0
            ca_facture      = 0.0
            paiement        = 0.0
            cout_matiere    = 0.0
            cout_service    = 0.0
            cout_materiel   = 0.0
            cout_soutraitance= 0.0
            cout_rh         = 0.0
            cout_parc       =0.0
            
                        
            for r in o.rapport_prod :
                ca_prod   = ca_prod + (r.total_amount or 0.0)
                cout_soutraitance   = cout_soutraitance + (r.total_amount_stt or 0.0)
            
            for a in o.attachement :  
                ca_attachement  = ca_attachement     + ((a.state == 'c') and  a.total_amount or 0.0)
                ca_facture      = ca_facture     + ((a.state == 'f') and  a.total_amount or 0.0)
            
            for ach in o.achat_matiere:
                cout_matiere = cout_matiere + ach.price_subtotal
            
            for ach in o.achat_service:
                cout_service = cout_service + ach.price_subtotal
            
            for ach in o.achat_materiel:
                cout_materiel = cout_materiel + ach.price_subtotal
                                                
            for ach in o.rapport_rh:
                cout_rh = cout_rh + ach.taux_charge
            
            for ach in o.affectation_parc:
                cout_parc = cout_parc + ach.amount
            
    
            
            res[o.id]['ca_prod']            =  ca_prod or 0.0
            res[o.id]['ca_attachement']     =  ca_attachement or 0.0
            res[o.id]['ca_facture']         =  ca_facture or 0.0
            res[o.id]['cout_matiere']       =  cout_matiere or 0.0
            res[o.id]['cout_service']       =  cout_service or 0.0
            res[o.id]['cout_materiel']      =  cout_materiel or 0.0
            res[o.id]['cout_soutraitance']  =  cout_soutraitance or 0.0
            res[o.id]['cout_rh']            =  cout_rh or 0.0
            res[o.id]['cout_parc']          =  cout_parc or 0.0
            # TODO : apres repartition
            res[o.id]['cout_indirecte']     =  0.0
            
            res[o.id]['cout_complet'] = res[o.id]['cout_matiere'] + res[o.id]['cout_service'] + res[o.id]['cout_materiel'] + res[o.id]['cout_soutraitance'] + res[o.id]['cout_rh'] +  res[o.id]['cout_parc'] +  res[o.id]['cout_indirecte']  
            res[o.id]['marge']        = res[o.id]['ca_facture'] +res[o.id]['ca_attachement'] + res[o.id]['ca_prod'] - res[o.id]['cout_complet']
            
                         
        return res

                      
    _columns = { 
    
        "ca_prod":       fields.function(ca_calc,multi="clc", string='CA produit', type="float",
                                        store={
                                            'project.rapport':(_get_ods_prod_id,  ['amount_total','state','project','lot','prod'],10),
                                            
                                            }),        
                                            
        'cout_soutraitance':fields.function(ca_calc,multi="clc",string='Soutraitance',      type='float', 
                                        store={'project.rapport':(_get_ods_prod_id,['total_amount_stt','state','project','lot','stt'],10)}),
                                                   
        
        "cout_rh":       fields.function(ca_calc,multi="clc", string='Charge RH',  type="float",      
                                        store={'project.rapport.attendance':(_get_ods_rh_id,    ['taux_charge','state'],10)}),        
        
        "ca_attachement":fields.function(ca_calc,multi="clc", string='CA Attache', type="float",
                                        store={'project.attachement':(_get_ods_attach_id,['amount_total','state','projet','ods','lines'],10)}),
        
        'ca_facture':       fields.function(ca_calc,multi="clc",string='CA facturation',    type='float', 
                                        store={'project.attachement':(_get_ods_attach_id,['amount_total','state','projet','ods','lines'],10)}),
        
        'cout_matiere':     fields.function(ca_calc,multi="clc",string='Coût matière',      type='float', 
                                        store={'purchase.order.line':(_get_ods_achat_id,['price_subtotal','state','odt'],10)}),
        
        'cout_materiel':    fields.function(ca_calc,multi="clc",string='Coût Achat Matériel',type='float', 
                                        store={'purchase.order.line':(_get_ods_achat_id,['price_subtotal','state','odt'],10)}),
        
        'cout_service':     fields.function(ca_calc,multi="clc",string='Coût Services',     type='float', 
                                        store={'purchase.order.line':(_get_ods_achat_id,['price_subtotal','state','odt'],10)}),
        
         
        'cout_parc':        fields.function(ca_calc,multi="clc",string='Coût Parc/engins',  type='float', 
                                        store={'project.fleet.affectation.line':(_get_ods_parc_id,['amount','analytic_account_id','odt'],10)}),
        
        'cout_indirecte':   fields.function(ca_calc,multi="clc",string='Coûts indirects',   type='float', store=True),
        
        'marge':            fields.function(ca_calc,multi="clc",string='La Marge',          type='float',
                                       store={
                                       'purchase.order.line':    (_get_ods_achat_id,['price_subtotal','state','odt'],10),
                                       'project.fleet.affectation.line':(_get_ods_parc_id,['amount','analytic_account_id','odt'],10),
                                       'project.attachement':           (_get_ods_attach_id,['amount_total','state','projet','ods','lines'],10),
                                       'project.rapport.attendance':    (_get_ods_rh_id,    ['taux_charge','state'],10),
                                       'project.rapport':               (_get_ods_prod_id,  ['amount_total','state','project','lot','prod'],10),
                                       }),
        
        'cout_complet':     fields.function(ca_calc,multi="clc",string='Le cout complet',   type='float', 
                                        store={
                                       'purchase.order.line':    (_get_ods_achat_id,['price_subtotal','state','odt'],10),
                                       'project.fleet.affectation.line':(_get_ods_parc_id,['amount','analytic_account_id','odt'],10),
                                       'project.attachement':           (_get_ods_attach_id,['amount_total','state','projet','ods','lines'],10),
                                       'project.rapport.attendance':    (_get_ods_rh_id,    ['taux_charge','state'],10),
                                       'project.rapport':               (_get_ods_prod_id,  ['amount_total','state','project','lot','prod'],10),
                                       }),
        
        #'ca_attache':       fields.function(ca_calc,multi="clc",string='CA Attachement',   type='float', store=True),
        'achat_matiere' : fields.one2many('purchase.order.line', 'odt', string=u'Achat matière' , domain=[(0,'=',1),('state','not in',('draft','cancel'))]),
        'achat_materiel': fields.one2many('purchase.order.line', 'odt', string=u'Achat Matériel', domain=[(0,'=',1),('state','not in',('draft','cancel'))]),
        'achat_service' : fields.one2many('purchase.order.line', 'odt', string='Autres achats',   domain=[('state','not in',('draft','cancel'))]),
        'affectation_parc':fields.one2many('project.fleet.affectation.line','odt','Affetation parc'),
        'partner_id'    : fields.related('project','partner_id',string="Client" , type="many2one",relation="res.partner"),
        'metier'        : fields.related('project','metier',string=u"Métier"    , type="many2one",relation="project.metier"),
        
    }
    

