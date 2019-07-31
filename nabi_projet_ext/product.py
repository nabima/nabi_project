# -*- encoding: utf-8 -*-


from openerp.osv import fields,osv



class product_template(osv.osv):
    _inherit = 'product.template'
    _columns ={
        'xml_id' : fields.function(osv.osv.get_xml_id, type='char', size=128, string="External ID",
                                  help="ID of the view defined in xml file"),
          }
