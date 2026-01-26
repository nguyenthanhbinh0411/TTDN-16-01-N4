# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LichSuTuongTac(models.Model):
    _name = 'lich_su_tuong_tac'
    _description = 'Lịch sử tương tác khách hàng'
    _rec_name = 'tieu_de'
    _order = 'ngay_tuong_tac desc'

    # Thông tin cơ bản
    tieu_de = fields.Char("Tiêu đề", required=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", default=lambda self: self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1).id or False)
    
    # Loại tương tác
    loai_tuong_tac = fields.Selection([
        ('cuoc_goi', 'Cuộc gọi'),
        ('email', 'Email'),
        ('hop', 'Họp'),
        ('demo', 'Demo sản phẩm'),
        ('tham_quan', 'Thăm quan'),
        ('su_kien', 'Sự kiện'),
        ('khac', 'Khác'),
    ], string="Loại tương tác", default='cuoc_goi', required=True)
    
    # Ngày giờ
    ngay_tuong_tac = fields.Datetime("Ngày giờ tương tác", default=fields.Datetime.now, required=True)
    thoi_luong = fields.Float("Thời lượng (phút)")
    
    # Nội dung
    noi_dung = fields.Html("Nội dung tương tác")
    ket_qua = fields.Text("Kết quả")
    
    # Ghi âm cuộc gọi (optional)
    file_ghi_am = fields.Binary("File ghi âm")
    file_ghi_am_name = fields.Char("Tên file")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")


class KhieuNaiPhanHoi(models.Model):
    _name = 'khieu_nai_phan_hoi'
    _description = 'Khiếu nại và phản hồi khách hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'tieu_de'
    _order = 'ngay_tao desc'

    # Thông tin cơ bản
    ma_khieu_nai = fields.Char("Mã khiếu nại", required=True, copy=False, default='New')
    tieu_de = fields.Char("Tiêu đề", required=True, tracking=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade', tracking=True)
    
    # Loại
    loai = fields.Selection([
        ('khieu_nai', 'Khiếu nại'),
        ('de_xuat', 'Đề xuất'),
        ('loi_san_pham', 'Lỗi sản phẩm'),
        ('phan_hoi_tich_cuc', 'Phản hồi tích cực'),
        ('khac', 'Khác'),
    ], string="Loại", default='khieu_nai', required=True, tracking=True)
    
    # Độ ưu tiên
    do_uu_tien = fields.Selection([
        ('thap', 'Thấp'),
        ('trung_binh', 'Trung bình'),
        ('cao', 'Cao'),
        ('khan_cap', 'Khẩn cấp'),
    ], string="Độ ưu tiên", default='trung_binh', required=True, tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('cho_phan_hoi', 'Chờ phản hồi'),
        ('da_giai_quyet', 'Đã giải quyết'),
        ('dong', 'Đóng'),
    ], string="Trạng thái", default='moi', required=True, tracking=True)
    
    # Nội dung
    noi_dung = fields.Html("Nội dung khiếu nại")
    phuong_an_giai_quyet = fields.Html("Phương án giải quyết")
    ket_qua = fields.Text("Kết quả xử lý")
    
    # Thời gian (SLA tracking)
    ngay_tao = fields.Datetime("Ngày tạo", default=fields.Datetime.now, required=True)
    han_xu_ly = fields.Datetime("Hạn xử lý", tracking=True)
    ngay_giai_quyet = fields.Datetime("Ngày giải quyết", tracking=True)
    thoi_gian_xu_ly = fields.Float("Thời gian xử lý (giờ)", compute='_compute_thoi_gian_xu_ly', store=True)
    
    # Người xử lý
    nguoi_xu_ly_id = fields.Many2one('nhan_vien', string="Người xử lý", tracking=True)
    
    # File đính kèm
    file_dinh_kem = fields.Binary("File đính kèm")
    file_dinh_kem_name = fields.Char("Tên file")
    
    # Đánh giá của khách hàng
    danh_gia_khach_hang = fields.Selection([
        ('1', '⭐ Rất không hài lòng'),
        ('2', '⭐⭐ Không hài lòng'),
        ('3', '⭐⭐⭐ Bình thường'),
        ('4', '⭐⭐⭐⭐ Hài lòng'),
        ('5', '⭐⭐⭐⭐⭐ Rất hài lòng'),
    ], string="Đánh giá của khách hàng")
    
    _sql_constraints = [
        ('ma_khieu_nai_unique', 'unique(ma_khieu_nai)', 'Mã khiếu nại phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_khieu_nai', 'New') == 'New':
            vals['ma_khieu_nai'] = self.env['ir.sequence'].next_by_code('khieu_nai_phan_hoi') or 'New'
        return super().create(vals)
    
    @api.depends('ngay_tao', 'ngay_giai_quyet')
    def _compute_thoi_gian_xu_ly(self):
        for record in self:
            if record.ngay_giai_quyet and record.ngay_tao:
                delta = record.ngay_giai_quyet - record.ngay_tao
                record.thoi_gian_xu_ly = delta.total_seconds() / 3600
            else:
                record.thoi_gian_xu_ly = 0
    
    def action_bat_dau_xu_ly(self):
        """Bắt đầu xử lý"""
        for record in self:
            if record.trang_thai == 'moi':
                record.trang_thai = 'dang_xu_ly'
    
    def action_giai_quyet(self):
        """Đánh dấu đã giải quyết"""
        for record in self:
            if record.trang_thai in ['dang_xu_ly', 'cho_phan_hoi']:
                record.write({
                    'trang_thai': 'da_giai_quyet',
                    'ngay_giai_quyet': fields.Datetime.now(),
                })
    
    def action_dong(self):
        """Đóng khiếu nại"""
        for record in self:
            if record.trang_thai == 'da_giai_quyet':
                record.trang_thai = 'dong'
