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
from datetime import *
from lxml import etree
from openerp.exceptions import  *
from openerp import models, fields as Fields, api, _,tools


class project_bordereau(osv.osv):
    _inherit="project.bordereau"
    _columns={
        'coef': fields.float('Coef. brd', default=False),
    }
    
class project_ods(osv.osv):
    _inherit = "project.ods"
    _columns ={
        'state': fields.selection([('new','Nouveau'),('progress','En cours'),('end',u'Terminée'),('delete',u'Supprimée')], string="Etat", default="new"),
            }
    
    ecart_ca= Fields.Float(u"Ecart CA Attaché/Produit", compute="calc_ecart")
    
    @api.multi
    def calc_ecart(self):
        for o in self:
            o.ecart_ca = o.ca_prod - o.ca_attachement
            
class project_attachement_line(models.Model):
    _inherit = "project.attachement.line"
    
    def unit_price(self, cr,uid,ids,field_name,arg,context=None): 
        res = {}
       
        for o in self.browse(cr,uid,ids,context=context):
            
            
            res[o.id] = (o.name and o.name.prix_net )  or 0.0
        
        return res
        
    _columns={
        "prix":         fields.function(unit_price,string="Prix",type="float",store=True),
    
    }
   # prix = Fields.Float(store=True)
    
    #_columns['prix'].store = True
     
class project_marche(osv.osv):
    _inherit="project.marche"
    
    date_visite = Fields.Datetime(u"Date visite des lieux")
    date_ouverture_plis = Fields.Datetime(u"Date d'ouverture des plis")
    metier      = Fields.Char(u"Métier")
    fiancement  = Fields.Char(u"Financement")
    offre       = Fields.Float(u"Offre HS")

class project_marche_concurrent(osv.osv):
    _inherit="project.marche.concurrent"
    
    offre       = Fields.Float(u"Offre financière")

class res_concurrent(osv.osv):
    
    #_inherit="res.partner"
    _inherit="res.concurrent"
    _columns={
        'name' : fields.char("Nom"),
    }




