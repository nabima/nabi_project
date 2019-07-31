from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.tools import float_compare, float_round
import time

class project_prod_synthese(osv.osv):
    _name="project.prod.synthese"
    _auto=False
    _columns={        
    "id": fields.integer("Id"),
    "project" : fields.many2one("project.project", "Projet"),
    "ods" : fields.many2one("project.ods", "Ordre de service"),
    "date" : fields.date("Date"),    
    "qte" : fields.integer("Quantite"),
    "ref_prix" : fields.many2one("project.bordereau.line", "Ref. Prix"),
    "prix"    : fields.float("Mtt"),
    "address" : fields.many2one("project.address","Address"),

        }
    
    def init(self, cr):
       # self._table = sale_report
        
        cr.execute("""CREATE or REPLACE VIEW project_prod_synthese as 
            select      row_number() over() as id,                 p.project,p.lot as ods,p.date,l.qte,b.id as ref_prix, b.prix_net * l.qte as prix, p.address 
            
            from project_rapport p, project_rapport_prod l, project_bordereau_line b
            
            where   p.id = l.parent and b.id = l.name
                 
            """)

class stock_picking_synthese(osv.osv):
    _name="stock.picking.synthese"
    _auto=False
    _columns={        
    "id": fields.integer("Id"),
    "projet" : fields.many2one("project.project", "Projet"),
    "date" : fields.date("Date"),    
    "qte" : fields.float("Quantite"),
    "source" : fields.many2one("stock.location", "Source"),
    "destination" : fields.many2one("stock.location", "Destination"),    
    "article" : fields.many2one("product.product", "Article"),    
    "unite" : fields.many2one("product.uom", "Unite"),    
    "partner" : fields.many2one("res.partner", "fournisseur"),    
    "bl" : fields.char("Bon de livraison"),    
    "type" : fields.many2one("stock.picking.type", "Type"),    

    
    
        } 
    
    def init(self, cr):
       # self._table = sale_report
        
        cr.execute("""CREATE or REPLACE VIEW stock_picking_synthese as 
            select      row_number() over() as id,                  
                   
    stock_picking.x_account_analytic_id AS projet,
    stock_pack_operation.date::date,
    stock_pack_operation.product_qty  * t.nature AS qte,
    stock_pack_operation.location_id AS source,
    stock_pack_operation.location_dest_id AS destination,
    stock_pack_operation.product_id AS article,
    stock_pack_operation.product_uom_id AS unite,
    stock_picking.partner_id AS partner,
    stock_picking.x_no_bl AS bl,
    stock_picking.picking_type_id AS type
   FROM stock_picking,
    stock_pack_operation, stock_picking_type t
  WHERE stock_pack_operation.picking_id = stock_picking.id and stock_picking.picking_type_id = t.id
  ;

                 
            """)            
