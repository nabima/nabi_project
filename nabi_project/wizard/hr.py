# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class project_rapport_attendance_wizard(osv.osv_memory):
    _name = 'project.rapport.attendance.wizard'
    _description = 'Automatic import employee'

    _columns = {
        
        'employee': fields.many2many('hr.employee','project_rapport_wizard_rel','wizard_id','employee_id' ), 
        
    }
    
    def _get_employee(self,cr,uid,ids):
        o = self.pool.get('hr.employee')
        emp = o.search(cr,uid,[]) or False
        if emp and emp != []:
            res = [(4,x) for x in emp] or False
        return  res
        
        
    _default = {
    'employee' : _get_employee
    
    }
    
    def importer(self, cr,uid,ids,context):
        o = self.pool['project.rapport.attendance']
        r = context.get('active_id',False)
        vals = []
        for w in self.browse(cr,uid,ids):
            vals = [(0,0,{'employee':x.id, 'jours':1}) for x in w.employee]
            
            
        if vals:   
            o.write(cr,uid,r,{'lines' : vals})




        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
