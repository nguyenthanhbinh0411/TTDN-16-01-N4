from odoo import models, fields, api


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    cap_do = fields.Integer(string='Cấp độ', default=1, help='Cấp độ chức vụ để phân biệt thứ tự/độ quan trọng (số nguyên, 1 = cao nhất)')