# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime

class KhieuNaiPhanHoi(models.Model):
    _name = 'khieu_nai_phan_hoi'
    _description = 'Quản lý khiếu nại và phản hồi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tieu_de'
    _order = 'ngay_tao desc'

    # Thông tin cơ bản
    ma_khieu_nai = fields.Char("Mã khiếu nại", required=True, copy=False, default='New')
    tieu_de = fields.Char("Tiêu đề", required=True, tracking=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')

    # Phân loại
    loai = fields.Selection([
        ('san_pham', 'Sản phẩm'),
        ('dich_vu', 'Dịch vụ'),
        ('giao_hang', 'Giao hàng'),
        ('thanh_toan', 'Thanh toán'),
        ('khac', 'Khác'),
    ], string="Loại khiếu nại", default='khac', required=True, tracking=True)

    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp'),
    ], string="Độ ưu tiên", default='trung_binh', required=True, tracking=True)

    # Thời gian
    ngay_tao = fields.Date("Ngày tạo", default=fields.Date.today, required=True, tracking=True)
    han_xu_ly = fields.Date("Hạn xử lý", tracking=True)
    ngay_giai_quyet = fields.Date("Ngày giải quyết", tracking=True)

    # Người xử lý
    nguoi_xu_ly_id = fields.Many2one('nhan_vien', string="Người xử lý", tracking=True)

    # Trạng thái
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('cho_phan_hoi', 'Chờ phản hồi'),
        ('da_giai_quyet', 'Đã giải quyết'),
        ('dong', 'Đóng'),
    ], string="Trạng thái", default='moi', required=True, tracking=True)

    # Thời gian xử lý (tính theo giờ)
    thoi_gian_xu_ly = fields.Float("Thời gian xử lý (giờ)", compute='_compute_thoi_gian_xu_ly', store=True)

    # Đánh giá
    danh_gia_khach_hang = fields.Selection([
        ('rat_khong_hai_long', 'Rất không hài lòng'),
        ('khong_hai_long', 'Không hài lòng'),
        ('binh_thuong', 'Bình thường'),
        ('hai_long', 'Hài lòng'),
        ('rat_hai_long', 'Rất hài lòng'),
    ], string="Đánh giá khách hàng", tracking=True)

    # Nội dung chi tiết
    noi_dung = fields.Text("Nội dung khiếu nại", tracking=True)
    phuong_an_giai_quyet = fields.Text("Phương án giải quyết", tracking=True)
    ket_qua = fields.Text("Kết quả", tracking=True)

    # File đính kèm
    file_dinh_kem = fields.Binary("File đính kèm")
    file_dinh_kem_name = fields.Char("Tên file")

    @api.model
    def create(self, vals):
        if vals.get('ma_khieu_nai', 'New') == 'New':
            vals['ma_khieu_nai'] = self.env['ir.sequence'].next_by_code('khieu_nai_phan_hoi') or 'New'
        return super().create(vals)

    @api.depends('ngay_tao', 'ngay_giai_quyet')
    def _compute_thoi_gian_xu_ly(self):
        for record in self:
            if record.ngay_giai_quyet and record.ngay_tao:
                # Tính số ngày giữa ngày tạo và ngày giải quyết
                delta = record.ngay_giai_quyet - record.ngay_tao
                # Chuyển sang giờ (giả sử 8 giờ/ngày làm việc)
                record.thoi_gian_xu_ly = delta.days * 8
            else:
                record.thoi_gian_xu_ly = 0.0

    # Actions
    def action_bat_dau_xu_ly(self):
        self.write({'trang_thai': 'dang_xu_ly'})

    def action_giai_quyet(self):
        self.write({
            'trang_thai': 'da_giai_quyet',
            'ngay_giai_quyet': fields.Date.today()
        })

    def action_dong(self):
        self.write({'trang_thai': 'dong'})