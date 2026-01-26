# -*- coding: utf-8 -*-

from odoo import models, fields, api

class GiaoHang(models.Model):
    _name = 'giao_hang'
    _description = 'Quản lý giao hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_giao_hang'
    _order = 'ngay_giao_hang_du_kien desc'

    # Thông tin cơ bản
    ma_giao_hang = fields.Char("Mã giao hàng", required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('giao_hang') or 'New')
    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng", required=True, tracking=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='don_hang_id.khach_hang_id', store=True)
    
    # Địa chỉ giao hàng
    dia_chi_giao_hang = fields.Text("Địa chỉ giao hàng", required=True)
    nguoi_nhan = fields.Char("Người nhận", required=True)
    so_dien_thoai_nguoi_nhan = fields.Char("Số điện thoại người nhận", required=True)
    
    # Ngày giờ
    ngay_giao_hang_du_kien = fields.Date("Ngày giao hàng dự kiến", tracking=True)
    ngay_giao_hang_thuc_te = fields.Date("Ngày giao hàng thực tế", tracking=True)
    gio_giao_hang = fields.Char("Giờ giao hàng")
    
    # Trạng thái vận chuyển
    trang_thai = fields.Selection([
        ('chuan_bi', 'Chuẩn bị'),
        ('dang_van_chuyen', 'Đang vận chuyển'),
        ('da_giao', 'Đã giao'),
        ('that_bai', 'Giao thất bại'),
        ('hoan_tra', 'Hoàn trả'),
    ], string="Trạng thái", default='chuan_bi', required=True, tracking=True)
    
    # Thông tin vận chuyển
    don_vi_van_chuyen = fields.Char("Đơn vị vận chuyển")
    ma_van_don = fields.Char("Mã vận đơn")
    phi_van_chuyen = fields.Float("Phí vận chuyển")
    
    # Người ký nhận
    nguoi_ky_nhan = fields.Char("Người ký nhận", tracking=True)
    ngay_ky_nhan = fields.Date("Ngày ký nhận", tracking=True)
    chu_ky_dien_tu = fields.Binary("Chữ ký điện tử")
    anh_xac_nhan = fields.Binary("Ảnh xác nhận giao hàng")
    
    # Lý do giao thất bại
    ly_do_that_bai = fields.Text("Lý do giao thất bại")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('ma_giao_hang_unique', 'unique(ma_giao_hang)', 'Mã giao hàng phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_giao_hang', 'New') == 'New':
            vals['ma_giao_hang'] = self.env['ir.sequence'].next_by_code('giao_hang') or 'New'
        return super().create(vals)
    
    @api.onchange('don_hang_id')
    def _onchange_don_hang(self):
        """Điền sẵn thông tin từ khách hàng"""
        if self.don_hang_id and self.don_hang_id.khach_hang_id:
            kh = self.don_hang_id.khach_hang_id
            self.dia_chi_giao_hang = kh.dia_chi
            self.nguoi_nhan = kh.ten_khach_hang
            self.so_dien_thoai_nguoi_nhan = kh.dien_thoai
    
    def action_bat_dau_van_chuyen(self):
        """Bắt đầu vận chuyển"""
        for record in self:
            if record.trang_thai == 'chuan_bi':
                record.trang_thai = 'dang_van_chuyen'
    
    def action_xac_nhan_da_giao(self):
        """Xác nhận đã giao hàng"""
        for record in self:
            if record.trang_thai == 'dang_van_chuyen':
                record.write({
                    'trang_thai': 'da_giao',
                    'ngay_giao_hang_thuc_te': fields.Date.today(),
                    'ngay_ky_nhan': fields.Date.today(),
                })
    
    def action_danh_dau_that_bai(self):
        """Đánh dấu giao thất bại"""
        for record in self:
            if record.trang_thai == 'dang_van_chuyen':
                record.trang_thai = 'that_bai'
    
    @api.model
    def create(self, vals):
        """Tự sinh mã giao hàng khi tạo mới"""
        if vals.get('ma_giao_hang', 'New') == 'New':
            vals['ma_giao_hang'] = self.env['ir.sequence'].next_by_code('giao_hang') or 'New'
        return super(GiaoHang, self).create(vals)
