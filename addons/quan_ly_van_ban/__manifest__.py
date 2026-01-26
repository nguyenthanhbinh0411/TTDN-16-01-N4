# -*- coding: utf-8 -*-
{
    'name': "Quản Lý Văn Bản",

    'summary': """
        Quản lý hợp đồng, báo giá và tài liệu số hóa""",

    'description': """
        Module quản lý văn bản bao gồm:
        - Quản lý văn bản đến/đi với OCR tự động
        - Danh mục loại văn bản
        - Quản lý hợp đồng với luồng duyệt đa cấp
        - Quản lý báo giá
        - Quản lý tài liệu số hóa
        - Lịch sử phiên bản với diff visualization
        - Chữ ký điện tử với PKI
        - Mẫu văn bản với Jinja2 templates
        - Luồng duyệt có điều kiện
        - Dashboard phân tích văn bản
        - Liên kết với khách hàng và nhân sự
        - Tự động hóa tạo văn bản đến khi gửi duyệt hợp đồng
        - Đính kèm file văn bản
    """,

    'author': "FIT-DNU",
    'website': "https://ttdn1501.aiotlabdnu.xyz/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Document Management',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'mail', 'nhan_su', 'quan_ly_khach_hang'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/loai_van_ban.xml',
        'views/van_ban_den.xml',
        'views/van_ban_di.xml',
        'views/hop_dong.xml',
        'views/bao_gia.xml',
        'views/tai_lieu.xml',
        'views/lich_su_phien_ban.xml',
        'views/chu_ky_dien_tu.xml',
        'views/mau_van_ban.xml',
        'views/luong_duyet.xml',
        'views/dashboard.xml',
        'views/approval_views.xml',
        'views/khach_hang_extend.xml',
        'views/yeu_cau_khach_hang.xml',
        'views/chatbot_action.xml',
        'views/menu.xml',
        'data/cron.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'quan_ly_van_ban/static/src/xml/chatbot_templates.xml',
        ],
        'web.assets_backend': [
            'quan_ly_van_ban/static/src/css/chatbot.css',
            'quan_ly_van_ban/static/src/js/chatbot_dialog.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
