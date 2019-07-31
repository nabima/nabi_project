# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
from datetime import datetime,timedelta
from dateutil import parser
import time

class fleet_category(osv.osv):
    _name="fleet.category"
    _columns={
        "name":fields.char("Name"),
        'prix_int_carb':    fields.float('Prix interne horaire avec carburant'),
        'prix_int':         fields.float('Prix interne journalier sans carburant '),
        'prix_ext_carb':    fields.float('Prix externe horaire avec carburant'),
        'prix_ext':         fields.float('Prix externe journalier sans carburant '),
    }

    
class fleet_fleet(osv.osv):
    _name="fleet.fleet"
    
    def tt_cout(self,cr,uid,ids,field,arg,context=None):
        
        res = {}
        for o in self.browse(cr,uid,ids):
            res[o.id]               = {'tt_cout' : 0.0, 'tt_revenu':0.0}
            res[o.id]['tt_cout']    = o.vehicle_ids and sum([x['tt_cout']    for x in o.vehicle_ids]) or 0.0
            res[o.id]['tt_revenu']  = o.vehicle_ids and sum([x['tt_revenu']  for x in o.vehicle_ids]) or 0.0
        return res
        
        
    _columns={
        'name' :        fields.char('name'),
        'vehicle_ids':  fields.one2many('fleet.vehicle','flotte','Véhicules'),
        'type':         fields.selection(string="Type", selection=(('i','Interne'),('l','Location')), default="i"),
        'tt_cout':      fields.function(tt_cout,string="Compte Charges", type="float" ,multi="cout",store={
                                        'fleet.vehicle' : (lambda s,c,u,i,x=None: [o.flotte.id for o in s.browse(c,u,i)] ,['write_date'],10),
                                        'project.fleet.affectation' : (lambda s,c,u,i,x=None: [o.vehicle_id.flotte.id for o in s.browse(c,u,i)] ,['state','write_date'],10),
                                        }) ,
        'tt_revenu':    fields.function(tt_cout,string="Compte Produits", type="float" ,multi="cout",store={
                                        'fleet.vehicle' : (lambda s,c,u,i,x=None: [o.flotte.id for o in s.browse(c,u,i)] ,['write_date'],10),
                                        'fleet.vehicle.cost' : (lambda s,c,u,i,x=None: [o.vehicle_id.flotte.id for o in s.browse(c,u,i)] ,['amount'],10),
                                        }) ,
    }

class fleet(osv.osv):
    _inherit="fleet.vehicle"
    

    def tt_cout(self,cr,uid,ids,field,arg,context=None):
       
        co = self.pool['fleet.vehicle.cost']
        ro = self.pool['project.fleet.affectation']
        res = {}
        for o in self.browse(cr,uid,ids):
            res[o.id] = {'tt_cout' : 0.0, 'tt_revenu':0.0}

            c = co.search_read(cr,uid,[('vehicle_id','=',o.id)])
            res[o.id]['tt_cout'] = c and  sum([x['amount']  for x in c]) or 0.0

            r = ro.search_read(cr,uid,[('vehicle_id','=',o.id)])
            res[o.id]['tt_revenu'] =  r and sum([x['tt_amount']  for x in r]) or 0.0

        return res
    
    _columns={
        "ref":          fields.char('Reference'),
        'odometer_unit':fields.selection([('kilometers', 'Kilometers'),('miles','Miles'),('heure','Heure')], 'Odometer Unit', help='Unit of the odometer ',required=True),
        "disponible":   fields.boolean("Disponible" , default=True),
        'affectation':  fields.one2many('project.fleet.affectation','vehicle_id','Affectations',ondelete="restrict"),
        'flotte':       fields.many2one('fleet.fleet', 'flotte'),
        'type':         fields.selection(string="Type", selection=(('i','Interne'),('l','Location')), default="i"),
        'prix_carb':    fields.float('Prix horaire avec carburant '),
        'prix':         fields.float('Prix journalier sans carburant '),
        'categ_id':     fields.many2one('fleet.category','Catégorie fonctionnelle'),
        'tt_cout':      fields.function(tt_cout,string="Compte Charges", type="float" ,multi="cout",store={
                                        'fleet.vehicle.cost' : (lambda s,c,u,i,x=None: [o.vehicle_id.id for o in s.browse(c,u,i)] ,['amount'],10),
                                        }) ,
        'tt_revenu':    fields.function(tt_cout,string="Compte Produits", type="float" ,multi="cout",store={
                                        'project.fleet.affectation' : (lambda s,c,u,i,x=None: [o.vehicle_id.id for o in s.browse(c,u,i)] ,['state','write_date'],10),
                                        }) ,
        'tarif':        fields.one2many('fleet.vehicle.tarif','vehicle_id','Tarifs unitaires'),
        
        
        
    }
    
    
    def on_change_categ(self, cr, uid, ids, categ,t, context=None):
        p = self.pool.get('fleet.category').browse(cr, uid, categ, context=context)
        res = {}
        if p:
        
            res = {'value': {
                        'prix':       ( t == 'i') and p.prix_int        or p.prix_ext       or False ,
                        'prix_carb':  ( t == 'i') and p.prix_int_carb   or p.prix_ext_carb  or False ,
                                                       
                    }}
        return res

       
    def name_get(self, cr, uid, ids, context=None): 
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, (project.ref and (project.ref + ' | ') or '') + project.name   ))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('ref', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))    
        
class fleet_vehicle_tarif(osv.osv):
    _name="fleet.vehicle.tarif"
    _columns = {
        'vehicle_id' :  fields.many2one('fleet.vehicle',u'Véhicule'),
        'name':         fields.many2one('fleet.unit',u'Unités'),
        'price':        fields.float('Prix unitaire'),
    }

class fleet_unit(osv.osv):
    _name = 'fleet.unit'    
    _columns={
        'name' : fields.char(u'Unité'),
    }
    
class fleet_intervention(osv.osv):
    _inherit="fleet.vehicle.log.services"
    _columns={
        "operation_caisse": fields.many2one('account.bank.statement.line','Operation de caisse' ),
        }
        
class fleet_plan_besoin_line(osv.osv):
    _name="fleet.plan.besoin.line"
    _columns={
        "parent":   fields.many2one('fleet.plan.besoin','plan' ),
        'type':     fields.many2one('fleet.vehicle.model', 'Engin'),
        'qte':      fields.float('Nombre'),
        'qte_dispo':fields.float('Nombre dispo'), 
        }          
class fleet_plan_besoin_location(osv.osv):
    _name="fleet.plan.location"
    _columns={
        "plan":   fields.many2one('fleet.plan.besoin','plan' ),
        'type':     fields.many2one('fleet.vehicle.model', 'Engin'),
        'qte':      fields.float('Nombre'),
        'affectation': fields.many2one('project.ods','ODT'),
        
        } 

class fleet_plan_affectation(osv.osv):
    _name="fleet.plan.affectation"
    _columns={
        "plan":   fields.many2one('fleet.plan.besoin','plan' ),
        'vehicle':     fields.many2one('fleet.vehicle', 'Engin'),
        'affectation': fields.many2one('project.ods','ODT'),
        
        }
                
class fleet_plan_besoin(osv.osv):
    _name="fleet.plan.besoin"
    _columns={
        "name":         fields.date('Date planification' ),
        "line":         fields.one2many('fleet.plan.besoin.line','parent','Lignes'),
        "location":     fields.one2many('fleet.plan.location','plan','Ordre de location'),
        "affectation":  fields.one2many('fleet.plan.affectation','plan','Affectation'),
        "state": fields.selection(string="Etat", selection=[('n','Nouveau'),('v','Validé')]),
        
        }   

     
        
class fleet_vehicle_log_fuel(osv.osv):
    
    _inherit="fleet.vehicle.log.fuel"
    
    def consommation(self,cr,uid,ids,field_name,arg,context):
        res = {}
        
        for o in self.browse(cr,uid,ids):
            od_ids = self.search(cr,uid,[('vehicle_id','=',o.vehicle_id.id),('date','<=',o.date),('odometer','!=',o.odometer),('id','!=',o.id)])
            od_o   = self.browse(cr,uid,od_ids).sorted(key=lambda x:x.date,reverse=True)
           
            odometer_last   = od_o and max([x.odometer for x in od_o[:1] ]) or 0.0
            odometer_count  = o.odometer - odometer_last or False
            consommation    = odometer_count and (100 *  o.liter / odometer_count) or 0.0
            
            res[o.id] = {
                'odometer_last':odometer_last,
                'odometer_count':odometer_count,
                'consommation':consommation,
            
            }
            
            
        return res
            
    
    _columns = {
        'type':                 fields.selection(string='Type',selection=(('i','Interne'),('e','Externe'))),
        'vehicle_dest':         fields.selection(string="Déstination", selection=(('i','Interne'),('l','Location'),('d','Dépôt'),), default="i"),
        'no_bon_ext':           fields.many2one('fleet.vehicle.log.fuel', 'No. Bon station'),
        'no_bon_stock':         fields.many2one('stock.picking','No. Bon stock'),
        'matricule':            fields.char('Matricule'),
        'chauffeur':            fields.many2one('hr.employee','Chauffeur'),
        'analytic_account_id':  fields.many2one('project.project','Projet'),
        'odt':                  fields.many2one('project.ods','Ordre de travail'),
        'odometer_last':        fields.function(consommation, string="Ancien compteur",        type="float", multi="calc", store=True),
        'odometer_count':       fields.function(consommation, string="Kélométres parcourus",   type="float", multi="calc", store=True),
        'consommation':         fields.function(consommation, string="Consommation /100KM",    type="float", multi="calc", store=True , group_operator="avg"),
        
            }
    _rec_name = 'inv_ref'

class fleet_vehicle_log_fuel_int(osv.osv):
    _name="fleet.vehicle.log.fuel.int"
    _inherit="fleet.vehicle.log.fuel"     
    _columns={
        'vehicle_id' : fields.char(''),
        'chauffeur': fields.many2one('hr.employee','Chauffeur'),
        
    }   
            
class fleet_intervention_int(osv.osv):
   
    _inherit="fleet.vehicle.log.services" 
    
    def couts(self,cr,uid,ids,field,arg,context=None):
        res= {}
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = {'cout_mo':         0.0,
                        'cout_pdr':         0.0,
                        'cout_achat':       0.0,
                        'cout_prestation':  0.0,
                    }
            
            
            
            res[o.id]['cout_mo']        = o.intervenant and sum([(x.employee.name.taux_charge or 0.0) * (x.temps or 0.0) for x in o.intervenant])    or 0.0
            res[o.id]['cout_pdr']       = o.pdr         and sum([(x.article.standard_price or 0.0) * (x.qte or 0.0) for x in o.pdr])            or 0.0  
            res[o.id]['cout_achat']     = o.achat       and sum([(x.qte or 0.0 )* (x.prix or 0.0)                   for x in o.achat])          or 0.0
            res[o.id]['cout_prestation']= o.prestation  and sum([(x.prix or 0.0)                                    for x in o.prestation])     or 0.0
            
            
        return res
    _columns={
        'type':         fields.selection(string='Type',selection=(('i','Interne'),('e','Externe'))), 
        'intervenant' : fields.one2many('fleet.intervention.int.intervenant','parent','Intervenants'),
        'pdr' :         fields.one2many('fleet.intervention.int.pdr', 'parent', 'Pièces de rechange magasin'),
        'achat' :       fields.one2many('fleet.intervention.int.achat', 'parent', 'Achats'),
        'prestation' :  fields.one2many('fleet.intervention.int.prestation', 'parent', 'Prestation'),
        'cout_mo' :     fields.function(couts,multi="couts",store=True,string="Coût main d'oeuvre"),
        'cout_pdr' :    fields.function(couts,multi="couts",store=True,string="Coût PDR magasin"),
        'cout_achat' :  fields.function(couts,multi="couts",store=True,string="Coût PDR Achat"),
        'cout_prestation':fields.function(couts,multi="couts",store=True,string="Coût prestation"),
        
    }   
    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, 'INT/%s' % project.id   ))
        return result
    
    #def write(self, cr, uid, ids, vals, context=None):
      #  o = self.browse(cr,uid,ids)
     #   amount = o.cout_mo + o.cout_pdr + o.cout_achat + o.cout_prestation
     #   vals.update({'amount':amount})

      #  return super(self,fleet_intervention_int).write(cr, uid, ids, vals,context)  
    
class fleet_intervention_int_intervenant(osv.osv):
    _name="fleet.intervention.int.intervenant"
    _columns={
        'parent':fields.many2one('fleet.vehicle.log.services','parent'),
        'employee' : fields.many2one('fleet.intervenant', 'Intervenant'),
        'temps': fields.float('Temps en heures'),    
    }
class fleet_intervenant(osv.osv):
    _name="fleet.intervenant"
    _columns={
        'name':fields.many2one('hr.employee','Employee'),
   
    }    
    
class stock_picking(osv.osv):
    _inherit="stock.picking"
    _columns={
        'fleet_intervention_id':fields.many2one('fleet.vehicle.log.services','Intervention Maintenance' ),
   
    }     
    
class fleet_intervention_int_prestation(osv.osv):
    _name="fleet.intervention.int.prestation"
    
    _columns={
        'parent'    : fields.many2one('fleet.vehicle.log.services','parent'),
        'detail'    : fields.text( 'Détail'),        
        'prix'      : fields.float('Prix unitaire HT'),    
        'fournisseur': fields.many2one('res.partner', 'Fournisseur'), 
        'facture'   : fields.char('Facture / BL'), 
    }

class fleet_intervention_int_achat(osv.osv):
    _name="fleet.intervention.int.achat"
    
    _columns={
        'parent'    : fields.many2one('fleet.vehicle.log.services','parent'),
        'detail'    : fields.char( 'Détail'),
        'qte'       : fields.float( 'Quantité'),        
        'prix'      : fields.float('Prix unitaire HT'),    
        'fournisseur': fields.many2one('res.partner', 'Fournisseur'), 
        'facture'   : fields.char('Facture / BL'), 
    }    
class fleet_intervention_int_pdr(osv.osv): 
    _name="fleet.intervention.int.pdr"
    _auto=False
    _columns={
        'parent':fields.many2one('fleet.vehicle.log.services','parent'),
        'article' : fields.many2one('product.product', 'Article'),
        'qte': fields.float('Quantité'),    
    }    
    def init(self, cr):
       
        
        cr.execute("""CREATE or REPLACE VIEW fleet_intervention_int_pdr as 
            select      row_number() over() as id,
                p.fleet_intervention_id as parent,
                o.product_id as article,
                sum(o.product_qty) as qte
                
                
            from stock_picking p, stock_pack_operation o
            where   p.id = o.picking_id
            group by p.fleet_intervention_id, o.product_id
            
            
                 
            """)

class project_fleet_affectation_line(osv.osv):
    _name="project.fleet.affectation.line"
    
    def _amount(self,cr,uid,ids,field,arg,context=None):
        res= {}
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = {'amount':0.0,
                        'nb_jrs':0.0,
                        'prix':0.0,'unit':'h',
                    }
            pj        = o.parent.vehicle_id.prix or 0.0
            ph   = o.parent.vehicle_id.prix_carb or 0.0
             
            
            d = o.date_debut    and parser.parse(o.date_debut)  or False
            f = o.date_fin      and parser.parse(o.date_fin)    or False
            
            nbj  = o.parent.full_day and ((f-d).days or 1  ) or ((f and d) and f > d ) and (f-d).seconds / 3600  or 0.0
            unit = o.parent.full_day and 'j'                 or 'h'                                              
            
            res[o.id]['amount'] = o.parent.unit_price and o.parent.unit_price *  o.qty  or o.parent.full_day and  pj  or  nbj * ph or 0.0
            res[o.id]['nb_jrs'] =  nbj  or 0.0
            res[o.id]['prix']   =  o.parent.unit_price and o.parent.unit_price or o.parent.full_day and  pj  or  ph or 0.0
            res[o.id]['unit']   =  unit or 'h'
            
            
        return res
    
    _columns={
        'analytic_account_id':  fields.many2one('project.project','Projet'),
        'odt':                  fields.many2one('project.ods','Ordre de travail'),
        'date_debut':           fields.datetime('De'),
        'date_fin':             fields.datetime('A'),
        'parent' :              fields.many2one('project.fleet.affectation','parent'),
        'amount' :              fields.function(_amount, type="float",      string="Montant total", multi="calc", store=True),
        'nb_jrs' :              fields.function(_amount, type="float",      string="Qte",           multi="calc", store=True),
        'unit':                 fields.function(_amount, type="selection",  string="Unit.",         multi="calc", selection=(('j','Jrs.'),('h','Hrs.'))),
        'prix':                 fields.function(_amount, type="float",      string="Prix Unit.",    multi="calc",store=True,group_operator = 'avg'),
        
        'name' :                fields.char(string='Numéro de bon', store="True",   related="parent.name"),
        'full_day':             fields.boolean( related="parent.full_day",string='Journée entière', store="True"),
        'vehicle_id':           fields.many2one('fleet.vehicle',string='Véhicule/Engin',ondelete="restrict",related="parent.vehicle_id", store="True"),
        'chauffeur' :           fields.many2one('hr.employee' , string='Chauffeur',related="parent.chauffeur", store="True"),
        'date' :                fields.date(    related="parent.date",string='Date', store="True"),
        'qty':                  fields.float(u'Qté'),
        
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(project_fleet_affectation_line,self).write(cr, uid, ids, vals,context) 
        o = self.browse(cr,uid,ids)
        self.pool['project.fleet.affectation'].write(cr,uid,o.parent.id,{'unit':o.unit},context)

        return res
    
    def create(self, cr, uid, vals, context=None):
        res = super(project_fleet_affectation_line,self).create(cr, uid, vals,context) 
        o = self.browse(cr,uid,res)
        self.pool['project.fleet.affectation'].write(cr,uid,o.parent.id,{'unit':o.unit},context)

        return res        
    
    
class project_fleet_affectation(osv.osv):
    _name="project.fleet.affectation"
    
    def _amount(self,cr,uid,ids,field,arg,context=None):
        res= {}
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = {'amount':0.0,'tt_heures':0.0,'unit':'h',}

            res[o.id]['amount']     = sum([x.amount  for x in o.line]) or 0.0
            res[o.id]['tt_heures']  = sum([x.nb_jrs  for x in o.line]) or 0.0
            res[o.id]['unit']       = o.full_day and 'j' or 'h'
            
            
        return res
    
    def _tt_amount(self,cr,uid,ids,field,arg,context=None):
        res= {}
        
        for o in self.browse(cr,uid,ids):
            res[o.id] = sum([x.qty for x in o.line]) * (o.unit_price or 0.0)
            
        return res
    
            
    READONLY_STATE = {
        'v': [('readonly', True)],
        'n': [('readonly', False)],
      
    }     
            
    _columns={
        'state':                fields.selection(string="state",selection=[('n','Brouillon'),('v','Validé')], default="n"),
        'name' :                fields.char('Numéro de bon'),

        'full_day':             fields.boolean('Journée entière'),
        'vehicle_id':           fields.many2one('fleet.vehicle', 'Véhicule/Engin',ondelete="restrict"),
        'chauffeur' :           fields.many2one('hr.employee' , 'Chauffeur'),
        'date' :                fields.date('Date'),
        'line':                 fields.one2many('project.fleet.affectation.line','parent','Lignes'),
        'amount' :              fields.function(_amount, type="float", string="Montant total",multi="calc", store=True),
        'tt_heures' :           fields.function(_amount, type="float", string="Montant total",multi="calc", store=True),
        'unit':                 fields.function(_amount, type="selection",  string="Unit.",         multi="calc", selection=(('j','Jrs.'),('h','Hrs.'))),
        'unit_id':              fields.many2one('fleet.vehicle.tarif',u'Unité de prix'),
        'unit_price':           fields.related('unit_id','price',string="Prix unitaire", type="float" , store=True),
        'analytic_account_id':  fields.many2one('project.project','Projet'),
        'odt':                  fields.many2one('project.ods','Ordre de travail'),
        'tt_amount':            fields.function(_tt_amount, string="Montant total",type="float",store={
                                                'project.fleet.affectation' : (lambda s,c,u,i,x=None: i ,['line'],10)
                                                }),
        
        
    }    
    
    
    
    
     

            
      
