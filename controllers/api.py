import json
import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

VALID_VIEWBOX_WIDTHS = ['144.57', '289.13', '430.87']
VALID_VIEWBOX_HEIGHTS = ['96.38', '192.75', '289.13']


def _cors_headers():
    return [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Origin, Content-Type, Accept, Authorization'),
    ]


def _json_response(data, status=200):
    return request.make_json_response(data, status=status, headers=_cors_headers())


def _error(message, code='error', status=400):
    return _json_response({'success': False, 'error': message, 'error_code': code}, status=status)


def _get_token_string():
    auth = request.httprequest.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return request.httprequest.args.get('token', '').strip()


def _authenticate():
    token_str = _get_token_string()
    if not token_str:
        return None, _error('Token is required', 'missing_token', 401)

    token = request.env['isd.api.token'].sudo().search([
        ('token', '=', token_str),
        ('expires_date', '>=', fields.Date.today()),
    ], limit=1)

    if not token:
        return None, _error('Invalid or expired token', 'unauthorized', 401)
    return token, None


def _layout_to_dict(layout):
    return {
        'id': layout.id,
        'name': layout.name,
        'view_box_width': layout.view_box_width,
        'view_box_height': layout.view_box_height,
        'frame_count': layout.frame_count,
        'print_width': layout.print_width,
        'print_height': layout.print_height,
        'actual_width': layout.actual_width,
        'actual_height': layout.actual_height,
        'is_cutted': layout.is_cutted,
        'is_landscape': layout.is_landscape,
        'print_top': layout.print_top,
        'print_left': layout.print_left,
        'print_bottom': layout.print_bottom,
        'print_right': layout.print_right,
        'systems': [{
            'id': s.id,
            'no': s.no,
            'frame_type': s.frame_type,
            'x': s.x,
            'y': s.y,
            'width': s.width,
            'height': s.height,
            'is_qr': s.is_qr,
        } for s in layout.system_ids],
    }


class LayoutApiController(http.Controller):

    # ── OPTIONS preflight ─────────────────────────────────────────────────────

    @http.route(['/api/layout/types', '/api/layout/types/<int:layout_id>'],
                type='http', auth='public', methods=['OPTIONS'], csrf=False)
    def options(self, **kwargs):
        return request.make_response('', headers=_cors_headers())

    # ── GET /api/layout/types ─────────────────────────────────────────────────

    @http.route('/api/layout/types', type='http', auth='public', methods=['GET'], csrf=False)
    def list_layouts(self, **kwargs):
        _, err = _authenticate()
        if err:
            return err

        layouts = request.env['isd.layout.type'].sudo().search([])
        return _json_response({
            'success': True,
            'total': len(layouts),
            'data': [_layout_to_dict(l) for l in layouts],
        })

    # ── GET /api/layout/types/<id> ────────────────────────────────────────────

    @http.route('/api/layout/types/<int:layout_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_layout(self, layout_id, **kwargs):
        _, err = _authenticate()
        if err:
            return err

        layout = request.env['isd.layout.type'].sudo().browse(layout_id)
        if not layout.exists():
            return _error('Layout not found', 'not_found', 404)

        return _json_response({'success': True, 'data': _layout_to_dict(layout)})

    # ── POST /api/layout/types ────────────────────────────────────────────────

    @http.route('/api/layout/types', type='http', auth='public', methods=['POST'], csrf=False)
    def create_layout(self, **kwargs):
        _, err = _authenticate()
        if err:
            return err

        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return _error('Invalid JSON body', 'invalid_json')

        name = data.get('name', '').strip()
        if not name:
            return _error('name is required', 'validation_error')

        view_box_width = str(data.get('view_box_width', ''))
        view_box_height = str(data.get('view_box_height', ''))
        if view_box_width not in VALID_VIEWBOX_WIDTHS:
            return _error(f'view_box_width must be one of {VALID_VIEWBOX_WIDTHS}', 'validation_error')
        if view_box_height not in VALID_VIEWBOX_HEIGHTS:
            return _error(f'view_box_height must be one of {VALID_VIEWBOX_HEIGHTS}', 'validation_error')

        frame_count = data.get('frame_count', 1)
        if not isinstance(frame_count, int) or frame_count < 1:
            return _error('frame_count must be a positive integer', 'validation_error')

        layout = request.env['isd.layout.type'].sudo().create({
            'name': name,
            'view_box_width': view_box_width,
            'view_box_height': view_box_height,
            'frame_count': frame_count,
        })

        return _json_response({'success': True, 'data': _layout_to_dict(layout)}, status=201)

    # ── PUT /api/layout/types/<id> ────────────────────────────────────────────

    @http.route('/api/layout/types/<int:layout_id>', type='http', auth='public', methods=['PUT'], csrf=False)
    def update_layout(self, layout_id, **kwargs):
        _, err = _authenticate()
        if err:
            return err

        layout = request.env['isd.layout.type'].sudo().browse(layout_id)
        if not layout.exists():
            return _error('Layout not found', 'not_found', 404)

        try:
            data = json.loads(request.httprequest.data.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return _error('Invalid JSON body', 'invalid_json')

        vals = {}
        if 'name' in data:
            vals['name'] = data['name'].strip()
        if 'view_box_width' in data:
            if str(data['view_box_width']) not in VALID_VIEWBOX_WIDTHS:
                return _error(f'view_box_width must be one of {VALID_VIEWBOX_WIDTHS}', 'validation_error')
            vals['view_box_width'] = str(data['view_box_width'])
        if 'view_box_height' in data:
            if str(data['view_box_height']) not in VALID_VIEWBOX_HEIGHTS:
                return _error(f'view_box_height must be one of {VALID_VIEWBOX_HEIGHTS}', 'validation_error')
            vals['view_box_height'] = str(data['view_box_height'])
        if 'frame_count' in data:
            if not isinstance(data['frame_count'], int) or data['frame_count'] < 1:
                return _error('frame_count must be a positive integer', 'validation_error')
            vals['frame_count'] = data['frame_count']

        if vals:
            layout.write(vals)

        return _json_response({'success': True, 'data': _layout_to_dict(layout)})

    # ── DELETE /api/layout/types/<id> ─────────────────────────────────────────

    @http.route('/api/layout/types/<int:layout_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_layout(self, layout_id, **kwargs):
        _, err = _authenticate()
        if err:
            return err

        layout = request.env['isd.layout.type'].sudo().browse(layout_id)
        if not layout.exists():
            return _error('Layout not found', 'not_found', 404)

        layout.unlink()
        return _json_response({'success': True, 'message': 'Layout deleted'})
