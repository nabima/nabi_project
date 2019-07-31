# -*- encoding: utf-8 -*-


from openerp import fields,models,api
from openerp.exceptions  import *
from openerp.osv import osv


class nabi_marche(models.Model):
    _name = "nabi.marche"
    _description = u"Marché"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    @api.one
    def _prc_attache(self):
        att_amount  = sum(self.attachement_ids.mapped('amount'))
        brd_amount  = sum(self.attachement_ids.mapped('amount'))
        
        
        try:
            self.prc_attache = att_amount / brd_amount
        except:
            self.prc_attache = 0
    
    name        = fields.Char(u"Réf.", default="/",copy=False,track_visibility='onchange')
    partner     = fields.Many2one("project.soutraitant",u"Soutraitant",track_visibility='onchange')
    date        = fields.Date("Date",track_visibility='onchange')
    objet       = fields.Char(u"Objet du marché",track_visibility='onchange')
    amount      = fields.Float(u"Montant du marché",track_visibility='onchange')
    coef        = fields.Float(u"Coéficient",track_visibility='onchange')
    delay       = fields.Float(u"Délai",track_visibility='onchange')
    date_start  = fields.Date(u"Date de début",track_visibility='onchange')
    date_end    = fields.Date(u"Date de fin",track_visibility='onchange')
    pay_delay   = fields.Integer(u"Délai de paiement",track_visibility='onchange')
    penalety    = fields.One2many('nabi.marche.penalety','marche',u"Pénalité de rétard en MAD",track_visibility='onchange')
    state       = fields.Selection([('draft','Brouillon'),('confirm','Confirmé'),('soumission','Soumission'),('affected','Affecté'),('end','Terminé'),('cancel',u'Annulé')],string="Etat", default="draft",track_visibility='onchange')
    bordereau_ids   = fields.One2many("project.project.soutraitant.bordereau","marche","Bordereau",track_visibility='onchange')
    attachement_ids   = fields.One2many("nabi.marche.attachement","marche","Attachements",track_visibility='onchange')
    notifs      = fields.One2many("nabi.marche.notif" ,"marche", "Ordres de notification",track_visibility='onchange')
    project     = fields.Many2one("project.project","Projet client")
    retenus      = fields.One2many('nabi.marche.retenu','marche',u"Retenus")
    ods         = fields.One2many('nabi.marche.ods','marche', 'Ordres de service')
    prc_attache = fields.Float(u"Pourcentage Attaché", compute=_prc_attache)
    commande    = fields.One2many('purchase.order', 'marche',u'Commandes / Avenant')
   
    

class nabi_marche_ods(models.Model):
    _name = "nabi.marche.ods"
    _description = u"Ordre de service"    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    marche      = fields.Many2one("nabi.marche", u"Marché",track_visibility='onchange')
    name        = fields.Char(u"Réf", default="/" , copy=False,track_visibility='onchange')
    date        = fields.Date(u"Date de l'ordre",track_visibility='onchange')
    objet       = fields.Char(u"Objet",track_visibility='onchange')
    motif       = fields.Char(u"Motif",track_visibility='onchange')
    date_start  = fields.Date(u"Date de début",track_visibility='onchange')
    date_end    = fields.Date(u"Date de fin",track_visibility='onchange')
    type        = fields.Selection([('start','commencement'),('stop',u"Arrêt"),
                                    ('restart',u"Reprise")], string=u"Type de l'ordre",track_visibility='onchange')
    state       = fields.Selection([('draft','Brouillon'),('confirm','Confirmé'),('sent',u'Envoyé'),('accused',u'Accusé')],string=u"Etat", default='draft')
    
    
    @api.model
    def create(self,vals):
        if 'name' not in vals:
            vals['name'] = '/'
        if 'name' in vals and vals['name'] == '/' :
            vals['name']= self.env['ir.sequence'].sudo().next_by_code('nabi.marche.ods')
        
        return super(nabi_marche_ods,self).create(vals)
    
    @api.onchange( "marche")
    def onchange_type_marche(self):
        TYPE= {'start':'stop',
                'restart':'stop',
                'stop':'restart',
                }
        self.type = False
        if  self.marche:
        
            last_ods = self.marche.ods.filtered(lambda  x:x.id != self.id)
            if last_ods :
                self.type = TYPE[last_ods[-1].type]
            else:
                self.type = 'start'
                


class nabi_marche_notification(models.Model):
    _name="nabi.marche.notif"
    _description = u"Notification"    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    marche  = fields.Many2one("nabi.marche", u"Marché",track_visibility='onchange')
    name    = fields.Char(u"Réf", default="/" , copy=False)
    state   = fields.Selection([('draft','Brouillon'),('confirm',u'Confirmé'),('sent',u'Envoyé'),('accused',u'Accusé')],string="Etat",track_visibility='onchange',default="draft")
    date    = fields.Date(u"Date de l'ordre",track_visibility='onchange')

class res_partner(models.Model):
    _inherit= "res.partner"

    rc      = fields.Char("RC")
    cnss    = fields.Char("CNSS")
    ice     = fields.Char("ICE")

class nabi_marche_attachement(models.Model):
    _name = "nabi.marche.attachement"
    _description = "Attachement de STT"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.one
    @api.depends('line','state','marche')
    def _get_amount(self):
        self.amount = sum([ x.amount for x in self.line])
        
        
    marche  = fields.Many2one("nabi.marche", u"Marché",track_visibility='onchange', ondelete="restrict")
    name    = fields.Char(u"Réf", default="/" , copy=False)
    state   = fields.Selection([('draft','Brouillon'),('confirm',u'Confirmé'),('sent',u'Envoyé'),('accused',u'Accusé'),('deleted',u'Supprimé')],string="Etat",track_visibility='onchange',default="draft")
    date    = fields.Date(u"Date",track_visibility='onchange')
    line    = fields.One2many( "nabi.marche.attachement.line" , "parent_id","Lignes")
    amount  = fields.Float("Montant",compute=_get_amount,store=True)
    partner  = fields.Char(string=u"Sous-Traitant",related="marche.partner.name.name",store=True)
    projet  = fields.Many2one("project.project", "Projet")
    
    
#    @api.multi
#    def unlink(self):
#        for o in self:
#            o.state = 'deleted'
#        return True
    
    @api.onchange("marche")
    def onchange_marche(self):
        if self.marche and self.marche.project:
            self.project = self.marche.project
        
    
   
        


class nabi_marche_attachement_line(models.Model):
    _name = "nabi.marche.attachement.line"
    _description = u"Attachement de STT, lignes"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.one
    @api.depends('prix','qty','parent_id')
    def _get_amount(self):
        self.amount = self.qty * self.prix
        
    
    parent_id  = fields.Many2one("nabi.marche.attachement", u"Attachement",track_visibility='onchange')
    name        = fields.Many2one('project.project.soutraitant.bordereau.line',u"Réf. prix")
    prix        = fields.Float("Prix", store=True, related="name.prix")
    qty         = fields.Float(u"Quantité")
    amount      = fields.Float(u"Montant", store=True, compute=_get_amount)

    
class project_project_soutraitant_bordereau(models.Model):
    _inherit="project.project.soutraitant.bordereau"
    
    marche  = fields.Many2one("nabi.marche", u"Marché",track_visibility='onchange')
    
    @api.multi
    def unlink(self):
        for o in self:
            if o.marche or o.project:
                raise Warning("Erreur","Vous ne pouvez par supprimer un bordereau active sur un contrat ou un projet !")
            else:
                o.unlink()
        return True

class project_project_soutraitant_bordereau_line(osv.osv):
    _inherit = "project.project.soutraitant.bordereau.line"

    def name_get(self, cr, uid, ids, context=None):
        result = []
        if not context:
            context={}
        rec_name = ''
        if 'rec_name' in context:
            rec_name = context.get('rec_name',False)
        
        if rec_name and rec_name in self._columns:
            for project in self.browse(cr, uid, ids, context):
                result.append((project.id, project[rec_name] ))
            return result
            
        
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, (project.code and (project.code + ' - ') or '') + project.name ))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))


class nabi_marche_penalety(models.Model):
    _name="nabi.marche.penalety"
    _description = u"Pénalités du marché"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    marche      = fields.Many2one("nabi.marche", u"Marché"  ,track_visibility='onchange')
    name        = fields.Char(u"Nom", default="/",copy=False,track_visibility='onchange')
    type        = fields.Selection([('p',u'Pourcentage'),('m','Montant')], string=u"Type d'application'", default="m")
    value       = fields.Float("Valeur")
    

class nabi_marche_retenu(models.Model):
    _name="nabi.marche.retenu"
    _description = u"Retenus du marché"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    marche      = fields.Many2one("nabi.marche", u"Marché"  ,track_visibility='onchange')
    sequence    = fields.Integer("Ordre")
    name        = fields.Char(u"Nom", default="/",copy=False,track_visibility='onchange')
    type        = fields.Selection([('p',u'Pourcentage'),('m','Montant')], string=u"Type d'application'", default="m")
    base        = fields.Selection([('b',u"Montant de  base"),('p',u"Sous-total")],string=u"Base de calcul")
    value       = fields.Float("Valeur")











