# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report  import report_sxw
from openerp.tools   import float_compare, float_round
from datetime        import datetime as d
from dateutil.parser import parse    as prs




import time

to_19_fr = (u'zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six',
          'sept', 'huit', 'neuf', 'dix', 'onze', 'douze', 'treize',
          'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf')
tens_fr = ('vingt', 'trente', 'quarante', 'Cinquante', 'Soixante', 'Soixante-dix', 'Quatre-vingts', 'Quatre-vingt Dix')
denom_fr = ('',
          'Mille', 'Millions', 'Milliards', 'Billions', 'Quadrillions',
          'Quintillion', 'Sextillion', 'Septillion', 'Octillion', 'Nonillion',
          'Décillion', 'Undecillion', 'Duodecillion', 'Tredecillion', 'Quattuordecillion',
          'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Icosillion', 'Vigintillion')

def _convert_nn_fr(val):
    """ convert a value < 100 to French
    """
    if val < 20:
        return to_19_fr[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_fr)):
        if dval + 10 > val:
            if val % 10:
                if dval == 70 or dval == 90:
                    return tens_fr[dval / 10 - 3] + '-' + to_19_fr[val % 10 + 10]
                else:
                    return dcap + '-' + to_19_fr[val % 10]
            return dcap

def _convert_nnn_fr(val):
    """ convert a value < 1000 to french
    
        special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        if rem == 1:
            word = 'Cent'
        else:
            word = to_19_fr[rem] + ' Cent'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nn_fr(mod)
    return word

def french_number(val):
    if val < 100:
        return _convert_nn_fr(val)
    if val < 1000:
        return _convert_nnn_fr(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_fr))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if l == 1:
                ret = denom_fr[didx]
            else:
                ret = _convert_nnn_fr(l) + ' ' + denom_fr[didx]
            if r > 0:
                ret = ret + ', ' + french_number(r)
            return ret

def amount_to_text_fr(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = french_number(abs(int(list[0])))
    end_word = french_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and ' Centimes' or ' Centime'
    final_result = start_word + ' ' + units_name +(cents_number and  (' ' + end_word + ' ' + cents_name) or '')
    return final_result.upper()



class project_bordereau_line(osv.osv):
    _name="project.bordereau.line"
    
    def prix_ca(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            coef = ( o.parent.coef and o.parent.coef or False) or o.parent.projet.coef or 1
            s = o.prix * (coef or 1)
            
            for r in o.parent.projet.retenus:
                if r.type != 'g':
                    if r.base == 'p':
                        s = s + (s * (r.ratio or 0.0) / 100)
                    else:
                        s = s + ((o.prix or 0.0) * (r.ratio or 0.0) / 100)
            res[o.id] = s or 0.0
        
        return res
    def get_bordereau(self, cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            brd_ids = []
            for b in  filter(lambda x:x.coef in (0,False), o.bordereau):
                brd_ids += b.lines._ids
            
            return brd_ids
            
        
    _columns={
        "parent":       fields.many2one("project.bordereau"),
        "sequence":     fields.integer('Sequence'),
        "name":         fields.char("No. Prix"),
        "designation":  fields.char("Designation"),
        "uom":          fields.many2one("product.uom","Unite",widget="selection" ),
        "qte_min":      fields.float("Qte. min", default=0.0),
        "qte_max":      fields.float("Qte. max", default=0.0),
        "prix_net":     fields.function(prix_ca,string="Prix Net",type="float",store={'project.project': (get_bordereau,['coef' ,'retenus'],10),
                                                                                      'project.bordereau':(lambda s,c,u,i,x: s.browse(c,u,i).lines._ids, ['coef'],10) }),
        "prix":         fields.float("Prix de base",default=0.0),
        }
    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, project.name + (project.designation and (' | ' +project.designation ) or '')   ))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('designation', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id)) 
    
class project_bordereau(osv.osv):
    _name="project.bordereau"
    def mtt_min(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        print "############### %s" % ids
        for obj in self.browse(cr,uid,ids,context=context):
        
            cr.execute("""
                select sum(qte_min * prix_net) as mtt 
                from project_bordereau_line 
                where parent = %s
              
            """ % (obj.id,))
            c =   cr.dictfetchone() or False
            if c:
                res[obj.id] = c['mtt']
        
        return res
        
    def mtt_max(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for obj in self.browse(cr,uid,ids,context=context):
            cr.execute("""
                select sum(qte_max * prix_net) as mtt 
                from project_bordereau_line 
                where parent = %s
              
            """ % (obj.id,))
            c =   cr.dictfetchone() or False
            if c:
                res[obj.id] = c['mtt']
        
        return res
    
    def _get_bord_id(self,cr,uid,ids,context=None):
        if not isinstance(ids, (int, long)):
            [ids] = ids
        return [s.parent.id for s in self.browse(cr, uid, ids, context=context)]
      
        
    _columns={
        "lines":    fields.one2many("project.bordereau.line","parent","lignes",copy=True),
        "name":     fields.char("Ref."),
        "projet":   fields.many2one("project.project","Projet"),
        "lot":      fields.many2one("project.project","Lot"), 
        "date":     fields.date("Date."),
        "mtt_min": fields.function(mtt_min, string="Mtt. min" ,type="float", store={'project.bordereau.line': (_get_bord_id,['qte_max' ,'qte_min','prix_net'],10)}),
        "mtt_max": fields.function(mtt_max, string="Mtt. max", type="float", store={'project.bordereau.line': (_get_bord_id,['qte_max' ,'qte_min','prix_net'],10)}),
        }
        
    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, project.name or "ID(%s) du %s" % (project.id, (project.date or '--/--/--') )  ))
        return result        

class project_attachement_line(osv.osv):
    _name="project.attachement.line"
    
    def total_amount(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = (o.qte * o.prix) or 0.0
        
        return res
        
    def unit_price(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = (o.name and o.name.prix_net )  or 0.0
        
        return res

    def uom(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = ( o.name and o.name.uom )  or False
        
        return res                
        
    _columns={
        "parent":       fields.many2one("project.attachement"),
        "sequence":     fields.integer('Sequence'),
        "name":         fields.many2one("project.bordereau.line","No. Prix"),

        "qte":          fields.float("Qte",digits_compute= dp.get_precision('Invoice calcul')),
        "prix":         fields.function(unit_price,string="Prix",type="float"),
        "ods":          fields.many2one("project.ods","ordre de service",required=False),
        "total_amount": fields.function(total_amount, string='Montant Tt', type="float", store=True),        
        }

class project_attachement(osv.osv):
    _name="project.attachement"
    
    def update_lines(self, cr,uid,ids,context=None):
        for o in self.browse(cr,uid,ids):
            rpt = False
            if o.rapport_ids:
                cr.execute("""
                    select %s as parent, rl.name, sum(rl.qte) as qte 
                    from project_rapport_prod rl, project_rapport r
                    
                    where rl.parent in %s
                        and r.id = rl.parent
                        
                    group by  rl.name
                """ % (o.id,tuple(x['id'] for x in o.rapport_ids)+tuple(x['id'] for x in o.rapport_ids),))
                rpt = cr.dictfetchall() or False
                print "#################### %s  #########################" % rpt
                if rpt:
                    o.lines =  [(0,0,x) for x in rpt] 
                
                o.rapport_ids = [(1,y['id'],{'state':'a'}) for y in o.rapport_ids]
        return True
    
    def total_amount(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            x = 0.0 
            for l in o.lines:
                x = x + (l.total_amount or 0.0)
            
            res[o.id] = x
        
        return res
    
    def create_invoice(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        o = self.browse(cr,uid,ids)
        
        values = {
            'partner_id' : o.projet.partner_id.id,
            'account_id' : o.projet.partner_id.property_account_receivable.id,
            'attachement_ids' : [(4,o.id)],
            'project' : o.projet.id,
        }
        
        invoice_id = self.pool['account.invoice'].create(cr,uid,values)
        
        o.write({'facture': (invoice_id and invoice_id) or False, 'state':(invoice_id and 'f') or o.state})
        
        data_pool = self.pool.get('ir.model.data')
        action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree1')
        
        if action_id:
            action_pool = self.pool['ir.actions.act_window']
            action = action_pool.read(cr, uid, action_id, context=context)
            #action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
            action['domain'] =  "[('id','=',"+str(invoice_id) +")]"
            action['context'] = "{}"
            return action
        return True
        for o in self.browse(cr,uid,ids,context):
            vals = {'partner_id' : o.projet.partner_id.id }
    
    def onchange_ods(self, cr, uid, ids, ods, context=None):
        p = self.pool.get('project.ods').browse(cr, uid, ods, context=context)
        return {'value': {
            'code_projet': p.code and p.code or False  ,
        }}        

    def onchange_project(self, cr, uid, ids, project, context=None):
        p = self.pool.get('project.project').browse(cr, uid, project, context=context)
        o = self.browse(cr,uid,ids)
        
       

        
        for r in o.rapport_ids:
            r.state = 'c'
        
        
            
            
        return {
      
            'value': {
                'ods':  False  ,
                'lines' : o.lines and [(2,o.lines)] or False ,
                'state':'n',
                'code_projet':False,
                'rapport_ids' : [(5)],
                'facture' : False,
                'state' : 'n'    
            }}            


            
    _columns={
        "lines":    fields.one2many("project.attachement.line","parent","lignes",copy=True),
        "name":     fields.char("Ref."),
        "projet":   fields.many2one("project.project","Projet"),
        "lot":      fields.many2one("project.project","Lot"),
        "date":     fields.date("Date"),
        "ods":      fields.many2one("project.ods","ordre de Travail"),
        "rapport_ids" : fields.one2many("project.rapport", 'attachement', 'Rapport liee'),
        "state":        fields.selection(string="Etat",selection=(('n','New'),('m','Metrage'),('c','confirme'),('f','facture')),default="n"),
        "total_amount": fields.function(total_amount, string ='Montant Tt', type="float"),
        "facture":      fields.many2one('account.invoice' , string="Facture"),
        "code_projet" : fields.char('code projet'),
        'partner_id'    : fields.related('projet','partner_id',string="Client" , type="many2one",relation="res.partner"),
        'metier'        : fields.related('projet','metier',string=u"Métier"    , type="many2one",relation="project.metier"),
        
        }

class project_situation_line(osv.osv):
    _name="project.situation.line"
    _columns={
        "parent":       fields.many2one("project.situation"),
        "name":         fields.many2one("account.analytic.account","Attachements"),
        #"ancien_solde": fields.float("Ancien solde"),
        "solde_actuel": fields.float("Nouveau solde"),
        "prix":         fields.float("Prix"),
        }
class project_decompte(osv.osv):
    _name="project.decompte"
    _columns={
        "situation":fields.many2one("project.situation"),
        "name":     fields.many2one("project.attachement.line","Attachements"),
        "uom":      fields.many2one("product.uom","Unite",widget="selection" ),
        "qte_min":  fields.float("Qte min marche"),
        "qte_max":  fields.float("Qte min marche"),
        "prix":     fields.float("Prix"),
        "qte":      fields.float("Qte. realisee"),
    
        }
class project_situation(osv.osv):
    _name="project.situation"

    def get_situation(self,cr,uid,id,date=d.now(),context=None):
        
        
        res = {'production': 0.0,
              'attachement': 0.0,
              'facturation': 0.0,
              'paiement':    0.0, 
              'charge_rh':   0.0,
              'matiere':     0.0,
              'materiel':    0.0,
              'service':     0.0,
              'soutraitance':0.0,  
              'parc':0.0, 
              'cout_indirecte':0.0 
               }
        oids  =  self.search(cr,uid,[('date','<=',date),('projet','=',id)])
        p =  self.browse(cr,uid,oids).sorted(key=lambda x:x.date,reverse=True)
        if p:
            o = p[0]
                   
            res ={'production':  o.production,
                  'attachement': o.attachement,
                  'facturation': o.facturation,
                  'paiement':    o.paiement, 
                  'charge_rh':   o.charge_rh,
                  'matiere':     o.matiere,
                  'materiel':    o.materiel,
                  'service':     o.service,
                  'soutraitance':o.soutraitance, 
                  'parc':       o.parc, 
                  'cout_indirecte':o.cout_indirecte,
                   }
        
        return res 
    
    _columns={
        "lines":        fields.one2many("project.situation.line","parent","lignes"),
        "name":         fields.char("Ref."),
        "date":         fields.date("Date",required=True),
        "projet":       fields.many2one("project.project","Projet"),
        "lot":          fields.many2one("project.project","Lot"),
        "production":   fields.float("Production",  required=True, default=0.0),
        "attachement":  fields.float("Attachement", required=True, default=0.0),
        "facturation":  fields.float("Facturation", required=True, default=0.0),
        "paiement":     fields.float("Paiement",    required=True, default=0.0),
        "charge_rh":    fields.float("Ressources humaines", required=True, default=0.0),
        "matiere":      fields.float("Matières Premières",  required=True, default=0.0),
        "materiel":     fields.float("Achat Matériels",     required=True, default=0.0),
        "service":      fields.float("Services",        required=True, default=0.0),
        "soutraitance": fields.float("Soutraitance",    required=True, default=0.0),
        "parc":         fields.float("Parc-engins",     required=True, default=0.0),
        "cout_indirecte":fields.float("Coûts indirectes",required=True, default=0.0),
        
        #"decomptes":fields.one2many("project.decompte","situation","Decomptes"),
        }

class project_approvisionnement_line(osv.osv):
    _name="project.approvisionnement.line"
    _columns={
        "parent":       fields.many2one("project.approvisionnement"),
        "name":         fields.many2one("product.template","Article"),
        "designation":  fields.char("Designation"),
        "uom":          fields.many2one("product.uom","Unite",widget="selection" ),
        "qte":          fields.float("Qte. min"),
        "prix":         fields.float("Prix"),
        }

class project_approvisionnement(osv.osv):
    _name="project.approvisionnement"
    _columns={
        "lines":    fields.one2many("project.approvisionnement.line","parent","lignes"),
        "name":     fields.char("Ref."),
        "projet":   fields.many2one("project.project","Projet"),
        "lot":      fields.many2one("project.project","Lot"),
        "date":     fields.float("date"),
        }
class project_project(osv.osv):
    _inherit="project.project" 
    def _stock_val(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            
            res[inv.id] = sum([(x.qte)*(x.prix) for x in  inv.stock_move]) or 0.0
        return res
    def _get_stock_move_id(self,cr,uid,ids,context=None):
#        if not isinstance(ids, (int, long)):
#            [ids] = ids
        return [s.analytic_account_id.id for s in self.browse(cr, uid, ids, context=context)]
               
    
    _columns={
        "ref": fields.char("Reference", required="True"),
        "bordereau":        fields.one2many("project.bordereau"  ,"projet" , "Bordereaux"),
        "bordereau_lot":    fields.one2many("project.bordereau"  ,"lot"    , "Bordereaux ods"),
        "attachement":      fields.one2many("project.attachement","projet" , "Attachements"),
        "rapport":          fields.one2many("project.rapport","project" , "Rapports journaliers"),
        "attachement_lot":  fields.one2many("project.attachement","lot"    , "Attachements"),
        "situation":        fields.one2many("project.situation","projet" , "Situations"),
        "situation_lot":    fields.one2many("project.situation","lot"    , "Situations"),
        "approvisionnement":        fields.one2many("project.approvisionnement","projet" , "Approvisionnements"),
        "approvisionnement_lot":    fields.one2many("project.approvisionnement","lot"    , "Approvisionnements"),
        "appel_offre":      fields.char("N. Appel d'offre"),
        "caution":          fields.one2many("project.caution","project","Cautions"),
        # "caution_def":    fields.one2many("project.caution","project","Caution definitive"),
        "date_ouv_plis":    fields.date("Ouverture des plis"),
        "mtt_offre":        fields.float("Offre financiere"),
        "delai":            fields.date("Délai d'execution des travaux"),
        "date_notif":       fields.date("date de notification"),
        "ods":              fields.one2many("project.ods","project","ordre de service"),
        "date_ods":         fields.date("Date ODS"),
        "date_start":       fields.date("Date début"),
        "date_stop":        fields.date("Date fin"),
        "marche" :          fields.many2one("project.marche",_("Marche")),
        "start_stop":       fields.one2many('project.start_stop','project','Ordres M/A.'),
        "duree":            fields.integer('Durée'),
        "stock_move":       fields.one2many('stock.pack.operation','analytic_account_id','Mouvement de Stock'),
        "stock_val":        fields.function(_stock_val, string="Valeur Conso. Stock", type='float' , store={'stock.pack.operation':(_get_stock_move_id,['qte','prix'],10),})
        
        
        }
    _sql_constraints = [('project_ref_unique', 'unique( ref )', 'Ref must be unique.'),('project_name_unique', 'unique( name )', 'name must be unique.')]
    
    def name_get(self, cr, uid, ids, context=None):
        result = []
        if not context:
            context={}
        rec_name = ''
        if 'rec_name' in context:
            rec_name = context.get('rec_name',False)
        
        if rec_name and rec_name in self._columns:
            for project in self.browse(cr, 1, ids, context):
                result.append((project.id, project[rec_name] ))
            return result
            
        
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, (project.ref and (project.ref + ' - ') or '') + project.name + (project.partner_id and ( '('+project.partner_id.name+')' ) or '')  ))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, ['|',('partner_id', 'ilike', name),('ref', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))
        
class project_caution(osv.osv):
    _name = "project.caution"
    
    def _amount_in_words(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = {
                'amount_words': '0.0',
                            }
            res[inv.id] = amount_to_text_fr(inv.montant or 0, 'DHS')
        return res
    
    _columns = {
        "name" :         fields.char("Reference"),
        "date":         fields.date("DATE DE DELIVRANCE"),
        "nature":       fields.selection(string="NATURE",selection=[(21,"PROVISOIRE"),
                                                            (22,"DEFINITIVE"),
                                                            (24,"RETENUE DE GARANTIE"),
                                                            (23,"RESTITUTION ACOMPTE"),
                                                            (11,"CREDIT ENLEVEMENT"),
                                                            (12,"O.C.C."),
                                                            (41,"LETTRE DE GARANTIE"),
                                                            (51,"DIVERSE")]),
        "echeance":     fields.date("ECHEANCE"),
        "montant":      fields.float("MONTANT"),
        "beneficiaire": fields.many2one("res.partner","BENEFICIAIRE"),
        "project":      fields.many2one("project.project","PROJET"),
        "marche":      fields.many2one("project.marche","Marche"),        
        "date_mainlevee":fields.date("DATE DE MAINLE    VEE"),
        "state": fields.selection(string=_("State"), selection=[('r',_("request")),('v',_("Valide")),('c',_("Cancelled")),('t',_("Terminee"))]),
        'amount_words': fields.function(_amount_in_words, string='In Words', type="char", help="The amount in words"),
        

    }

class project_rapport(osv.osv):
    _name="project.rapport"
    
    def create_Attachement(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        for o in self.browse(cr,uid,ids):
            if o.state != 'a':
            
            
                ao = self.pool['project.attachement']
                a = ao.search(cr,uid,[('projet','=',o.project.id ), ('state','=','n')])
                if a :
                    ar = ao.browse(cr,uid,a)
                    w = ar.write({'rapport_ids' : [(4,x) for x in ids]})
                    o.write({ 'state':(w and 'a') or o.state})
                    
                else : 
                    values = {
                        'rapport_ids' : [(4,x) for x in ids],
                        'projet' : o.project.id 
                    }
                    
                    invoice_id = self.pool['project.attachement'].create(cr,uid,values)
            
                    o.write({ 'state':(invoice_id and 'a') or o.state})
        
        data_pool = self.pool.get('ir.model.data')
        action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree1')
        
        if action_id:
            action_pool = self.pool['ir.actions.act_window']
            action = action_pool.read(cr, uid, action_id, context=context)
            #action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
            #action['domain'] =  "[('id','=',"+str(invoice_id) +")]"
            action['context'] = "{}"
            return action
        return True
    
    def total_amount(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            x = 0.0 
            for l in o.prod:
                x = x + (l.total_amount or 0.0)
            
            res[o.id] = x
        
        return res 
    def _get_prod_id(self, cr,uid,ids,context=None):
        if not isinstance(ids, (int, long)):
            [ids] = ids
        return [s.parent.id for s in self.browse(cr, uid, ids, context=context)]
               
    _columns={
        "name": fields.char("ref", required=True, default="New"),
        "state":    fields.selection(string="Etat",selection=(('n','New'),('c','Confirme'),('a','Attache'),('t','termine')),default="n"),
        "project": fields.many2one("project.project","PROJET"),
        "lot":     fields.many2one("project.ods","Ordre de Travail"),
        "date":    fields.date("date"),
        "prod":    fields.one2many("project.rapport.prod","parent","Production",copy=True),
        "parc":    fields.one2many("project.rapport.parc","parent","Engin - vehicule",copy=True),
        "hr":      fields.one2many("project.rapport.hr","parent","Personnel",copy=True),
        "address" : fields.many2one("project.address","Address"),
        "ods" : fields.many2one("project.ods","Ordres de service"),
        "attachement" : fields.many2one("project.attachement", "Ref. Attachement"),
        "total_amount": fields.function(total_amount, string='Montant Tt', type="float", 
                                    store={
                                        'project.rapport.prod': (_get_prod_id,['total_amount','qte'], 10),
                                        'project.rapport.parc': (_get_prod_id,['total_amount'], 10),
                                        'project.rapport.hr': (_get_prod_id,['total_amount'], 10),
                                    }),        
        'partner_id'    : fields.related('project','partner_id',string="Client" , type="many2one",relation="res.partner"),
        'metier'        : fields.related('project','metier',string=u"Métier"    , type="many2one",relation="project.metier"),
    }
class project_address(osv.osv):
    _name="project.address"
    _columns={
        "name": fields.char("Quartier"),
        "street":   fields.char("ligne 1"),
        "street2":    fields.char("ligne 2"),
        "ville": fields.char("Ville"),
        

        }
    
class project_rapport_prod(osv.osv):
    _name="project.rapport.prod"
    
    def total_amount(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = ((o.qte or 0.0) * (o.name.prix_net or 0.0) ) or 0.0
        
        return res
    _columns={
        "parent":   fields.many2one("project.rapport"),
        "sequence":     fields.integer('Sequence'),
        "name":     fields.many2one("project.bordereau.line","Code"),
        "uom":      fields.related('name','uom',relation="product.uom",string="Unite",widget="selection", type="many2one" ), 
        "qte":      fields.float("Qte. realisee"),
        "total_amount":       fields.function(total_amount, string='Montant Tt', type="float", store=True),        
        }
        
class project_rapport_parc(osv.osv):
    _name="project.rapport.parc"
    _columns={
        "project":   fields.related('parent','project',readonly=True,type="many2one",   relation="project.project", string=_("Projet"),store=True), 
        "odt":       fields.related('parent','ods',readonly=True,type="many2one",       relation="project.ods",     string=_("No Travail"),store=True), 
        "address":   fields.related('parent','address',readonly=True,type="many2one",   relation="project.address", string=_("Addresse"),store=True), 
        "date":      fields.related('parent','date',readonly=True,type="date",          string=_("Date"),           store=True), 
        "parent":    fields.many2one("project.rapport"),
        "name":      fields.many2one("fleet.vehicle",string="Engin - vehicule"),
        "qte":       fields.float("Qte. en heure"),
        }


                
class project_rapport_hr(osv.osv):
    _name="project.rapport.hr"
    _columns={
        "parent":   fields.many2one("project.rapport"),
        "name":     fields.many2one("hr.employee",string="Employe"),
        "qte":      fields.float("Qte. en heure"),
        }


class project_ods(osv.osv):
    _name="project.ods"
    
 
    
    
 
        
             
    _columns={
        
        "name":         fields.char("Ordre de service", default="New"),
        "designation":  fields.char("Designation"),
        "ref":          fields.char("Reference"),
        "project":      fields.many2one('project.project','Projet'),
        "lot" : fields.many2one('project.lot', 'lot', ondelete="restrict"),
        "code" : fields.char('code projet'),
        "address" : fields.many2one("project.address","Address"),
        "no_odt" : fields.integer("No Odt"),
        "rapport_prod" : fields.one2many('project.rapport', 'lot','Rapport de production' ),
        "rapport_rh" : fields.one2many('project.rapport.attendance', 'ods','Rapport MO' ),
        "attachement" : fields.one2many('project.attachement', 'ods','Attachements' ),
        "delai"         :fields.integer("Délai"),
        "state":    fields.selection(string="Etat", selection=[('n','Nouveau'),('v','Validé'),('e','En cours'),('t','Terminé'),('a','Annulé')])                

        }


    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, project.name + (project.designation and (' | ' +project.designation ) or '')   ))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('designation', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))         
    def create(self, cr, uid, vals, context=None):

        p = self.pool.get('project.project').browse(cr,uid,vals['project'])
        odt = 0
        for i in p.ods:
            odt = i.no_odt and i.no_odt or 1
        
        vals['no_odt'] = odt and odt + 1 or 1
        
        no_odt = ('0000' + str(vals['no_odt']))
        no_odt = no_odt[-5:]
        
        vals['name'] = p.ref and (p.ref +'/'+ no_odt) or no_odt
        
        return super(project_ods,self).create( cr, uid, vals, context=None)
        
        
class project_project_ods(osv.osv):

    _inherit="project.project"
    
    def mtt_min(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for obj in self.browse(cr,uid,ids,context=context):
            cr.execute("""
                select sum(bl.qte_min * bl.prix_net) as mtt 
                from project_bordereau_line bl,project_bordereau b, project_project p
                where p.id = %s
                    and p.id = b.projet
                    and b.id = bl.parent
              
            """ % (obj.id,))
            c =   cr.dictfetchone() or False
            if c:
                res[obj.id] = c['mtt']
        
        return res    
    def mtt_max(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
       
        for obj in self.browse(cr,uid,ids,context=context):
            cr.execute("""
                select sum(qte_max * bl.prix_net) as mtt 
                from project_bordereau_line bl,project_bordereau b, project_project p
                where p.id = %s
                    and p.id = b.projet
                    and b.id = bl.parent
              
            """ % (obj.id,))
            c =   cr.dictfetchone() or False
            if c:
                res[obj.id] = c['mtt']
        
        return res
        
    def _get_project_id(self, cr,uid,ids,context=None):
        if not isinstance(ids, (int, long)):
            [ids] = ids
        return [s.projet.id for s in self.browse(cr, uid, ids, context=context)]   
           
    _columns={        
        "ods":          fields.one2many('project.ods','project',string="Ordre de service"),
        "metier" :      fields.many2one('project.metier','Metier')        ,
        "lot" :         fields.one2many('project.lot','project','Lot')  ,
        "sous_projet" : fields.one2many('project.project','project_parent_id', 'Sous-projets')  , 
        "project_parent_id"    : fields.many2one("project.project", 'Projet parent'), 
        "mtt_min" :     fields.function(mtt_min, string="Mtt. min", type="float", store={'project.bordereau':(_get_project_id,['mtt_min','mtt_min'],10)})            ,  
        "mtt_max" :     fields.function(mtt_max, string="Mtt. max", type="float", store={'project.bordereau':(_get_project_id,['mtt_min','mtt_min'],10)}),
        "coef":         fields.float('coef. multiplicateur'),                              
        "delai"         :fields.integer("Délai"),
        }
        
class project_metier(osv.osv):
    _name="project.metier"
    _columns={        
        "name":         fields.char('Metier'),
        "lot"  : fields.one2many('project.lot','metier','Lots')      
        }    
            
class project_lot(osv.osv):
    _name="project.lot"
    _columns={        
        "name":         fields.char('Lot'),  
        "metier" : fields.many2one('project.metier','Metier') ,
        "project": fields.many2one('project.project', 'Projet'),
        "active":   fields.boolean('actif', default=True),   
        }      
        
class project_marche(osv.osv):
    _name="project.marche"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _columns={      
        "state" :           fields.selection(string="State",selection=[('e',u"En cours d'étude"),('j','En cours de jugement'),('a',u'Adjugé'),('p',u'Non Adjugé'),('t',u'terminé'),('c',u'annulé')], track_visibility='onchange'),      
        "name":             fields.char(u"Numéro d'appel d'offre"),  
        "objet" :           fields.char('Objet') ,
        "detail":           fields.text('Detail'),
        "project":          fields.one2many('project.project','marche', 'Projet') ,
        "address" :         fields.text(_('Addresse')), 
        "client" :          fields.many2one('res.partner', u"Maître d'ouvrage"),
        "type_contrat" :    fields.selection(string='Type de contrat', selection=[('marche',_('Marche')),('prive',_('Prive'))]),
        "type_prestation":  fields.selection(string='Type de prestation',selection=[('travaux',_('Travaux')),('fourniture',_('Fourniture')),('Service',_('Services')),]),
        "forme_marche":     fields.selection(string=_('Forme de marche'), selection=[('ordinaire',_('Ordinaire')),('commande',_('Bon de commande'))]),
        "montant":          fields.float(u"Estimation du MO en DH TTC"),
        "date_soumission" : fields.date(_('Date de soumission')),
        "date_ouverture_plis" : fields.datetime(_('Date de ouverture de plis')),
        "caution":          fields.one2many("project.caution","marche","Cautions"),
        "cause" :           fields.one2many("project.marche.reject","marche","Cause de rejet"),
        "concurrent" :      fields.one2many("project.marche.concurrent", "marche", "Concurrents"),
        "responsable" :     fields.many2one('res.users',string=_("Responsable"))
        
                }
    _track = {
        'state': {'mt_marche_creat': lambda self, cr, uid, obj, ctx=None: obj['state'] and obj['state'] ,},
            }

class project_marche_reject(osv.osv):
    _name="project.marche.reject"
    _columns={
        "marche" :  fields.many2one("project.marche",_("Marche")),
        "cause" :   fields.many2one("project.marche.reject.cause","Cause de rejet"),
        "motif" :   fields.many2many("project.marche.reject.motif","marche_reject_motif","reject_id","motif_id","motif de rejet"),        
        "remarque": fields.text("Remarque")

    }
class project_marche_reject_cause(osv.osv):
    _name="project.marche.reject.cause"
    _columns={
        "name" : fields.char("Cause"),


    }      
class project_marche_reject_motif(osv.osv):
    _name="project.marche.reject.motif"
    _columns={
        "name" : fields.char("Motif"),
        "cause_id" : fields.many2one("project.marche.reject.cause", "Cause") 

    }    
class project_marche_concurrent(osv.osv):
    _name="project.marche.concurrent"
    _columns={
        "marche" :       fields.many2one("project.marche",_("Marche")),
        "concurrent" :   fields.many2one("res.concurrent","Concurrent"),
        "adjudicataire": fields.boolean("Adjudicataire"),       
        "remarque":      fields.text("Remarque"),

    }    

class res_concurrent(osv.osv):
    
    #_inherit="res.partner"
    _name="res.concurrent"
    _columns={
        'active' : fields.boolean('Active', default=True),
    }
    
        
class project_start_stop(osv.osv):
    _name="project.start_stop"
    
    def _ss_type(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        ss = self.pool['project.start_stop']

        for o in self.browse(cr,uid,ids,context=context):
            ss_ids = ss.search(cr,uid,[('project','=',o.project.id)])
            ss_id=[]
            ss_id.append(ss_ids and ss_ids[len(ss_ids)-2] or False)
            sso= ss.browse(cr,uid, ss_id)
            if sso:
                last =  sso[0].type == 'a' and  'm'  or 'a'
            
                current = (last == 'm') and 'a' or 'm'
            
            res[o.id] = last or 'a'
        
        return res
    _columns={        
        "project":  fields.many2one('project.project','Projet'),
        "type"  :    fields.function(_ss_type,store=True, type="selection", selection=[('m','Début de travaux'),('a','Arrêt de travaux')], string="Type d'ordre"),      
        "date":     fields.date('Date'),
        #"state":    fields.selection(string='Etat', selection=[(),()]),
        "reference": fields.char('Réference'),
        }       
