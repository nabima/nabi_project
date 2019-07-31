# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from xml.sax.saxutils import escape
import time
from openerp.osv import fields, osv
from datetime import datetime
from lxml import etree
from openerp import tools
from openerp.tools.translate import _
from openerp.exceptions import  Warning
from openerp import api
from openerp.tools import frozendict
from openerp import models



class hr_accident_travail_prolong(osv.osv):
    _name="hr.accident.travail.prolong"
    _columns = {
        'at' : fields.many2one('hr.accident.travail','AT'),
        'date': fields.date('date'),
        'jours': fields.integer('Nombre de jours'),
        'obs':  fields.text('Observations'),
    }
    
    def create(self, cr,uid,vals,context=None):
        
        lids = self.search(cr,uid,[('at','=',vals['at'])])
        
        for l in self.browse(cr,uid,lids):
            if l.date > vals['date']:
                raise Warning('Error',u"la date n'est pas valide")
        
        
        res = super(hr_accident_travail_prolong,self).create(cr,uid,vals)
        return res
    
    @api.onchange('date')
    def onchange_date(self):
        at = self.at
        raise Warning('test','%s' % [x.date for x in at.prolongation])
        for o in at.prolongation:
            
            if o.date > self.date:
                raise Warning('Error',u"la date n'est pas valide") 
    

class hr_accident_travail(osv.osv):
    _inherit="hr.accident.travail"
    
    def _prolong_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for o in self.browse(cr,uid,ids,context=context):
            
            res[o.id] =  sum([ x.jours for x in o.prolongation]) or 0.0
        return res
    
    _columns = {
        'prolongation':     fields.one2many('hr.accident.travail.prolong','at','Prolongation'),
        'prolong_count':    fields.function( _prolong_count, type="integer",string="Nb. jours prolongation"),
    }
    
    
class project_rapport_attendance(osv.osv):
    _inherit="project.rapport.attendance"
    READONLY_STATES = {
        'v': [('readonly', True)],
        'c': [('readonly', True)],
        't': [('readonly', True)],
        }
    _columns = {
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'  , required=False),
        'lines' :               fields.one2many('project.rapport.attendance.line', 'parent','lignes', required=False,ondelete="cascade", states = READONLY_STATES,copy=True),
    
    }
    
    @api.onchange('date','state')
    def onchange_date(self):
        for l in self.lines:
            l.date= self.date
            
    @api.onchange('state')
    def onchange_state(self):
        
        if  isinstance(self.id,(int,list) ) and self.state == 'n':
            
            
            self._cr.execute("""with 
                    a as (  select distinct l.employee , r."date" as dt
                            from project_rapport_attendance_line l 
                                    inner join project_rapport_attendance r on r.id = l.parent
                            where r.id=%s and coalesce(l.jours,0.0) <> 0.0 
                    )

                    select   ll.matricule as name, sum(coalesce(ll.jours,0.0)) as cnt, array_agg(rr.name ) as agg
                    from project_rapport_attendance_line ll 
                        inner join a on (a.employee = ll.employee and ll.date = a.dt )
                        inner join  project_rapport_attendance rr on ll.parent= rr.id
                        
                    
                    group by ll.matricule
                    having sum(coalesce(ll.jours,0)) > 1  """, (self.id,) )
            
            
            test = self._cr.dictfetchall()
            if test:
                #self.state='n'
                raise osv.except_osv(u"Employée saisie en double!",
                                     u"""L'employée (%s) est renseigné plusieurs fois dans les rapports %s \n 
                                        Eliminer les doublons avant la confirmation!\n
                                        ou Utiliser le champs (Heures) au de champs (jours)
                                        """ % (test[0]['name'],list(test[0]['agg'])))
            
    
    
    
    

class project_rapport_attendance_line(osv.osv):
    _inherit="project.rapport.attendance.line"
    
    def _get_selection(self,cr,uid,context=None):
        return [(r['id'],r['ref']) for r in self.pool['project.project'].search_read(cr,uid,[],['id','ref'])]
        
    _columns = {
        'project' :             fields.many2one('project.project', 'Projet',selection=_get_selection),
        "ods" :                 fields.many2one("project.ods","Ordres de travail"),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'),
    }
    
    @api.onchange('project')
    def onchange_project(self):
        if self.project:
            self.analytic_account_id = self.project.analytic_account_id
            self.ods = False
            #self.env.context = frozendict(self.env.context, default_project=self.project.id)
            
            #raise Warning('e','%s' % str(self.env))
            
            
class hr_employee(osv.osv):

    _inherit="hr.employee"
    
    _columns= {
        'etablissement':fields.char(u"Etablissement"),
        'departement':  fields.char(u"Département"),
        'unite':        fields.char(u'Unité'),
        'service':      fields.char(u'Service'),
        'matricule_sage':    fields.char("Matricule"),
        'date_in':fields.date(u"Date d'entrée'"),
        'date_out':     fields.date(u'date de sortie'),
        'salaire_base': fields.float(u"Salaire de base",groups='base.group_hr_user'),
        'date_embauche': fields.date(u"Date d'embauche"),
        'age':          fields.float(u"Age"),
        'anciennete':   fields.float(u"Ancienneté"),
        
        
        
        
        
        
    
    }









