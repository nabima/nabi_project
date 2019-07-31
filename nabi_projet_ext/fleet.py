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

class fleet_request(osv.osv):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name="fleet.request"
    _description = u"Demande de matériel"
    _columns = {
    
        'name' :        fields.char('name', default='/'),
        'company_id':   fields.many2one('res.company', u'Société' ) ,
        'metier':       fields.many2one('nabi.res.activity', u'Activité',ondelete="restrict"),
        'priority':     fields.selection([('1','Pas urgent'),('2','Normal'),('3','Urgent'),],string=u'Priorité',default='2'),
        'projet':       fields.many2one('project.project',u'Projet/compte',ondelete="restrict"),
        'odt':          fields.many2one('project.ods', u'Sous projet/compte',ondelete="restrict"),
        'state':        fields.selection([('draft','Demande'),('progress','Encours de traitement'),('done','Traitée'),('end',u'Terminé'),('suspendu','Suspendue'),('cancel','Annulée')],string='Etat',default=u"draft",track_visibility='onchange'),
        'note':         fields.text('Note',track_visibility='onchange'),
        'line':         fields.one2many('fleet.request.line','parent','Lignes',track_visibility='onchange',copy=True)
    }

    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        company_id  = vals.get('company_id', False)
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, 1, 'fleet.request', context=context) or '/'
        new_id = super(fleet_request, self).create(cr, uid, vals, context=context)
        return new_id

class fleet_request_line(osv.osv):
    _description = u"Lignes de demande de matériel"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name="fleet.request.line"
    _columns = {    
        'parent':       fields.many2one('fleet.request', 'parent',ondelete="restrict"),
        'name' :        fields.char('name',track_visibility='onchange'),
        'unit':         fields.many2one('fleet.unit',u'Unité',track_visibility='onchange',ondelete="restrict"),
        'qte':          fields.float(u'Qté',track_visibility='onchange'),
        'destination':  fields.char('Destination',track_visibility='onchange'),
        'date':         fields.datetime('Date',track_visibility='onchange'),
        'state':        fields.selection([('draft','Demande'),('progress','Encours de traitement'),('done','Traitée'),('end',u'Terminé'),('cancel','Annulée')],string='Etat',default=u"draft",track_visibility='onchange'),    
        'note':         fields.text('Note',track_visibility='onchange'),
        'duree':        fields.float(u"Durée"),
        "date_achat":   fields.date(u"Date d'achat"),
        "delai":        fields.float(u"Délai"),
    }

    
