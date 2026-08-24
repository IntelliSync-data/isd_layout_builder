{
    'name': 'ISD Layout Builder',
    'version': '18.0.1.0.0',
    'category': 'ISD Modules',
    'summary': 'Tạo và quản lý bố cục mặc định cho photo booth',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/isd_layout_type_views.xml',
        'views/isd_api_token_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'isd_layout_builder/static/src/xml/download_png.xml',
            'isd_layout_builder/static/src/js/download_png.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
