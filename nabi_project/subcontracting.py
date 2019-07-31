# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
from datetime import datetime
from dateutil import parser
import time


class project_soutraitant(osv.osv):
    _name="project.soutraitant"
    _columns={
        'name': fields.many2one('res.partner','Sous-traitant'),
        'active': fields.boolean('Active',default=True),
    
    }
    
class project_ods(osv.osv):
    _inherit="project.ods"
    _columns={
        'soutraitant' : fields.many2one('project.soutraitant','Sous-traitant', ondelete="restrict"),
    }    

class project_project(osv.osv):
    _inherit="project.project"
    _columns={
        'soutraitant': fields.one2many('project.project.soutraitant','project','Sous-traitants')
    
    }   

class project_project_soutraitant(osv.osv):
    _name="project.project.soutraitant" 
    _columns={
        'project':  fields.many2one('project.project','Projet'),
        'name':     fields.many2one('project.soutraitant',string='Sous-traitants', oldname='soutraitant', ondelete="restrict"),
        'bordereau':fields.many2one('project.project.soutraitant.bordereau','Bordereau',ondelete="restrict"),
    
    }    
    
class project_project_soutraitant_bordereau(osv.osv):
    _name="project.project.soutraitant.bordereau"
    _columns={
        'name' :fields.char('Ref'),
        'project':fields.many2one('project.project','Projet'),
        'soutraitant': fields.many2one('project.soutraitant','Sous-traitants',ondelete="restrict"),
        'line': fields.one2many('project.project.soutraitant.bordereau.line','parent','Lignes',copy=True),
    } 
class project_project_soutraitant_bordereau_line(osv.osv):
    _name="project.project.soutraitant.bordereau.line"
    _columns={ 
        "parent":       fields.many2one("project.project.soutraitant.bordereau",ondelete="cascade" ),
        "sequence":     fields.integer('Sequence'),
        "code":         fields.char("No. Prix",oldname="name"),
        "name":  fields.char("Designation",oldname="designation"),
        "uom":          fields.many2one("product.uom","Unite",widget="selection" ),
        "qte_min":      fields.float("Qte. min", default=0.0),
        "qte_max":      fields.float("Qte. max", default=0.0),       
        "prix":         fields.float("Prix de base",default=0.0),
    
       }
class project_rapport_stt(osv.osv):
    _name="project.rapport.stt"
    
    def total_amount(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = ((o.qte or 0.0) * (o.name.prix or 0.0) ) or 0.0
        
        return res
        
    _columns={
        "parent":       fields.many2one("project.rapport"),
        "sequence":     fields.integer('Sequence'),
        'soutraitant':  fields.many2one('project.soutraitant','Sous-traitants', ondelete="restrict"),
        "name":         fields.many2one("project.project.soutraitant.bordereau.line","Code", ondelete="restrict"),
        "qte":          fields.float("Qte. realisee"),
        "total_amount": fields.function(total_amount, string='Montant Tt', type="float", store=True),        
        }    


class project_rapport(osv.osv):
    _inherit="project.rapport"
    
    def _total_amount_stt(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            x = 0.0 
            for l in o.stt:
                x = x + (l.total_amount or 0.0)
            
            res[o.id] = x
        
        return res
    _columns={
        "stt":    fields.one2many("project.rapport.stt","parent","Sous-taitance",copy=True),
        "total_amount_stt": fields.function(_total_amount_stt, string='Montant Tt Stt', type="float", store=True),        
    }           
