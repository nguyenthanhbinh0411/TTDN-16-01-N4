# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta

class HoaDon(models.Model):
    _name = 'hoa_don'
    _description = 'Quản lý hóa đơn'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'so_hoa_don'
    _order = 'ngay_xuat desc'

    # Thông tin cơ bản
    so_hoa_don = fields.Char("Số hóa đơn", required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('hoa_don') or 'New')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng liên quan", ondelete='set null')
    
    # Ngày tháng
    ngay_xuat = fields.Date("Ngày xuất hóa đơn", default=fields.Date.today, required=True, tracking=True)
    han_thanh_toan = fields.Date("Hạn thanh toán", required=True, tracking=True)
    ngay_thanh_toan_du_kien = fields.Date("Ngày thanh toán dự kiến", compute='_compute_ngay_thanh_toan_du_kien', store=True)
    
    # Chi tiết hóa đơn
    hoa_don_chi_tiet_ids = fields.One2many('hoa_don_chi_tiet', 'hoa_don_id', string="Chi tiết hóa đơn")
    
    # Giá trị
    tong_gia_tri = fields.Float("Tổng giá trị", compute='_compute_tong_gia_tri', store=True, tracking=True)
    thue_vat = fields.Float("Thuế VAT (%)", default=10.0)
    tien_thue = fields.Float("Tiền thuế", compute='_compute_tien_thue', store=True)
    tong_thanh_toan = fields.Float("Tổng thanh toán", compute='_compute_tong_thanh_toan', store=True, tracking=True)
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    # Hình thức thanh toán
    hinh_thuc_thanh_toan = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('vi_dien_tu', 'Ví điện tử'),
        ('the_tin_dung', 'Thẻ tín dụng'),
        ('tra_gop', 'Trả góp'),
    ], string="Hình thức thanh toán", default='chuyen_khoan')
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('da_xuat', 'Đã xuất'),
        ('da_thanh_toan', 'Đã thanh toán'),
        ('qua_han', 'Quá hạn'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, tracking=True, compute='_compute_trang_thai', store=True)
    
    # Thanh toán
    thanh_toan_ids = fields.One2many('thanh_toan', 'hoa_don_id', string="Thanh toán")
    tong_da_thanh_toan = fields.Float("Tổng đã thanh toán", compute='_compute_tong_da_thanh_toan', store=True)
    con_no = fields.Float("Còn nợ", compute='_compute_con_no', store=True)
    
    # File đính kèm
    file_hoa_don = fields.Binary("File hóa đơn PDF")
    file_hoa_don_name = fields.Char("Tên file")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('so_hoa_don_unique', 'unique(so_hoa_don)', 'Số hóa đơn phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('so_hoa_don', 'New') == 'New':
            vals['so_hoa_don'] = self.env['ir.sequence'].next_by_code('hoa_don') or 'New'
        # Tự động set hạn thanh toán 30 ngày nếu không có
        if not vals.get('han_thanh_toan'):
            vals['han_thanh_toan'] = fields.Date.today() + timedelta(days=30)
        return super().create(vals)
    
    @api.depends('han_thanh_toan')
    def _compute_ngay_thanh_toan_du_kien(self):
        for record in self:
            record.ngay_thanh_toan_du_kien = record.han_thanh_toan
    
    @api.depends('hoa_don_chi_tiet_ids.thanh_tien')
    def _compute_tong_gia_tri(self):
        for record in self:
            record.tong_gia_tri = sum(line.thanh_tien for line in record.hoa_don_chi_tiet_ids)
    
    @api.depends('tong_gia_tri', 'thue_vat')
    def _compute_tien_thue(self):
        for record in self:
            record.tien_thue = record.tong_gia_tri * record.thue_vat / 100
    
    @api.depends('tong_gia_tri', 'tien_thue')
    def _compute_tong_thanh_toan(self):
        for record in self:
            record.tong_thanh_toan = record.tong_gia_tri + record.tien_thue
    
    @api.depends('thanh_toan_ids.so_tien')
    def _compute_tong_da_thanh_toan(self):
        for record in self:
            record.tong_da_thanh_toan = sum(tt.so_tien for tt in record.thanh_toan_ids if tt.trang_thai == 'da_xac_nhan')
    
    @api.depends('tong_thanh_toan', 'tong_da_thanh_toan')
    def _compute_con_no(self):
        for record in self:
            record.con_no = record.tong_thanh_toan - record.tong_da_thanh_toan
    
    @api.depends('han_thanh_toan', 'tong_da_thanh_toan', 'tong_thanh_toan')
    def _compute_trang_thai(self):
        today = fields.Date.today()
        for record in self:
            if record.trang_thai == 'huy':
                continue
            if record.con_no <= 0:
                record.trang_thai = 'da_thanh_toan'
            elif record.han_thanh_toan and record.han_thanh_toan < today and record.con_no > 0:
                record.trang_thai = 'qua_han'
            elif record.trang_thai == 'nhap':
                record.trang_thai = 'nhap'
            else:
                record.trang_thai = 'da_xuat'
    
    @api.onchange('don_hang_id')
    def _onchange_don_hang_id(self):
        """Tự động điền chi tiết hóa đơn từ đơn hàng được chọn"""
        if self.don_hang_id:
            # Xóa chi tiết hiện tại
            self.hoa_don_chi_tiet_ids = [(5, 0, 0)]
            
            # Tạo chi tiết mới từ đơn hàng
            chi_tiet_lines = []
            for chi_tiet in self.don_hang_id.don_hang_chi_tiet_ids:
                chi_tiet_lines.append((0, 0, {
                    'ten_san_pham': chi_tiet.ten_san_pham,
                    'mo_ta': chi_tiet.mo_ta,
                    'so_luong': chi_tiet.so_luong,
                    'don_vi_tinh': chi_tiet.don_vi_tinh,
                    'don_gia': chi_tiet.don_gia,
                }))
            
            self.hoa_don_chi_tiet_ids = chi_tiet_lines
            
            # Điền thông tin khách hàng nếu chưa có
            if not self.khach_hang_id and self.don_hang_id.khach_hang_id:
                self.khach_hang_id = self.don_hang_id.khach_hang_id.id
    
    def action_xuat_hoa_don(self):
        """Xuất hóa đơn"""
        for record in self:
            if record.trang_thai == 'nhap':
                record.trang_thai = 'da_xuat'
    
    def action_huy(self):
        """Hủy hóa đơn"""
        for record in self:
            if record.trang_thai in ['nhap', 'da_xuat']:
                record.trang_thai = 'huy'
    
    @api.model
    def create(self, vals):
        """Tự sinh số hóa đơn khi tạo mới"""
        if vals.get('so_hoa_don', 'New') == 'New':
            vals['so_hoa_don'] = self.env['ir.sequence'].next_by_code('hoa_don') or 'New'
        return super(HoaDon, self).create(vals)
    
    def action_view_thanh_toan(self):
        """Xem danh sách thanh toán"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Thanh toán',
            'res_model': 'thanh_toan',
            'view_mode': 'tree,form',
            'domain': [('hoa_don_id', '=', self.id)],
            'context': {'default_hoa_don_id': self.id, 'default_so_tien': self.con_no}
        }
    
    def action_check_payment_status(self):
        """Kiểm tra nếu hóa đơn liên kết với thanh toán thì đổi trạng thái từ da_xuat thành da_thanh_toan"""
        for record in self:
            if record.thanh_toan_ids and record.trang_thai == 'da_xuat':
                record.trang_thai = 'da_thanh_toan'
    
    def action_check_and_clear_debt(self):
        """Kiểm tra thanh toán và chuyển còn nợ về 0 nếu có thanh toán"""
        for record in self:
            if record.thanh_toan_ids:
                # Force set con_no = 0 nếu có thanh toán
                record.con_no = 0
                # Cập nhật trạng thái thành đã thanh toán
                record.trang_thai = 'da_thanh_toan'


class HoaDonChiTiet(models.Model):
    _name = 'hoa_don_chi_tiet'
    _description = 'Chi tiết hóa đơn'
    _rec_name = 'ten_san_pham'

    hoa_don_id = fields.Many2one('hoa_don', string="Hóa đơn", required=True, ondelete='cascade')
    ten_san_pham = fields.Char("Tên sản phẩm/Dịch vụ", required=True)
    mo_ta = fields.Text("Mô tả")
    so_luong = fields.Float("Số lượng", default=1.0, required=True)
    don_vi_tinh = fields.Char("Đơn vị tính", default='Cái')
    don_gia = fields.Float("Đơn giá", required=True)
    thanh_tien = fields.Float("Thành tiền", compute='_compute_thanh_tien', store=True)
    
    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.don_gia
