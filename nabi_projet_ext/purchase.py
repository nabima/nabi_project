# -*- encoding: utf-8 -*-


from xml.sax.saxutils import escape
import time
from openerp import fields as Fields,models
from openerp.osv import fields,osv
from datetime import datetime
from lxml import etree
from openerp import tools
from openerp.tools.translate import _
from openerp.exceptions import  *
from openerp import api
from openerp.tools import *


class purchase_department(osv.osv):
    _name="purchase.department"
    
    name= Fields.Char("Name")

class nabi_res_activity(osv.osv):
    _name="nabi.res.activity"
    _columns = { 
        'name' : fields.char(u'Activité'),
    }


class purchase_reception(models.Model):
    _name = "purchase.reception"
    _description = u"Réception des article hors stock"    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _STATES = {}
    _STATESS = { 'draft'     :[('readonly',False)],
                'confirm'   :[('readonly',True)],
                'invoiced'  :[('readonly',True)],
                'cancel'    :[('readonly',True)]
                
                
    }
    
    state       = Fields.Selection([('draft','Brouillon'),('confirm',u'confirmé'),('invoiced',u'Facturé'),('cancel',u'Annulé')],string="state",index=True,default='draft',track_visibility='onchange')
    name        = Fields.Char("Nom",default="/",required=True,track_visibility='onchange',states=_STATES)
    partner_id  = Fields.Many2one("res.partner","Fournisseur",required=True,track_visibility='onchange',states=_STATES)
    date        = Fields.Date("Date",track_visibility='onchange',states=_STATES)
    
    order_id    = Fields.Many2one('purchase.order','Origin',track_visibility='onchange',states=_STATES)
    ligne       = Fields.One2many('purchase.reception.line','parent','Lignes',track_visibility='onchange',states=_STATES)
    invoice_state= Fields.Boolean(u"Facturé",track_visibility='onchange',states=_STATES)
    department_id = Fields.Many2one("purchase.department",u"Département",states=_STATES)

    @api.one
    def action_confirm(self):
        self.state = 'confirm'
    
    @api.one
    def action_cancel(self):
        self.state = 'cancel'
    
    @api.one
    def action_invoiced(self):
        self.state = 'invoiced'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('purchase.reception') or '/'
        return super(PurchaseOrder, self).create(vals)
    
class purchase_reception_line(models.Model):
    _name="purchase.reception.line"
    
    parent          = Fields.Many2one('purchase.reception','parent')
    name            = Fields.Char('Nom')
    qte             = Fields.Float(u"Quantité")
    invoice_state   = Fields.Boolean(u"Facturé")
    order_line_id   = Fields.Many2one("purchase.order.line","ligne de commande")

class wizard_purchase_request_receive(osv.osv_memory):
    _name="wizard.purchase.request.receive"
    
    line= Fields.One2many("wizard.purchase.request.receive.line","parent_id", "Lignes")
    
    
    def default_get(self,cr,uid,ids,context=None):
        res = super(wizard_purchase_request_receive,self).default_get(cr,uid,ids,context)
        o = self.pool.get('purchase.reception')
        order_id = o.browse(cr,uid,context.get('active_ids',[]),context=context).order_id
        vals = []
        for l in  order_id.order_line:
            pass
            vals += [(0,0,{
                'name':l.name,
                'qte_cde':  l.product_qty,
                'order_line_id':l.id,
                
            
            })]
        if vals :
        
            res['line'] = vals
        
        return  res
    
    def receptionner(self, cr ,uid,ids,context=None):
        parent = self.pool['purchase.reception'].browse(cr,uid,context.get('active_id',[]),context=context)
        for o in self.browse(cr,uid,ids):
            parent.ligne = [(0,0,{'name':x.name, 'qte': x.qte, 'order_line_id':x.order_line_id.id}) for x in o.line if x.qte ]
        
        
        
        return True
        


class wizard_purchase_request_receive_line(osv.osv_memory):
    _name="wizard.purchase.request.receive.line"
    
    parent_id       = Fields.Many2one("wizard.purchase.request.receive","Parent")
    name            = Fields.Char('Nom')
    qte_cde         = Fields.Float(u"Quantité cdé")
    qte_reste       = Fields.Float(u"Quantité Rest.")
    order_line_id   = Fields.Many2one("purchase.order.line","ligne de commande")
    qte             = Fields.Float(u"Quantité reçu")




class purchase_request(osv.osv):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = u"Demande d'achat"
    _name="purchase.request"
    _columns = {
    
        'name' :        fields.char('name', default='/'),
        'company_id':   fields.many2one('res.company', u'Société' ) ,
        'metier':     fields.many2one('nabi.res.activity', u'Activité'),
        'priority':     fields.selection([('1','Pas urgent'),('2','Normal'),('3','Urgent'),],string=u'Priorité',default='2'),
        'projet':      fields.many2one('project.project',u'Projet/compte'),
        'odt':  fields.many2one('project.ods', u'Sous projet/compte'),
        'state':        fields.selection([('d','Demande'),('e','Encours de traitement'),('s','Suspendue'),('t','Traitée'),('a','Annulée')],u='Etat',default=u"d",track_visibility='onchange'),
        'note':         fields.text('Note',track_visibility='onchange'),
        'line':         fields.one2many('purchase.request.line','parent','Lignes',track_visibility='onchange'),
        'analytic_account_id': fields.many2one("account.analytic.account",u"Compte analytique"),
        'partner_id':   fields.many2one('res.partner','Fournisseur')
    }
    
    department_id = Fields.Many2one("purchase.department",u"Département")
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        company_id  = vals.get('company_id', False)
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, 1, 'purchase.request.mg', context=context) or '/'
        new_id = super(purchase_request, self).create(cr, uid, vals, context=context)
        return new_id
    @api.multi
    def print_report(self):
        p_ids = [x.po.id for x in self.line if x.po]
        p = self.env['purchase.order'].sudo().browse(p_ids)
        if p_ids:
            
            xx = self.env['report'].sudo().get_action(p,'purchase.report_purchaseorder')
            return xx
        raise Warning(u"Pas de commande!",u"Aucune commande n'est encore traité")
    
    @api.onchange('project')
    def onchange_projet(self):
        self.analytic_account_id = self.projet and self.projet.analytic_account_id.id or False

class purchase_request_line(osv.osv):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name="purchase.request.line"
    _columns = {    
        'parent':   fields.many2one('purchase.request', 'parent'),
        'product_id': fields.many2one('product.product','Article'),
        'price':    fields.float('Prix'),
        'name' :    fields.char('name',track_visibility='onchange'),
        'uom':      fields.char(u'Unité',track_visibility='onchange'),
        'qte':      fields.float(u'Qté',track_visibility='onchange'),
        'destination':  fields.char('Destination',track_visibility='onchange'),
        'date':     fields.datetime('Date',track_visibility='onchange'),
        'po':  fields.many2one('purchase.order','Bon de commande'),
        'state':        fields.selection([('d','Demande'),('e','Encours de traitement'),('t','Traitée'),('a','Annulée')],string='Etat',default=u"d",track_visibility='onchange'),    
        'note':         fields.text('Note',track_visibility='onchange'),
    }
    
    @api.multi
    def print_report(self):
        datas = {
            'ids': [self.po.id],
            'model': 'purchase.order',
            }
        return {
            'type' : 'ir.actions.report.xml',
            'report_name' : 'purchase.report_purchaseorder',
            'datas' : datas,
        } 


class purchase_order(osv.osv):
    _inherit="purchase.order"

    department_id   = Fields.Many2one("purchase.department",u"Département")
    pr_name         = Fields.Char(u'Numéro de demande de prix', default="/",select=True, copy=False)
    name            = Fields.Char(default="-")
    is_marche       = Fields.Boolean("Commande liée à un contrat de soutraitance", default=False)
    marche          = Fields.Many2one("nabi.marche", u"Contrat de soutraitance")
    
    def _shipped_rate(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        for id in ids:
            res[id] = [0.0,0.0]
        
        cr.execute('''SELECT
                p.order_id, sum(m.product_qty), m.state
            FROM
                stock_move m
            LEFT JOIN
                purchase_order_line p on (p.id=m.purchase_line_id)
            WHERE
                p.order_id IN %s GROUP BY m.state, p.order_id''',(tuple(ids),))
        
        for oid,nbr,state in cr.fetchall():
            if state=='cancel':
                continue
            if state=='done':
                res[oid][0] += nbr or 0.0
                res[oid][1] += nbr or 0.0
            else:
                res[oid][1] += nbr or 0.0
        
        cr.execute("""
            select pl.order_id , sum(l.qte), r.state
            from
            purchase_reception_line l
            left join
                purchase_order_line  pl on (pl.id = l.order_line_id)
            inner join 
                purchase_reception r on (r.id = l.parent)
            
            where   pl.order_id in %s 
            Group by r.state , pl.order_id """ , (tuple(ids),))
        
        for oid,nbr,state in cr.fetchall():
            if state=='cancel':
                continue
            if state=='confirm':
                res[oid][0] += nbr or 0.0
                res[oid][1] += nbr or 0.0
            else:
                res[oid][1] += nbr or 0.0
        
        
        for r in res:
            if not res[r][1]:
                res[r] = 0.0
            else:
                res[r] = 100.0 * res[r][0] / res[r][1]
        return res
        
        
        
        

    _columns ={
        'shipped_rate': fields.function(_shipped_rate, string='Received Ratio', type='float'),
    
    }
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('pr_name','/')=='/':
            ctx = dict(context or {}, force_company=vals['company_id'])
            vals['pr_name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.devis', context=ctx) or '/'
            vals['name']    = vals['pr_name']
        ctx = dict(context or {}, mail_create_nolog=True,force_company=vals['company_id'])
        
        order =  super(purchase_order, self).create(cr, uid, vals, context=ctx)
        self.message_post(cr, uid, [order], body=_("RFQ created"), context=ctx)
        return order

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        o = self.browse(cr,uid,ids)
        ctx = dict(context or {},force_company=o.company_id.id)
        if o.name == o.pr_name or o.name == '-' :
            o.name = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order', context=ctx) or '-'
    
        res = super(purchase_order,self).wkf_confirm_order(cr, uid, ids, ctx)
        return res 


    


class stock_picking(osv.osv):
    _inherit="stock.picking"
    
    department_id = Fields.Many2one("purchase.department",u"Département")

class res_partner(osv.osv):
    _inherit="res.partner"
    
    ice = Fields.Char("ICE")


class res_partner_bank(osv.osv):
    _inherit="res.partner.bank"
    
    attachement = Fields.Binary(u"Pièces jointes")

    
