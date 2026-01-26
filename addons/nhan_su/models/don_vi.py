from odoo import models, fields, api


class DonVi(models.Model):
    _name = 'don_vi'
    _description = 'Bảng chứa thông tin đơn vị'
    _rec_name = 'ten_don_vi'
    _order = 'cap_do asc, ten_don_vi asc'

    ma_don_vi = fields.Char("Mã đơn vị", required=True)
    ten_don_vi = fields.Char("Tên đơn vị", required=True)
    cap_do = fields.Integer(string='Cấp độ', default=1, help='Cấp độ của đơn vị trong cấu trúc tổ chức (số nguyên, 1 = cao nhất)')