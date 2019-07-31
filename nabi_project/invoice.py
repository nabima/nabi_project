# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
import time
from project import amount_to_text_fr


class account_invoice_retenus(osv.osv):
    _name ="account.invoice.retenus"
    _order = 'sequence,id'
    _columns={
        
        'name':         fields.char('Description'),
        'invoice':      fields.many2one('account.invoice','Facture'),
        'account':      fields.many2one('account.account','Compte'),
        'ratio':        fields.float('ratio',       digits_compute= dp.get_precision('Invoice calcul') ,default=False),
        'mtt_base':     fields.float('Mtt. base',   digits_compute= dp.get_precision('Invoice calcul') ,default=False),
        'mtt_ht':       fields.float('Mtt. HT',     digits_compute= dp.get_precision('Invoice calcul') ,default=False),
        'mtt_taxe':     fields.float('Mtt. taxe',   digits_compute= dp.get_precision('Invoice calcul') ,default=False),
        'mtt_ttc':      fields.float('Mtt. TTC',    digits_compute= dp.get_precision('Invoice calcul'),default=False),
        'stt_ht':       fields.float('Sous Tt HT',  digits_compute= dp.get_precision('Invoice calcul'),default=False),
        'type':         fields.selection(string="Type", selection=[('g','Retenu de garantie'),('d','Décompte')]),
        'base':         fields.selection(string="Base de calcul", selection=[('p','Précedant'),('ht','Total HT')], default=False),
        'sequence':     fields.integer('sequence',default=99),
        'param_line':   fields.many2one('project.retenus','Ligne de paramètrage'), 
        
    }
class project_retenus(osv.osv):
    _name ="project.retenus"
    _columns={
        'project':  fields.many2one('project.project','Projet'),
        'name':     fields.char('Description'),
        'account':  fields.many2one('account.account','Compte'),
        'ratio':    fields.float('ratio', digits_compute= dp.get_precision('Invoice calcul')), 
        'type':     fields.selection(string="Type", selection=[('g','Retenu de garantie')]),
        'base':     fields.selection(string="Base de calcul", selection=[('p','Précedant'),('ht','Total HT')], default="ht"),
        
    }
class project_project(osv.osv):
    _inherit="project.project"
    _columns = {
        'retenus':  fields.one2many('project.retenus','project','Retenus'),

        
    }    
    
class account_invoice(osv.osv):
    _inherit = "account.invoice" 
    
    def _amount_in_words(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = {
                'amount_words': '0.0',
                            }
            montant = sum( [(x.mtt_ttc or 0.0) for x in inv.retenus])
            res[inv.id] = amount_to_text_fr(montant or 0, 'DHS')
        print "####################### %s" % res 
        return res
    
    _columns = {
        "attachement_ids":      fields.one2many("project.attachement",'facture', string="Facture"),
        "attachement_line":     fields.one2many("invoice.attachement.line",'facture', string="Lignes d'attachements"),
        "retenus":              fields.one2many('account.invoice.retenus','invoice','Retenus'),
        'odt_client':           fields.char("No. d'ordre"),
        'code_projet_client':   fields.char('Code de projet client'),
        'quantity':             fields.float(string='Quantity', digits_compute= dp.get_precision('Invoice Product Unit of Measure'), required=True, default=1),
        "objet":                fields.char("Objet du projet"),
        "marche":               fields.char("Marché cadre"),
        "nb_attachement":       fields.integer("Nombre d'attachements"),
        "commande":             fields.char("No. commande"),
        "desc_projet":          fields.char("Détail du projet"),
        "adresse":             fields.char("Adresse"),
        'amount_words':         fields.function(_amount_in_words, string='In Words', type="char", help="The amount in words"),
        }

        
    def clear_lines(self, cr, uid, ids, context=None):

        o = self.browse(cr,uid,ids)
        i = []
        for l in o.invoice_line :
            if (l.quantity == 0.0 or l.quantity == False) and  (l.qte_cumul == 0.0 or l.qte_cumul == False):
                i.append((2,l.id))
        
        if i:
            o.invoice_line = i
        
        return True
    
    def calc_retenus(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        vals=[]
        o = self.browse(cr,uid,ids)
        for ro in o.retenus:
            o.retenus = [(2,ro.id)]
        
        decompte =  sum([(x.mtt_cumul or 0.0) for x in o.invoice_line]) or 0.0
        mtt_ht = o.amount_untaxed + decompte or 0.0
        
        stt_ht = mtt_ht or 0.0
        vals.append((0,0, { 

                'name':     _("Travaux realises HT") ,
                
                'mtt_ht':      mtt_ht or False,
                'mtt_taxe': (mtt_ht *  0.2) or False,
                'mtt_ttc':  (mtt_ht * 1.2) or False,
                'stt_ht': stt_ht ,
                'sequence' : 1,
                        
                    
                    }) )
        if o.project.coef != 0.0 and o.project.coef and not o.project.inv_line_price_net:
            coef = ( o.project.coef - 1) * 100
            mtt_ht = stt_ht 
            stt_ht = stt_ht + ((stt_ht * coef)/100 or 0.0)
            vals.append((0,0, { 

                'name':     _("coef. operationnel"),
               
                'ratio'     :o.project.coef,
                'mtt_base'  :mtt_ht,
                'mtt_ht'    :(mtt_ht * coef)/100 or False,
                'mtt_taxe'  :(mtt_ht * coef * 0.2)/100 or False,
                'mtt_ttc'   :( mtt_ht * coef * 1.2) /100 or False,
                'stt_ht'    :stt_ht,
                'sequence' : 2,
                        
                    
                    }) )
        
        
        if decompte != 0.0:
            
            mtt_ht =  - decompte or False
            mtt_taxe = (mtt_ht * 0.2) or False
            mtt_ttc = (mtt_ht * 1.2) or 0.0
            stt_ht = stt_ht + ( mtt_ht or 0.0)
            vals.append((0,0, { 

                'name':     'Décompte(s)',
                #'account':  r.account,
                #'ratio':    r.ratio,
                #'mtt_base':   mtt_base,
                'mtt_ht':     mtt_ht,
                'mtt_taxe':   mtt_taxe,
                'mtt_ttc':    mtt_ttc,
                'stt_ht' :    stt_ht,
                'type':     'd',
                #'base':     r.base,
                'sequence' : 3,
                    }) ) 
            
        
        
        
        
        for r in o.project.retenus:
            if r.base == 'p':
                mtt_base = stt_ht or 0.0
            else:
                mtt_base = o.amount_untaxed 
                
            mtt_ht =  (mtt_base * r.ratio)/100 or False
            mtt_taxe = (mtt_base * r.ratio * 0.2)/100 or False
            mtt_ttc = (mtt_base * r.ratio * 1.2) /100
            stt_ht = stt_ht + ( mtt_ht or 0.0)
            vals.append((0,0, { 

                'name':     r.name,
                'account':  r.account,
                'ratio':    r.ratio,
                'mtt_base':   mtt_base,
                'mtt_ht':     mtt_ht,
                'mtt_taxe':   mtt_taxe,
                'mtt_ttc':    mtt_ttc,
                'stt_ht' :    stt_ht,
                'type':     r.type,
                'base':     r.base,
                        
                    
                    }) ) 
        if vals:
            o.retenus = vals
            o.amount_net_ht = sum([(x.mtt_ht or 0.0) for x in o.retenus]) or 0.0
            o.amount_net_taxe = sum([(x.mtt_taxe or 0.0) for x in o.retenus]) or 0.0
            o.amount_net_ttc = sum([(x.mtt_ttc or 0.0) for x in o.retenus]) or 0.0
        return True
    
    def recalc_retenus(self, cr, uid, ids, context=None):
        
        o = self.browse(cr,uid,ids)
        decompte =  sum([(x.mtt_cumul or 0.0) for x in o.invoice_line]) or 0.0
        total = o.amount_untaxed + decompte or 0.0
        stt_ht = 0.0
        
        for ro in o.retenus.sorted(key=lambda x: x.sequence):
            if ro.name == _("Travaux realises HT"):
                ro.mtt_base = total
                mtt_ht      = total 
                ro.mtt_ht   = total 
                ro.mtt_taxe = total * 0.2
                ro.mtt_ttc  = total * 1.2
                stt_ht      = stt_ht + mtt_ht
                ro.stt_ht   = stt_ht
                continue
                
                
            if ro.name == _("coef. operationnel"):
                ro.mtt_base = total
                coef = (ro.ratio or 1) - 1
                 
                mtt_ht      = total * coef 
                ro.mtt_ht   = mtt_ht 
                ro.mtt_taxe = mtt_ht * 0.2
                ro.mtt_ttc  = mtt_ht * 1.2
                stt_ht      = stt_ht + mtt_ht
                ro.stt_ht   = stt_ht
                continue
            
            if ro.type == 'd':
                stt_ht   = stt_ht + ro.mtt_ht 
                ro.stt_ht   = stt_ht
                
                
                continue
            elif ro.base == 'p':
                if ro.ratio and ro.ratio !=0.0:
                    ro.mtt_base = stt_ht
                    mtt_ht      = stt_ht * (ro.ratio or 0.0) / 100
                    ro.mtt_ht   = mtt_ht
                     
                else:
                    mtt_ht   = ro.mtt_ht
                    
                ro.mtt_taxe = mtt_ht * 0.2
                ro.mtt_ttc  = mtt_ht * 1.2
                stt_ht      = stt_ht + mtt_ht
                ro.stt_ht   = stt_ht 
                    
            
            
            else :
                if ro.ratio and ro.ratio !=0.0:
                   
                    ro.mtt_base = total
                    mtt_ht   = total * (ro.ratio or 0.0) / 100
                    ro.mtt_ht   = mtt_ht 
                else:
                    mtt_ht   = ro.mtt_ht
                ro.mtt_taxe = mtt_ht * 0.2
                ro.mtt_ttc  = mtt_ht * 1.2
                stt_ht   = stt_ht + mtt_ht
                ro.stt_ht   = stt_ht
        if o:                   
            o.amount_net_ht = sum([(x.mtt_ht or 0.0) for x in o.retenus]) or 0.0
            o.amount_net_taxe = sum([(x.mtt_taxe or 0.0) for x in o.retenus]) or 0.0
            o.amount_net_ttc = sum([(x.mtt_ttc or 0.0) for x in o.retenus]) or 0.0
        return True             
                        
        
        
        

class invoice_attachement_line(osv.osv):
    _name = "invoice.attachement.line"
    _auto = False
    _columns = {
        'id':   fields.integer('ID'),
        'facture':   fields.many2one('account.invoice', 'Facture'),    
        'name':   fields.many2one('project.bordereau.line', 'Ref. Prix'),    
        'attachement':   fields.many2one('project.attachement', 'Attachement'),    
        'qte':   fields.float('Qte Total',digits_compute= dp.get_precision('Invoice calcul')),               
        'prix':   fields.float('Mtt Total',digits_compute= dp.get_precision('Invoice calcul')),                   
    }
    
    def init(self, cr):
        
        cr.execute("""CREATE or REPLACE VIEW invoice_attachement_line as 
            select  row_number() over() as id,
                    i.id as facture,
                    al.name ,
                    sum(al.total_amount) as prix,
                    sum(al.qte) as qte,
                    a.name as attachement,
                    a.ods as ods                    
                      
            from    project_attachement a,
                    project_attachement_line al,
                    account_invoice i
            
            where   a.id = al.parent
                and a.facture = i.id
            group by i.id, al.name ,a.name, a.ods          
            """)
            

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def import_brd_lines(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        vals=[]
        prestation= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Prestation')
        rabais= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Rabais') or prestation
        decompte= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Decompte') or prestation
        rg= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.RG')             or prestation         
        co= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.RG')             or prestation                 
        
        # get attachement total : 
        
        o = self.browse(cr,uid,ids)

        for l in o.bordereau.lines : 

            vals.append((0,0, { 
                        'product_id'    : prestation.id,
                        'ref_prix'      : l.id,
                        'name'          : l.designation,
                        'quantity'      : 0,
                        'price_unit'    : l.prix_net ,
                        'price_unit_net': l.prix ,
                        'invoice_line_tax_id'   : prestation.taxes_id,
                        'account_id'            : prestation.property_account_income,
                        'account_analytic_id'   : o.project.analytic_account_id.id
                    }) )
        if vals : 
                o.invoice_line = vals
        return True
                
    def copy_lines(self, cr, uid, ids, context=None):
        if context is None: context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        vals=[]
        prestation= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Prestation')
        rabais= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Rabais') or prestation
        decompte= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.Decompte') or prestation
        rg= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.RG')             or prestation         
        co= self.pool.get('ir.model.data').xmlid_to_object(cr, 1, 'project.RG')             or prestation                 
        
        # get attachement total : 
        
        o = self.browse(cr,uid,ids)
        total = 0.0
        for a in o.attachement_ids:
            total = (a.total_amount  + total)           or 0.0
        
                 
        if vals : 
                o.invoice_line = vals
        
        # return True
        
        for o in self.browse(cr,uid,ids):
            for l in o.attachement_line : 

                vals.append((0,0, { 
                    'product_id': prestation.id,
                    'ref_prix' : l.name,
                    'name' : l.name.designation ,
                    'quantity' : l.qte,
                    'price_unit' : l.name.prix,
                    'invoice_line_tax_id' : prestation.taxes_id,
                    'account_id' : prestation.property_account_income,
                    'account_analytic_id' : l.name.parent.projet.analytic_account_id.id
                    
                
                }) )
            if vals : 
                o.invoice_line = vals
        
            

        return True


    _columns = {
        "attachement_ids":  fields.one2many("project.attachement",'facture', string="Facture"),
        "attachement_line": fields.one2many("invoice.attachement.line",'facture', string="Lignes d'attachements"),
        "project" : fields.many2one('project.project', 'Projet', required=True),
        "bordereau" : fields.many2one('project.bordereau','Bordereau de prix', required=True),
        "amount_net_ht":   fields.float("Montant net HT"),
        "amount_net_taxe": fields.float("Montant TVA net"),
        "amount_net_ttc":  fields.float("Montant net TTC"),
        }

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    def qte_cumul(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        ilo = self.pool.get('account.invoice.line')
       
        for o in self.browse(cr,uid,ids,context=context):
            l = o.invoice_id.code_projet_client and  ilo.search(cr,uid,[('ref_prix','=',o.ref_prix.id),('invoice_id','<',o.invoice_id.id),('invoice_id.project','=',o.invoice_id.project.id),('invoice_id.code_projet_client','=',o.invoice_id.code_projet_client)],limit=1, order="id desc") or []
            co =  ilo.browse(cr,uid,l)
            c= 0.0 
            if co:
                
                c= (co.quantity or 0.0) + (co.qte_cumul or 0.0)
                print "qte ############ %s - %s" % (ids, c)
            else:
                continue
            res[o.id] = c or False
            
        return res
    
    def qte_cumul_inv(self, cr, uid, ids, name, value, arg, context):  
        o = self.browse(cr,uid,ids)
        val =  value * (o.price_unit or price_unit_net) or False
        if val:
            print "qte_inv ############ %s - %s" % (ids,val)
            cr.execute("update account_invoice_line set qte_cumul=%s, mtt_cumul = %s where id =%s" % (value,val,ids))
        return True        

    def mtt_cumul(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        ilo = self.pool.get('account.invoice.line')
        
       
        for o in self.browse(cr,uid,ids,context=context):
            l = o.invoice_id.code_projet_client and ilo.search(cr,uid,[('ref_prix','=',o.ref_prix.id),('invoice_id','<',o.invoice_id.id),('invoice_id.project','=',o.invoice_id.project.id),('invoice_id.code_projet_client','=',o.invoice_id.code_projet_client)],limit=1,order="id desc") or []
            c = 0.0
            co = ilo.browse(cr,uid,l)
            if co :
            
                c = (co.mtt_cumul or 0.0) + (co.price_subtotal or 0.0)
                print "mtt ############ %s - %s" % (ids,c)
            else:
                continue
            
            res[o.id] = c or False
        
        return res
    
    def mtt_cumul_manuel(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        for o in self.browse(cr,uid,ids,context=context):
            res[o.id] = o.qte_cumul_manuel * o.price_unit or False
        
        return res
    
    def mtt_cumul_inv(self, cr, uid, ids, name, value, arg, context):
        o = self.browse(cr,uid,ids)
        val = o.price_unit and value /  o.price_unit or False
        if val:
            print "mtt_inv ############ %s - %s" % (ids,val)
            cr.execute("update account_invoice_line set mtt_cumul=%s, qte_cumul=%s where id=%s" % (value,val,ids))
        return True
        
            
    
    _columns = {
        'ref_prix':   fields.many2one('project.bordereau.line', 'Ref. Prix'),
        'attachement':   fields.many2one('project.bordereau.line', 'Ref. Prix'),
        'odt_client': fields.char('ordre de travail client'),
        'code_projet_client': fields.char('Code de projet client'),
        'qte_cumul': fields.function(qte_cumul,fnct_inv=qte_cumul_inv,string=_('Qte Cumul precedent'), type='float',digits_compute= dp.get_precision('Invoice calcul') ,store=True),
        'mtt_cumul': fields.function(mtt_cumul,fnct_inv=mtt_cumul_inv, string=_('Mtt Cumul precedent'), type='float' ,digits_compute= dp.get_precision('Invoice calcul'), store=True),
        
        "uom":   fields.related('ref_prix','uom',readonly=True,type="many2one",   relation="product.uom",string="Unit.",store=True), 
        #'qte_cumul_manuel': fields.float(string='Qte Cumul precedent', type='float'),
        #'mtt_cumul_manuel': fields.function(mtt_cumul_manuel, string='Mtt Cumul precedent', type='float' ,digits_compute= dp.get_precision('Invoice calcul'),store=True),        
        'price_unit_net':   fields.float('Prix rèf.'),        

        }
    def onchange_ref_prix(self, cr, uid, ids, ref_prix, context=None):
        p = self.pool.get('project.bordereau.line').browse(cr, uid, ref_prix, context=context)
        
        
        return {'value': {
            'price_unit': p.prix_net and p.prix_net or False  ,
            'price_unit_net': p.prix and p.prix or False  ,
            'name' : p.designation and p.designation or False
        }} 

    def onchange_odt_code(self, cr, uid, ids, invoice_id,odt_client, code_projet_client,context=None):
        
        
        return {'value':{'odt_client':odt_client and odt_client.upper() or False,
                         'code_projet_client' : code_projet_client and code_projet_client.upper() or False, 
                            
                        }
                }
                
class res_partner(osv.osv):
    _inherit ="project.project"
   
    _columns={
        
        'inv_line':             fields.boolean("Afficher lignes de facture", default=True),
        'inv_line_price_net':   fields.boolean("Valoriser au prix Net"),
        'inv_line_col_odt':     fields.boolean("Afficher les colonnes ODT et Projet"),
        'inv_line_col_cumul':   fields.boolean("Afficher Les colonnes cumul"),
        'unit_price_title':     fields.char("Entête de la colonne prix unitaire"),
       
        
        
        }
        
        
        
        
        
        
                
