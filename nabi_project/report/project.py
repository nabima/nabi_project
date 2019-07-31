# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time

class project_project(osv.osv):
    _inherit = "project.project"
    
    def ca_calc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for o in self.browse(cr,1,ids,context=context):    
            res[o.id] =     {'ca_enc_prod'  :0.0,
                            'ca_prod'       :0.0,
                            'ca_enc_attache':0.0,
                            'ca_attache'    :0.0,
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
            ca_attache      = 0.0
            ca_facture      = 0.0
            paiement        = 0.0
            cout_matiere    = 0.0
            cout_service    = 0.0
            cout_materiel   = 0.0
            cout_soutraitance= 0.0
            cout_rh         = 0.0
            cout_parc       =0.0
            
            s =  o.situation and o.situation.sorted(key=lambda x:x.date, reverse=True)[0] or False
                        
            for r in filter(lambda x: s and (x.date > s['date']) or (not s and True)  or False ,o.rapport) :
                for l in r.prod : 
                    ca_enc_prod         = ca_enc_prod                                   + ((l.qte or 0.0) * (l.name.prix_net or 0.0))
                    ca_prod             = ca_prod       + (r.state in ('c','a','t')) and  ((l.qte or 0.0) * (l.name.prix_net or 0.0)) or 0.0
                
                cout_soutraitance   = cout_soutraitance + (r.total_amount_stt or 0.0)
            
            for a in filter(lambda x: s and (x.date > s['date']) or (not s and True)  or False ,o.attachement) :  
                for l in a.lines : 
                    ca_enc_attache = ca_enc_attache                       + ((l.qte or 0.0) * (l.name.prix_net or 0.0)) 
                    ca_attache     = ca_attache     + ((a.state == 'c') and  ((l.qte or 0.0) * (l.name.prix_net or 0.0)) or 0.0)
                    ca_facture     = ca_facture     + ((a.state == 'f') and  ((l.qte or 0.0) * (l.name.prix_net or 0.0)) or 0.0)
            
            for ach in filter(lambda x: s and (x.date_planned > s['date']) or (not s and True)  or False ,o.analytic_account_id.achat_matiere):
                cout_matiere = cout_matiere + ach.price_subtotal
            
            for ach in filter(lambda x: s and (x.date_planned > s['date']) or (not s and True)  or False ,o.analytic_account_id.achat_service):
                cout_service = cout_service + ach.price_subtotal
            
            for ach in filter(lambda x: s and (x.date_planned > s['date']) or (not s and True)  or False ,o.analytic_account_id.achat_materiel):
                cout_materiel = cout_materiel + ach.price_subtotal
                                                
            for ach in filter(lambda x: s and (x.date_fin > s['date']) or (not s and True)  or False ,o.analytic_account_id.imputation_rh):
                cout_rh = cout_rh + ach.amount
            
            for ach in filter(lambda x: s and (x.date > s['date']) or (not s and True)  or False ,o.affectation_parc):
                cout_parc = cout_parc + ach.amount
            
    
            
            res[o.id]['ca_enc_prod']        = s and s['production']  + ca_enc_prod      or ca_enc_prod
            res[o.id]['ca_prod']            = s and s['production']  + ca_prod          or ca_prod
            res[o.id]['ca_enc_attache']     = s and s['attachement'] + ca_enc_attache   or ca_enc_attache
            res[o.id]['ca_attache']         = s and s['attachement'] + ca_attache       or ca_attache
            res[o.id]['ca_facture']         = s and s['facturation'] + ca_facture       or ca_facture
            res[o.id]['paiement']           = s and s['paiement']    + paiement         or paiement
            res[o.id]['cout_matiere']       = s and s['matiere']     + cout_matiere     or cout_matiere
            res[o.id]['cout_service']       = s and s['service']     + cout_service     or cout_service
            res[o.id]['cout_materiel']      = s and s['materiel']    + cout_materiel    or cout_materiel
            res[o.id]['cout_soutraitance']  = s and s['soutraitance']+ cout_soutraitance or cout_soutraitance
            res[o.id]['cout_rh']            = s and s['charge_rh']   + cout_rh          or cout_rh
            res[o.id]['cout_parc']          = s and s['parc']        + cout_parc        or cout_parc
            # TODO : apres repartition
            res[o.id]['cout_indirecte']     = s and s['cout_indirecte'] or 0.0
            
            res[o.id]['cout_complet'] = res[o.id]['cout_matiere'] + res[o.id]['cout_service'] + res[o.id]['cout_materiel'] + res[o.id]['cout_soutraitance'] + res[o.id]['cout_rh'] +  res[o.id]['cout_parc'] +  res[o.id]['cout_indirecte']  
            res[o.id]['marge']        = res[o.id]['ca_facture'] +res[o.id]['ca_attache'] +res[o.id]['ca_prod'] - res[o.id]['cout_complet']
            res[o.id]['avancement']   = o.mtt_min and (res[o.id]['ca_facture'] +res[o.id]['ca_attache'] +res[o.id]['ca_prod'] ) / o.mtt_min or 0.0
            
                         
        return res
    
    def _get_project_achat(s,c,u,i,t=None):
        aa = [x.account_analytic_id.id for x in s.browse(c,u,i)]
        pids  = s.pool['project.project'].search(c,u,[('analytic_account_id','in',aa)])
        return  pids 
    
    def _get_project_parc(s,c,u,i,t=None):
        p = []
        for o in s.browse(c,u,i):
            p += [x.analytic_account_id.id for x in o.line if x.analytic_account_id != False ] 
        
        return list(set(p)) or []
                      
    _columns = { 
        'ca_enc_prod':      fields.function(ca_calc,multi="clc",string='CA Encours de prod',        type='float', store={
                                                'project.rapport'   : (lambda s,c,u,i,ctx=None:[x.project.id for x in s.browse(c,u,i)] ,['write_date','prod','state','project'],10),
                                                'project.situation' : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'ca_prod':          fields.function(ca_calc,multi="clc",string='CA prod',                   type='float', store={
                                                'project.rapport'   : (lambda s,c,u,i,ctx=None:[x.project.id for x in s.browse(c,u,i)] ,['write_date','prod','state','project'],10),
                                                'project.situation' : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'ca_enc_attache':   fields.function(ca_calc,multi="clc",string="CA Encours d'attachement",  type='float', store={
                                                'project.attachement': (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)] ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),       
        'ca_attache':       fields.function(ca_calc,multi="clc",string='CA Attachement',            type='float', store={
                                                'project.attachement': (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)] ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }), 
        'ca_facture':       fields.function(ca_calc,multi="clc",string='CA facturation',            type='float', store={
                                                'project.attachement': (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)] ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }), 
        'paiement':         fields.function(ca_calc,multi="clc",string='paiement',                  type='float', store=True),
        'cout_matiere':     fields.function(ca_calc,multi="clc",string='Coût matière',              type='float', store={
                                                'purchase.order.line': (_get_project_achat ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }), 
        'cout_materiel':    fields.function(ca_calc,multi="clc",string='Coût Achat Matériel',       type='float', store={
                                                'purchase.order.line': (_get_project_achat ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }), 
        'cout_rh':          fields.function(ca_calc,multi="clc",string='Coût RH',                   type='float', store=True),
        'cout_service':     fields.function(ca_calc,multi="clc",string='Coût Services',             type='float', store={
                                                'purchase.order.line': (_get_project_achat ,['write_date','lines','state','projet'],10),
                                                'project.situation'  : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }), 
        'cout_soutraitance':fields.function(ca_calc,multi="clc",string='Soutraitance',              type='float', store={
                                                'project.rapport'   : (lambda s,c,u,i,ctx=None:[x.project.id for x in s.browse(c,u,i)] ,['write_date','stt','state','project'],10),
                                                'project.situation' : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'cout_parc':        fields.function(ca_calc,multi="clc",string='Coût Parc/engins',          type='float', store={
                                                'project.fleet.affectation'     : (_get_project_parc,['write_date','line','state'],10),
                                                'project.situation'             : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'cout_indirecte':   fields.function(ca_calc,multi="clc",string='Coûts indirects',           type='float', store=True),
        'marge':            fields.function(ca_calc,multi="clc",string='La Marge',                  type='float', store={
                                                'project.project'     : (lambda s,c,u,i,t=None: i,['write_date','state'],10),
                                                'project.situation'             : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'cout_complet':     fields.function(ca_calc,multi="clc",string='Le cout complet',           type='float', store={
                                                'project.project'     : (lambda s,c,u,i,t=None: i,['write_date','state'],10),
                                                'project.situation'             : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        'avancement':       fields.function(ca_calc,multi="clc",string='Avancement',                type='float', store={
                                                'project.project'     : (lambda s,c,u,i,t=None: i,['write_date','state'],10),
                                                'project.situation'             : (lambda s,c,u,i,ctx=None:[x.projet.id for x in s.browse(c,u,i)]  ,['write_date','projet'],10)
                                            }),
        
        #'achat_matiere' : fields.one2many("purchase.order.line",            "account_analytic_id", related="analytic_account_id.achat_matiere" , string='Achat matière' ),
        #'achat_materiel': fields.one2many("purchase.order.line",            "account_analytic_id", related="analytic_account_id.achat_materiel", string='Achat Matériel'),
        #'imputation_rh' : fields.one2many('project.hr.pay.15.imputation',   'analytic_account_id', related="analytic_account_id.imputation_rh" , string='Imputation RH'),
        #'achat_service' : fields.one2many("purchase.order.line",            "account_analytic_id", related="analytic_account_id.achat_service" , string='Achat Services'),
        
        'affectation_parc':fields.one2many('project.fleet.affectation.line','analytic_account_id','Affetation parc'),
        
    }
    
class account_analytic_account(osv.osv):
    _inherit="account.analytic.account"    
    _columns={
        'achat_matiere' : fields.one2many('purchase.order.line',         'account_analytic_id', string='Achat matière' , domain=[('product_id.type','=','product')]),
        'achat_materiel': fields.one2many('purchase.order.line',         'account_analytic_id', string='Achat Matériel', domain=[('product_id.type','=','service')]),
        'imputation_rh' : fields.one2many('project.hr.pay.15.imputation','analytic_account_id', string='Imputation RH'),
        'achat_service' : fields.one2many('purchase.order.line',         'account_analytic_id', string='Achat Services', domain=[('product_id.type','=','service')]),
        
    }
