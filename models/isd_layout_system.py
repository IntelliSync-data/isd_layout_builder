from odoo import api, fields, models


class IsdLayoutSystem(models.Model):
    _name = 'isd.layout.system'
    _description = 'Layout System Frame'
    _order = 'no asc'

    layout_type_id = fields.Many2one(
        comodel_name='isd.layout.type',
        string='Layout Type',
        required=True,
        ondelete='cascade',
    )
    no = fields.Integer(string='STT')
    frame_type = fields.Selection(
        selection=[('image', 'Ảnh'), ('qr', 'QR')],
        string='Loại',
        default='image',
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    is_qr = fields.Boolean(
        string='Is QR',
        compute='_compute_is_qr',
        store=True,
    )
    x = fields.Float(string='Left (X)')
    y = fields.Float(string='Top (Y)')
    width = fields.Float(string='Width')
    height = fields.Float(string='Height')

    @api.depends('frame_type')
    def _compute_name(self):
        for rec in self:
            rec.name = 'rect' if rec.frame_type == 'qr' else 'image'

    @api.depends('frame_type')
    def _compute_is_qr(self):
        for rec in self:
            rec.is_qr = rec.frame_type == 'qr'
