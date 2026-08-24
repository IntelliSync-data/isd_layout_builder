from odoo import api, fields, models

VIEWBOX_TO_PRINT = {
    '144.57': 200,
    '289.13': 400,
    '430.87': 600,
}

VIEWBOX_TO_ACTUAL = {
    '144.57': 220,
    '289.13': 440,
    '430.87': 660,
}

MARGIN_MAP = {
    (600, 400): (5, 5, 3, 5),
    (400, 600): (5, 7, 4, 5),
    (600, 200): (5, 5, 5, 5),
    (200, 600): (5, 8, 5, 5.5),
}

DEFAULT_MARGIN = (5, 5, 5, 5)

VIEWBOX_SELECTION = [
    ('144.57', '144.57 (200px)'),
    ('289.13', '289.13 (400px)'),
    ('430.87', '430.87 (600px)'),
]


class IsdLayoutType(models.Model):
    _name = 'isd.layout.type'
    _description = 'Layout Type'

    name = fields.Char(string='Name', required=True)
    view_box_width = fields.Selection(
        selection=VIEWBOX_SELECTION,
        string='ViewBox Width',
        required=True,
    )
    view_box_height = fields.Selection(
        selection=VIEWBOX_SELECTION,
        string='ViewBox Height',
        required=True,
    )
    frame_count = fields.Integer(string='Number of Image Frames', default=1)
    dpi = fields.Integer(string='DPI', default=600, readonly=True)

    print_width = fields.Float(
        string='Print Width (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    print_height = fields.Float(
        string='Print Height (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    actual_width = fields.Float(
        string='Actual Width (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    actual_height = fields.Float(
        string='Actual Height (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    is_cutted = fields.Boolean(
        string='Is Cutted',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    is_landscape = fields.Boolean(
        string='Is Landscape',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    print_top = fields.Float(
        string='Print Top (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    print_left = fields.Float(
        string='Print Left (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    print_bottom = fields.Float(
        string='Print Bottom (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )
    print_right = fields.Float(
        string='Print Right (mm)',
        compute='_compute_print_dimensions',
        store=True,
        readonly=True,
    )

    system_ids = fields.One2many(
        comodel_name='isd.layout.system',
        inverse_name='layout_type_id',
        string='Layout Systems',
    )

    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html',
        store=False,
        sanitize=False,
        sanitize_tags=False,
        sanitize_attributes=False,
    )

    @api.depends('view_box_width', 'view_box_height')
    def _compute_print_dimensions(self):
        for rec in self:
            vbw = rec.view_box_width
            vbh = rec.view_box_height

            if vbw and vbh:
                pw = float(VIEWBOX_TO_PRINT.get(vbw, 0))
                ph = float(VIEWBOX_TO_PRINT.get(vbh, 0))
                aw = float(VIEWBOX_TO_ACTUAL.get(vbw, 0))
                ah = float(VIEWBOX_TO_ACTUAL.get(vbh, 0))
            else:
                pw = ph = aw = ah = 0.0

            rec.print_width = pw
            rec.print_height = ph
            rec.actual_width = aw
            rec.actual_height = ah

            rec.is_cutted = (pw == 200 or ph == 200)
            rec.is_landscape = (float(vbw or 0) > float(vbh or 0)) if (vbw and vbh) else False

            margin_key = (int(pw), int(ph))
            top, left, bottom, right = MARGIN_MAP.get(margin_key, DEFAULT_MARGIN)
            rec.print_top = top
            rec.print_left = left
            rec.print_bottom = bottom
            rec.print_right = right

    @api.depends('view_box_width', 'view_box_height', 'system_ids', 'system_ids.x',
                 'system_ids.y', 'system_ids.width', 'system_ids.height')
    def _compute_preview_html(self):
        for rec in self:
            vbw = rec.view_box_width or '289.13'
            vbh = rec.view_box_height or '289.13'

            vbw_float = float(vbw)
            vbh_float = float(vbh)

            # Scale SVG to fit 400px wide
            display_width = 400
            scale = display_width / vbw_float if vbw_float else 1
            display_height = vbh_float * scale

            rects = ''
            for system in rec.system_ids:
                rects += (
                    f'<rect x="{system.x}" y="{system.y}" '
                    f'width="{system.width}" height="{system.height}" '
                    f'fill="#ffffff" stroke="#aaaaaa" stroke-width="0.5"/>'
                )
                # Label each frame with its number
                cx = system.x + system.width / 2
                cy = system.y + system.height / 2
                label = 'QR' if system.is_qr else str(system.no)
                font_size = min(system.width, system.height) * 0.15 if (system.width and system.height) else 5
                rects += (
                    f'<text x="{cx}" y="{cy}" '
                    f'dominant-baseline="middle" text-anchor="middle" '
                    f'font-size="{font_size}" fill="#666666">{label}</text>'
                )

            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{display_width}" height="{display_height:.2f}" '
                f'viewBox="0 0 {vbw} {vbh}">'
                f'<rect width="{vbw}" height="{vbh}" fill="#cccccc"/>'
                f'{rects}'
                f'</svg>'
            )
            rec.preview_html = svg

    def action_init_systems(self):
        self.ensure_one()
        # Remove existing systems
        self.system_ids.unlink()

        systems_to_create = []
        for i in range(1, self.frame_count + 1):
            systems_to_create.append({
                'layout_type_id': self.id,
                'no': i,
                'frame_type': 'image',
                'x': 0.0,
                'y': 0.0,
                'width': 0.0,
                'height': 0.0,
            })
        # QR frame
        systems_to_create.append({
            'layout_type_id': self.id,
            'no': self.frame_count + 1,
            'frame_type': 'qr',
            'x': 0.0,
            'y': 0.0,
            'width': 0.0,
            'height': 0.0,
        })

        self.env['isd.layout.system'].create(systems_to_create)
        return True

    def action_download_png(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'isd_layout_builder.download_png',
            'params': {
                'record_id': self.id,
            },
        }
