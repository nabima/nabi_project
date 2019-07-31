# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round

import time


class project_planning_line_engin(osv.osv):
    _name="project.planning.line.engin"
    
    
    
    _columns={
        'planning_line_id': fields.many2one('project.planning.line','Ligne'),
        'name':            fields.char('name'),
        'engin':            fields.many2one('fleet.vehicle.model', 'Engin'),
        'qte':              fields.float('Nombre'),

     
    }
    
class project_planning_line_job(osv.osv):
    _name="project.planning.line.job"
    _columns={
        'planning_line_id': fields.many2one('project.planning.line','Ligne'),
        'name':            fields.char('name'),
        'job':            fields.many2one('hr.job', 'job'),
        'qte':              fields.float('Nombre'),
    
    }     

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, '%s (%s)' % (project.job , project.qte)   ))
        return result

class project_planning_line(osv.osv):
    _name="project.planning.line"
    
    def _engin_tags(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for e in self.browse(cr, uid, ids, context):
            if e.engin_ids:
                res[e.id] = " \r\n ".join(['%s:%s' % (x.qte, x.engin.name) for x in e.engin_ids])
            else:
                res[e.id] = _(u'-')
        return res
    def _employee_tags(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for e in self.browse(cr, uid, ids, context):
            if e.employee:
                res[e.id] = " \r\n ".join(['%s:%s' % (x.qte, x.job.name) for x in e.employee])
            else:
                res[e.id] = _(u'-')
        return res
    
    _columns={
    
        'parent':       fields.many2one("project.planning","Code planning"),
        'project':      fields.many2one('project.project','Projet'),
        'chef_equipe':  fields.many2one('hr.employee','Chef équipe'),
        'engin_ids':    fields.one2many('project.planning.line.engin','planning_line_id','Engins'),
        'employee':     fields.one2many('project.planning.line.job','planning_line_id','Employee'),
        'chauffeur':    fields.many2one('hr.employee','Chauffeur'),
        'travaux':      fields.text('Type de travaux'),
        'odt':          fields.many2one('project.ods','Ordre de travail'),
        'engin_tags':   fields.function(_engin_tags, method=True, type='char', string='Engins', store=False),               
        'employee_tags':   fields.function(_employee_tags, method=True, type='char', string='MO', store=False),               
        
    }

    
class project_planning(osv.osv):
    _name="project.planning"
    _columns={
    
        'name':     fields.char("Code planning"),
        'date':     fields.date("date"),
        'metier' :   fields.many2one('project.metier','Metier'),
        'state':    fields.selection(string="Etat", selection=[('n','Nouveau'),('v','Validé'),('a','Annulé')]),
        'line':     fields.one2many('project.planning.line','parent','Lignes'),
    
    }

class project_ods(osv.osv):
    _inherit="project.ods"
    _columns={
        'planning_line': fields.one2many('project.planning.line','odt','Lignes de planning', ondelete="restrict")
    }
    
