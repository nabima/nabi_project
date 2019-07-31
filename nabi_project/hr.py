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
from openerp import api


monnais = (200,
            100,
            50,
            20,
            10,
            5,
            2,
            1)

def billeter(val):
    res = ':'
    v = val
    for m in monnais:
        d = divmod(v,m)
        res = res + ',{}:{}'.format(m, (d[0] != 0.0 ) and int(d[0]) or ''   ) 

        v= d[1]
    
    return res


class employee(osv.osv):
    _inherit="hr.employee"
    
    def write(self, cr, uid, ids, vals, context=None):
        
        #if 'matricule' in vals:

            
            #vals['matricule'] = vals['matricule']  and ('0000000' + vals['matricule'])[-4:] or vals['matricule'] 
            
            

        res = super(employee,self).write(cr, uid, ids, vals, context=None)
        return res
    
    def heures(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.attendance:
                tx = tx + l.heures   
                
            
            res[obj.id] = tx or 0.0
        
        return res
    def jours(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.attendance:
                tx = tx + l.jours   
                
            
            res[obj.id] = tx or 0.0
        
        return res
        
    def recuperation_heures(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.recuperation:
                tx = tx + l.heures   
                
            
            res[obj.id] = tx or 0.0
        
        return res 
    def recuperation_jours(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.recuperation:
                tx = tx + l.jours   
                
            
            res[obj.id] = tx or 0.0
        
        return res   
    def credit_tt(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.credit:
                tx = (l.state == 'p') and tx + l.montant  or tx 
                
            
            res[obj.id] = tx or 0.0
        
        return res                             
            
    _columns={
        'taux_reel':fields.float('taux reel'),
        'taux_charge':      fields.float('taux de charge'),
        'matricule':        fields.char(u'Numéro de badge'),
        'attendance' :      fields.one2many('project.rapport.attendance.line','employee', 'Pointage'),
        'recuperation' :    fields.one2many('project.rapport.attendance.line','employee', 'Recuperation', domain=[('type','!=',False)]),
        'heures':           fields.function(heures,string=_("Total Heures "), type="float") ,
        'jours':            fields.function(jours,string=_("Total Jours "), type="float") ,
        'recuperation_heures':      fields.function(recuperation_heures,string=_("Recuperation heures "), type="float") ,
        'recuperation_jours':       fields.function(recuperation_jours,string=_("Recuperation jours "), type="float") ,
        'salaire_type':     fields.selection(string=_("type salaire"), selection=[('j',_('Journalier')),('f',_('Forfaitaire'))]),
        'salaire_frequence': fields.selection(string=_("Freq. paie"), selection=[('m',_('Mensuelle')),('b',_('Bimensuelle'))]),
        'absence':          fields.one2many('project.hr.absence','name',string=_('Absence')),
        'heures_sup':       fields.one2many('project.hr.hs','name',string=_('Heures sup.')),
        'credit':           fields.one2many('project.hr.employee.credit', 'employee', u'Crédit'),
        'credit_tt':        fields.function(credit_tt,string=_(u"Total crédit "), type="float") ,
        'chauffeur' :       fields.boolean('Chauffeur ?'),
        

    }
    def name_get(self, cr, uid, ids, context=None):
        result = []
        for project in self.browse(cr, uid, ids, context):
            result.append((project.id, project.name + (project.matricule and (' (' +project.matricule + ')' ) or '')   ))
        return result

   
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        ids = []
        if len(name) > 1:
            ids = self.search(cr, user, [('matricule', 'ilike', name)] + args,
                              limit=limit, context=context)

        search_domain = [('name', operator, name)]
        if ids:
            search_domain.append(('id', 'not in', ids))
        ids.extend(self.search(cr, user, search_domain + args,
                               limit=limit, context=context))

        locations = self.name_get(cr, user, ids, context)
        return sorted(locations, key=lambda (id, name): ids.index(id))
                 
class project_rapport_attendance(osv.osv):
    _name="project.rapport.attendance"


    def onchange_project(self, cr, uid, ids, project, context=None):
        p = self.pool.get('project.project').browse(cr, uid, project, context=context)
        return {'value': {
            'analytic_account_id': p.analytic_account_id.id,
            'ods' : False,
            
        }}

    def taux_reel(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.lines:
                if l.employee.salaire_type == 'j':
                    tx = tx + l.taux_reel    
                
            
            res[obj.id] = tx or 0.0

        return res

    def taux_charge(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            tx = 0.0
            for l in obj.lines:
                if l.employee.salaire_type == 'j':
                    tx = tx + l.taux_charge   
                
            
            res[obj.id] = tx or 0.0
        
        return res    
    
    def unlink_pay(self,cr,uid,ids,context=None)                :
        for o in self.browse(cr,uid,ids):
            if o.pay_journal:
                o.pay_journal = False
                o.state = 'v'
        print "###########\n %s \n############" % context               
        return {
                    'type': 'ir.actions.client',
                    'tag': 'auto_refresh',
                }
    
    
    READONLY_STATES = {
        'v': [('readonly', True)],
        'c': [('readonly', True)],
        't': [('readonly', True)],
        }
    
    _columns={
        'name':                 fields.char('Reference', default="new", required=True, states = READONLY_STATES ,copy=True),
        'state':                fields.selection(string="state",selection=[('n','New'),('cn',u'Confirmé'),('v1','Validation conducteur'),('v2','Validation Chef projet'),('v',u'Validé'),('t',u'Terminée'),('c','Canceled'),('r',u'Refusé')], default='n',copy=False),
        'date':                 fields.date('Date', required=True, states = READONLY_STATES),
        'project' :             fields.many2one('project.project', 'Projet', states = READONLY_STATES),
        'lot' :                 fields.many2one('project.project', 'Lot' , states = READONLY_STATES),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'  , required=False, states = READONLY_STATES),        
        'lines' :               fields.one2many('project.rapport.attendance.line', 'parent','lignes', required=False,ondelete="cascade", states = READONLY_STATES, copy=False),
        "ods" :                 fields.many2one("project.ods","Ordres de travail", states = READONLY_STATES),
        'taux_reel':            fields.function(taux_reel,string=_("Taux reel"), type="float",store=True, states = READONLY_STATES) ,
        'taux_charge':          fields.function(taux_charge,string=_("Taux charge"), type="float",store=True, states = READONLY_STATES), 
        'chef_equipe':          fields.many2one('hr.employee', string=_("Chef equipe"), states = READONLY_STATES),
        'chefequipe':           fields.many2many('hr.employee','project_attendance_chefequipe_rel','rapport_id','emp_id', string="Chef equipe", states = READONLY_STATES),
        'conducteur':           fields.many2many('hr.employee', 'project_attendance_chauffeur_rel','rapport_id','emp_id', string="Chauffeur"  , states = READONLY_STATES),
        'pay_journal':          fields.many2one('project.hr.pay.15', 'journal de paie'),
        }
        
    def copy(self, cr, uid, id, default={}, context=None):
        default = {'lines':[]}
        res =  super(project_rapport_attendance,self).copy(cr,uid,id,default,context)
        cr.execute("""
            insert into project_rapport_attendance_line (matricule,parent,employee,jours, heures,taux_reel,taux_charge,type,project,ods,analytic_account_id,date,create_uid,create_date,write_uid,write_date)
            select matricule,%s,employee,jours, heures,taux_reel,taux_charge,type,project,ods,analytic_account_id,date,create_uid,create_date,write_uid,write_date
            from project_rapport_attendance_line
            where parent = %s
            
        
        """ % (res, id))	
        
        
        return res 
        
        
        
class project_rapport_attendance_line(osv.osv):
    _name="project.rapport.attendance.line"
    
    def taux(self,cr,uid,ids,field_name,arg,context=None):
        res={            }
        for o in self.browse(cr,uid,ids):
            res[o.id]={'taux_reel':False,
                        'taux_charge':False
                    }
                    
            tr = o.employee.taux_reel or 0
            tc = o.employee.taux_charge or 0
            
            res[o.id]['taux_reel'] =   ((o.jours or 0.0) * tr) + ((o.heures or 0.0)  *  (tr /7.3461))
            res[o.id]['taux_charge'] = ((o.jours or 0.0) * tc) + ((o.heures or 0.0)  *  (tc /7.3461))
        
        return res
        
        
    def taux_reel(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        o = self.pool.get('hr.employee')
       
        for obj in self.browse(cr,uid,ids,context=context):
            #emp = o.browse(cr,uid,obj.employee.id)
            emp = obj.employee
            tx = emp.taux_reel or 0.0
            res[obj.id] = ((obj.jours or 0.0) * tx) + ((obj.heures or 0.0)  *  (tx /7.3461))
        
        return res

    def taux_charge(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        o = self.pool.get('hr.employee')
       
        for obj in self.browse(cr,uid,ids,context=context):
            #emp = o.browse(cr,uid,obj.employee.id)
            emp = obj.employee
            tx = emp.taux_charge or 0.0
            res[obj.id] = ((obj.jours or 0.0) * tx) + ((obj.heures or 0.0)  * (tx /7.3461))
        
        return res            
        
    _columns={
        'parent':       fields.many2one('project.rapport.attendance','parent',ondelete="cascade"),
        'employee':     fields.many2one('hr.employee', 'Employe', required=True),
        'jours' :       fields.float('Jours'),
        'heures' :      fields.float('Heures'),
        'taux_reel':    fields.function(taux,multi="all",string=_("Taux reel"), type="float",store=True) ,
        'taux_charge':  fields.function(taux,multi="all",string=_("Taux charge"), type="float",store=True),
        'type':         fields.many2one("hr.holidays.status", "Type") ,
        'project' :     fields.many2one('project.project', 'Projet'),
        "ods" :         fields.many2one("project.ods","Ordres de travail"),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'),
        'date':         fields.date('Date'),
        'matricule':    fields.char(related='employee.matricule',string=_("Matricule")) ,
        
        
    }
    
#    def write(self, cr, uid, ids, vals, context=None):
#        res = super(project_rapport_attendance_line,self).write(cr, uid, ids, vals,context) 
#        o = self.browse(cr,uid,ids)
#        self.pool['project.rapport.attendance'].write(cr,uid,o.parent.id,{'state':'n'},context)

#        return res
#        
#    def create(self, cr, uid, vals, context=None):
#        res = super(project_rapport_attendance_line,self).create(cr, uid, vals,context) 
#        o = self.browse(cr,uid,res)
#        self.pool['project.rapport.attendance'].write(cr,uid,o.parent.id,{'state':'n'},context)

#        return res   
    
class project_hr_pay_15(osv.osv):
    _name="project.hr.pay.15"
    
    def total_salaire(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        r= 0.0
       
        for obj in self.browse(cr,uid,ids,context=context):
            for l in obj.lines:
                
                r = r + (l.salaire or 0.0)

            res[obj.id] = r
        
        return res
    
    _columns = {
        'date_debut' :  fields.date(string = _("date de debut")),
        'date_fin' :    fields.date(string = _("date de fin")),
        'rapport' :     fields.one2many('project.rapport.attendance','pay_journal',string = _("Rapports de pointage"),ondelete="set null"),
        'lines' :       fields.one2many('project.hr.pay.15.line','parent',string = _("Detail de paie")),                
        'imputation' :  fields.one2many('project.hr.pay.15.imputation','parent',string = _("Imputation")),                        
        'state':        fields.selection(string=_('state'),selection=[('n',_('new')),('v',_('Valide'))]),
        'jour_ferie' :  fields.integer('jours férié'),
        'total_salaire': fields.function(total_salaire, string="Total salaire", type="float"),

    
    }
    def import_rapport(self,cr,uid,ids,context=None):
        o  = self.pool['project.hr.pay.15.line']
        r = self.pool['project.rapport.attendance']

        for p in self.browse(cr,1, ids):
            rids = r.search(cr,1,[('state','=','v'),('date','<=',p.date_fin),('date','>=',p.date_debut)])
            
            xx = 0
            vv = []
            rr = []
            for i in rids:
                vv.append((4,i))                
               
                                
            if vv:
                p.rapport = vv                
                for i in rids:
                    r.write(cr,1,i,{'state':'t'})
        
        return True

    def onchange_rapport(self, cr, uid, ids,rapport, context=None):

        return True 
        
    def write(self, cr, uid, ids, vals, context=None):
        rapport = []
        o = self.pool['project.rapport.attendance']
        if 'rapport' in vals:

            for v in vals['rapport']:
                if v[0] == 2:
                    v[0] = 3
                    o.write(cr, uid, v[1], {'state':'v'}, context=None)
                rapport.append(v)
            vals['rapport'] = rapport
            
            

        res = super(project_hr_pay_15,self).write(cr, uid, ids, vals, context=None)
        return res
    
    def calculer_pay(self,cr,uid,ids, context=None):
        line   = self.pool['project.hr.pay.15.line']
        parent = self.pool['project.hr.pay.15']
        ca_o   = self.pool['project.hr.employee.credit']
        o      = parent.browse(cr,uid,ids[0])
        jf     = self.pool['project.hr.holiday.public']._get_conge_count(cr,uid,ids,o.date_debut,o.date_fin)
        o.jour_ferie = jf or False
        req ="""select  a.pay_journal       as parent, 
                        al.employee,
                        sum(al.heures)      as heures,
                        sum(al.jours)       as jours,
                        round(sum(al.taux_reel) )  as taux_reel,
                        round(sum(al.taux_charge)) as taux_charge,
                        sum(case when al.type is not null then al.heures else null end)              as heures_recup,
	                    sum(case when al.type is not null then al.jours else null end)               as jours_recup
                        
                from   project_rapport_attendance a 
	                        inner join project_rapport_attendance_line al on al.parent = a.id
	                        inner join hr_employee e on e.id = al.employee
	                  
                where a.pay_journal = %s and e.salaire_type = 'j'
                group by a.pay_journal , al.employee """ % ids[0]
        
        cr.execute(req)
        res = cr.dictfetchall() or False
        
        if res :
            for x in self.browse(cr,uid,ids).lines:
                line.unlink(cr,uid,x.id)
            
            for r in res:
                credit_ca = 0.0               
                credit_a  = 0.0                 
                credit_c  = 0.0
                emp = self.pool['hr.employee'].browse(cr,uid,r['employee'])
                
                c_ids  = ca_o.search(cr,uid,[('employee','=',emp.id),('echeance','<=',o.date_fin),('echeance','>=',o.date_debut),('state','=','p')])

                for ca in ca_o.browse(cr,uid,c_ids):
                     
                    credit_a = (ca.type == 'a') and ca.montant + credit_a  or credit_a                
                    credit_c = (ca.type == 'c') and ca.montant + credit_c  or credit_c
                
                
                
                
                
                
                salaire = r['taux_reel'] - credit_a -  credit_c + ( jf * emp.taux_reel)
                
                
                
                r.update({
                    
                    'avance'        : credit_a,
                    'credit'        : credit_c,
                    'salaire'       : round(salaire),
                    'jour_ferie'    : jf,
                    
                    })
                    
                line.create(cr,uid,r)
                
        self.calculer_imputation(cr,uid,ids,o)
        return True
    
    def calculer_imputation(self,cr,uid,ids,o ,context=None):
        line = self.pool['project.hr.pay.15.imputation']
        
        
        req ="""select	a.pay_journal               as parent, 
	                    a.analytic_account_id                   ,
	                    lot.id                      as lot,
	                    m.id                        as metier,
	                    sum(al.heures)              as heures,
	                    sum(al.jours)               as jours,
	                    round(sum(al.taux_reel))           as taux_reel,
	                    round(sum(al.taux_charge))         as taux_charge,
	                    round( sum(al.taux_reel) )/ (sum(round(sum(al.taux_reel))) over()) as cle
	                    

                from   project_rapport_attendance a 
		                    inner join project_rapport_attendance_line al   on al.parent = a.id
		                    left  join project_ods o                        on o.id      = a.ods
		                    left  join project_lot lot                      on lot.id    = o.lot
		                    left  join project_metier m                     on m.id      = lot.metier
		                    inner join hr_employee e                        on e.id      = al.employee
                
                where a.pay_journal = %s and e.salaire_type = 'j'
                group by a.pay_journal ,a.analytic_account_id,lot.id, m.id """ % o.id
        
        cr.execute(req)
        res = cr.dictfetchall() or False
        
        if res :
            for x in self.browse(cr,uid,ids).imputation:
                line.unlink(cr,uid,x.id)
            
            for r in res:
                r.update({'amount' : o.total_salaire * r['cle']})
                line.create(cr,uid,r)
        return True    
    
class project_hr_pay_15_line(osv.osv):
    _name="project.hr.pay.15.line"
    
    def _billetage(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        r=[]
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            if obj.taux_reel:
                r = billeter(obj.taux_reel) or False
                
            res[obj.id] = r
        
        return res
        
    
    _columns = {
        'parent':       fields.many2one('project.hr.pay.15','parent'),
        'employee':     fields.many2one('hr.employee', 'Employe', required=True),
        'jours' :       fields.float('Jours'),
        'heures' :      fields.float('Heures'),
        'jours_recup' :       fields.float('Jours recup'),
        'heures_recup' :      fields.float('Heures recup'),
        'taux_reel':    fields.float(string=_("Taux reel")) ,
        'taux_charge':  fields.float(string=_("Taux charge")),
        'billetage' : fields.function(_billetage, string="Billetage" ,type="char"),
        'credit':    fields.float(string=_("Credit")) ,
        'avance':    fields.float(string=_("Avance")) ,
        'credit_tt':    fields.float(related='employee.credit_tt',string=_("Total Crédit"),store=True) ,
        'salaire':    fields.float(string=_("Salaire")) ,
        'matricule':    fields.char(related='employee.matricule',string=_("Matricule")) ,
        'jour_ferie' :  fields.integer(string='jours férié'),

    
    
    }
    
    @api.onchange('jour_ferie')
    def onchange_jr(self):
        self.salaire = self.taux_reel - self.credit -  self.avance +(self.employee.taux_reel * self.jour_ferie)
        
        
        
        
class project_hr_pay_15_imputation(osv.osv):
    _name="project.hr.pay.15.imputation"
    _columns = {
        'parent':fields.many2one('project.hr.pay.15','parent'),
        'jours' :       fields.float('Jours'),
        'heures' :      fields.float('Heures'),
        'taux_reel':    fields.float(string=_("Taux reel")) ,
        'taux_charge':  fields.float(string=_("Taux charge")),
        "lot" :         fields.many2one("project.lot","Lot", ondelete="restrict"),
        "metier" :         fields.many2one("project.metier","metier"),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'),
        'amount':    fields.float(string=_("Montant Imputation")) ,
        'date_debut' :  fields.date(related="parent.date_debut", string = _("date de debut")),
        'date_fin' :    fields.date(related="parent.date_fin", string = _("date de fin")),
    }         
        
class project_hr_absence(osv.osv):
    _name="project.hr.absence"
    _columns = {        
        'name':         fields.many2one('hr.employee',_('employee'),required=True),
        'date':         fields.date('Date',required=True),
        'jours':        fields.float(_('Nombre de jours')),
        'heures':       fields.float(_('Nombre heures')),
        'motif':        fields.many2one("hr.holidays.status", "Motif",required=True) ,
    }
    
class project_hr_hs(osv.osv):
    _name="project.hr.hs"
    _columns = {        
        'name':         fields.many2one('hr.employee',_('employee'),required=True),
        'date':         fields.date('Date',required=True),
        'jours':        fields.float(_('Nombre de jours')),
        'heures':       fields.float(_('Nombre heures')),
        'analytic_account_id' : fields.many2one('account.analytic.account', 'Compte Analytique'),
    }    
class hr_holidays_status(osv.osv):
    _inherit    = 'hr.holidays.status'
    _columns={
        'payed' :       fields.boolean(_('Payee')),
    }
    
class project_hr_pay_30(osv.osv):
    _name="project.hr.pay.30"
    
    def total_salaire(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        r= 0.0
       
        for obj in self.browse(cr,uid,ids,context=context):
            for l in obj.lines:
                
                r = r + (l.salaire or 0.0)

            res[obj.id] = r
        
        return res
        
    def jour_ferie(self, cr, uid, ids, field_name, arg, context=None):
        
        res={}
        
        for o in self.browse(cr,uid,ids,context=context):
            

            res[o.id] = self.pool['project.hr.holiday.public']._get_conge_count(cr,uid,ids,o.date_debut,o.date_fin)
        return res
        
    _columns = {
        'date_debut' :  fields.date(string = _("date de debut")),
        'date_fin' :    fields.date(string = _("date de fin")),
        'base': fields.selection(string='Base de salaire', selection=[(26,'Mensuel'),(13,'Bi-mensuel ')], default=30), 
        'lines' :       fields.one2many('project.hr.pay.30.line','parent',string = _("Detail de paie")),
        'state':        fields.selection(string=_('state'),selection=[('n',_('new')),('v',_('Valide'))]),
        'jour_ferie' :  fields.function(jour_ferie, string="jour_ferie", type="integer"),
        'total_salaire': fields.function(total_salaire, string="Total salaire", type="float"),
    }
    
    def calcul_salaire(self,cr,uid,ids,context=None): 
        emp_o    = self.pool['hr.employee']
        
        
        
        abs_o    = self.pool['project.hr.absence']
        hs_o     = self.pool['project.hr.hs']
        conge_o  = self.pool['hr.holidays']
        ca_o  = self.pool['project.hr.employee.credit']
        
        
        for o in self.browse(cr,uid,ids):
            #c_ids  = ca_o.search(cr,uid,[('echeance','<=',o.date_fin),('echeance','>=',o.date_debut),('type','=','c'),('state','=','p')])
            #a_ids  = ca_o.search(cr,uid,[('echeance','<=',o.date_fin),('echeance','>=',o.date_debut),('type','=','a'),('state','=','p')])
            #ca_ids  = ca_o.search(cr,uid,[('state','=','p')])
            date_debut = parser.parse(o.date_debut).date()
            date_fin = parser.parse(o.date_fin).date()            
            
            vals = []
            freq = (o.base == 26 and 'm') or (o.base == 13 and 'b') or 'm'
            emp_ids  = emp_o.search(cr,uid,[('salaire_type','=','f'),('salaire_frequence','=',freq),('active','=',True)])
            for emp in emp_o.browse(cr,uid,emp_ids): 
                # calcul credit
                
                credit_ca = 0.0               
                credit_a = 0.0                
                credit_c = 0.0
                c_ids  = ca_o.search(cr,uid,[('employee','=',emp.id),('echeance','<=',o.date_fin),('echeance','>=',o.date_debut),('state','=','p')])

                for ca in ca_o.browse(cr,uid,c_ids):
                     
                    credit_a = (ca.type == 'a') and ca.montant + credit_a  or credit_a                
                    credit_c = (ca.type == 'c') and ca.montant + credit_c  or credit_c
                    
                          
                      
                # calcul absence
                
                jours_recup = 0.0
                
                heures_recup = 0.0 
                heures_abs = 0.0            
                absence = 0.0
                
                salaire = 0.0
                
                
                abs_ids = abs_o.search(cr,uid,[('date','<=',o.date_fin),('date','>=',o.date_debut),('name','=',emp.id)]) 
                
                for a in abs_o.browse(cr,uid,abs_ids):
                    if a.motif.payed == True:
                        jours_recup     = jours_recup   + (a.jours or 0.0)
                        heures_recup    = heures_recup  +  (a.heures or 0.0) 
                    else:                                           
                        absence         = absence       + (a.jours or 0.0)                                           
                        heures_abs      = heures_abs    + (a.heures or 0.0)  
                
                # calcul HS
                heures_sup = 0.0
                jours_sup = 0.0
                hs_ids = hs_o.search(cr,uid,[('date','<=',o.date_fin),('date','>=',o.date_debut),('name','=',emp.id)])
                
                for h in hs_o.browse(cr,uid,hs_ids):
                    heures_sup = heures_sup + (h.heures or 0.0)
                    jours_sup = jours_sup + (h.jours or 0.0)
                
                # calcul conge
                conge = 0.0
                conge_ids = conge_o.search(cr,uid,[ ('employee_id','=',emp.id),'|',('date_from','>=',o.date_debut),('date_to','>=',o.date_debut)])

                
                for c in conge_o.browse(cr,uid,conge_ids):

                    date_from = parser.parse(c.date_from).date()
                    date_to = parser.parse(c.date_to).date()
                    
                    if date_from < date_debut:
                        nb = date_to - date_debut
                        conge = conge + nb.days +1 
                    else :
                        if date_to <= date_fin:
                            conge = conge + abs(c.number_of_days)
                        else :
                            nb = date_fin - date_from
                            conge = conge + nb.days +1
                        
                    

                
                jours_travail = (o.base - conge - jours_recup - absence + jours_sup-(o.jour_ferie or 0.0)) or 0.0
                jours_paye    = (o.base - absence) <= o.base and (o.base - absence) or o.base
                
                salaire  = jours_paye * (emp.taux_reel / o.base or 0.0) - credit_a - credit_c 
                
 
                val={
                    'parent'        : o.id,
                    'employee'      : emp.id,
                    'jours_travail' : jours_travail,    
                    'jours_recup'   : jours_recup ,
                    'jours_sup'     : jours_sup,

        
                    'heure_sup'     : heures_sup ,
                    'heure_recup'   : heures_recup ,                           

                    'absence'       : absence,
                    'conge'         : conge,
                    'salaire'       : salaire,
                    'jours_paye'    : jours_paye,
                    'avance'        : credit_a,
                    'credit'        : credit_c
                                       
                                   
                
                }
                lids = []
                for l in o.lines:
                    if l.employee.id == emp.id:
                        lids.append(l.id)
                        print '%s'.rjust(50,'#') % l.id
                print '%s'.rjust(50,'#') % [(2,x) for x in lids ]
                o.lines = [(2,x) for x in lids ]
                vals.append((0,0,val))
            o.lines=vals
        return True
                
            
            
        
class project_hr_pay_30_line(osv.osv):
    _name="project.hr.pay.30.line"
    
    
    def _billetage(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        r=[]
        
       
        for obj in self.browse(cr,uid,ids,context=context):
            if obj.salaire:
                r = billeter(obj.salaire) or False
                
            res[obj.id] = r
        
        return res
        
    _columns = {
        'parent':       fields.many2one('project.hr.pay.30','parent'),
        'employee':     fields.many2one('hr.employee', 'Employe', required=True),
        'jours_travail':fields.float(string=_('Jours travail')),
        'jours_paye':   fields.float(string=_('Jrs. a payee')),
        'jours_sup':    fields.float(string=_('Jrs. sup.')) ,
        'jours_recup':  fields.float(string=_('jrs. abs. paye')),        
        'heure_sup':    fields.float(string=_('Hrs. sup.')),
        'heure_recup':  fields.float(string=_('Hrs. abs.')),                           
        'absence':      fields.float(string=_('Jrs. absence')),
        'conge':        fields.float(string=_('Jrs. conge')),
        'salaire':      fields.float(string=_("Salaire")),
        'credit':       fields.float(string=_("Credit")),
        'avance':       fields.float(string=_("Avance")),
        'credit_tt':    fields.float(related='employee.credit_tt',string=_("Total Crédit"),store=True) ,
        'billetage' :   fields.function(_billetage, string="Billetage" ,type="char"),
        'matricule':    fields.char(related='employee.matricule',string=_("Matricule")) ,
        'jour_ferie':   fields.integer(related='parent.jour_ferie',string='jours férié'),
         
    }

    
class project_hr_employee_credit(osv.osv):
    _name="project.hr.employee.credit"
    _columns = {    
        'name':     fields.char('No. de bon'),
        'employee': fields.many2one('hr.employee','Employé'),
        'montant':  fields.float('Montant'),
        'motif':    fields.char('Motif'),
        'date' :    fields.date('Date'),
        'echeance': fields.date('Echeance'),
        'state' :   fields.selection(string="Etat",selection=(('v','Validé'),('p','Payé'),('r','Remboursé')), default='v') ,  
        'type' :    fields.selection(string="Type",selection=(('c','Credit'),('a','Avance')), required=True) ,
        'mensualite': fields.integer('Mensualité'),
        'prime':    fields.integer('Nbr. décompte'),
        'reglement' : fields.one2many('project.hr.employee.credit.reglement','parent','Réglements'),
        
        
    }
class project_hr_employee_credit_reglement(osv.osv):
    _name="project.hr.employee.credit.reglement"
    _columns = {
        'parent':   fields.many2one('project.hr.employee.credit','Parent'),
        'name':     fields.char('No. de bon'),
        'montant':  fields.float('Montant'),
        'date' :    fields.date('Date'),
    
     }
          

class hr_holiday_public(osv.osv):
    _name ="project.hr.holiday.public"
   
    def date_fin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
   
        for obj in self.browse(cr,uid,ids,context=context):
           
                
            
            res[obj.id] = parser.parse(obj.debut).date() + timedelta(days= (obj.nb_jours or 0.0))
        
        return res                              
    _columns={
        

        'debut': fields.date('Date début'),
        'fin': fields.function(date_fin, string='Date fin' ,type="date",store=True),
        'nb_jours': fields.integer('Nombre de jours'),
        'Description': fields.char('Description'),
        
    }
    
    def _get_conge_count(self,cr,uid,ids,debut,fin,context=None):
        
        cids = self.search(cr,uid,['|','&',('debut','>=',debut),('debut','<=',fin),'&',('fin','>=',debut),('fin','<=',fin)])

        res = 0.0
        for o in self.browse(cr,uid,cids):
            od = parser.parse(o.debut).date()
            of = parser.parse(o.fin).date()
            pd = parser.parse(debut).date()
            pf = parser.parse(fin).date()
            

            
            if od <= pd:
                res = (of - pd).days

            elif of >= pf : 
                res = (pf - od).days

            else:
                res = o.nb_jours

        

        return res or 0.0
    
    


class hr_charge_commune_journal(osv.osv):
    _name = "hr.charge.commune.journal"    
    _columns ={
    
        'name' :                fields.char('name'),
        'date':                 fields.date('date'),
        'line':                 fields.one2many('hr.charge.commune.line','parent','Lignes',copy=True),
        
    }    
class hr_charge_commune_line(osv.osv):
    _name = "hr.charge.commune.line"    
    _columns ={
    
        'name' :                fields.char('name'),
        'date':                 fields.date(related="parent.date",string='Date'),
        'analytic_account_id' : fields.many2one('account.analytic.account','Compta Analytique'),
        'amount' :              fields.float('Montant'),
        'parent':               fields.many2one('hr.charge.commune.journal','parent', ondelete="Restrict"),
        
    }    
class hr_accident_travail(osv.osv):
    _name="hr.accident.travail"
    _columns={
        'name':     fields.char('No. de bon'),
        'employee': fields.many2one('hr.employee','Employé'),
        'lieu':    fields.char('Lieu'),
        'secteur':    fields.char('Secteur'),        
        'date' :    fields.date('Date'),
        'nature': fields.many2one('hr.accident.travail.nature','Nature'),
        'itt':fields.integer('ITT'),
        'prolongation': fields.integer('Prolongation'),
        'arret': fields.integer('Tt Arrêt'),
        'guerison' :    fields.date('Guerison'),
        'accuse':fields.boolean('Accusé'),
            
    
    
    }
class hr_accident_travail_nature(osv.osv):
    _name ="hr.accident.travail.nature"
    _columns ={
        'name': fields.char('Name')
    
    }
class hr_epi_nature(osv.osv):
    _name ="hr.epi.nature"
    _columns ={
        'name': fields.char('Name')
    
    }    
    
class hr_epi(osv.osv):
    _name ="hr.epi"
    _columns ={
        'name':     fields.char('No. de bon'),
        'employee': fields.many2one('hr.employee','Employé'),
        'date' :    fields.date('Date'),
        'line': fields.one2many('hr.epi.line','parent', 'Lignes'),
        
    
    }
       
    
class hr_epi_line(osv.osv):
    _name ="hr.epi.line"
    _columns ={
        'parent':fields.many2one('hr.epi','Parent', ondelete="restrict"),
        'name':     fields.char('Name'),
        'employee': fields.related('parent','employee',readonly=True,type="many2one",   relation="hr.employee",string="Employé",store=True), 
        'date' :    fields.date(related="parent.date",string='Date'),
        
        'nature':   fields.many2one('hr.epi.nature','Nature'),
        'observation':fields.text('Observations'),
        'qte': fields.integer('Qte', default=1),
        
    
    }        
