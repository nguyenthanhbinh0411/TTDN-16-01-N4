# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta

class BaoGia(models.Model):
    _name = 'bao_gia'
    _description = 'Quản lý báo giá'
    _rec_name = 'ten_bao_gia'
    _order = 'ngay_tao desc'

    ma_bao_gia = fields.Char("Mã báo giá", required=True, copy=False)
    ten_bao_gia = fields.Char("Tên báo giá", required=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng", ondelete='set null')
    
    ngay_tao = fields.Date("Ngày tạo", required=True, default=fields.Date.today)
    ngay_hieu_luc = fields.Date("Hiệu lực đến", default=lambda self: date.today() + timedelta(days=30))
    
    tong_gia_tri = fields.Float("Tổng giá trị")
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    nhan_vien_lap_id = fields.Many2one('nhan_vien', string="Nhân viên lập")
    
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('gui_khach', 'Đã gửi khách'),
        ('khach_dong_y', 'Khách đồng ý'),
        ('khach_tu_choi', 'Khách từ chối'),
        ('het_han', 'Hết hạn'),
    ], string="Trạng thái", default='nhap')
    
    noi_dung = fields.Html("Nội dung báo giá")
    ghi_chu = fields.Text("Ghi chú")
    
    # File đính kèm
    file_bao_gia = fields.Binary("File báo giá")
    file_bao_gia_name = fields.Char("Tên file")
    
    # Quan hệ với hợp đồng (nếu báo giá được chấp nhận)
    hop_dong_id = fields.Many2one('hop_dong', string="Hợp đồng liên quan")
    
    _sql_constraints = [
        ('ma_bao_gia_unique', 'unique(ma_bao_gia)', 'Mã báo giá phải là duy nhất!')
    ]
    
    # Workflow methods
    def action_send_to_customer(self):
        """Gửi báo giá cho khách hàng"""
        for record in self:
            if record.trang_thai == 'nhap':
                record.trang_thai = 'gui_khach'
                record._create_van_ban_den()
    
    def action_customer_approve(self):
        """Khách hàng đồng ý báo giá"""
        for record in self:
            if record.trang_thai == 'gui_khach':
                record.trang_thai = 'khach_dong_y'
    
    def action_customer_reject(self):
        """Khách hàng từ chối báo giá"""
        for record in self:
            if record.trang_thai == 'gui_khach':
                record.trang_thai = 'khach_tu_choi'
    
    def action_expire(self):
        """Báo giá hết hạn"""
        for record in self:
            if record.trang_thai in ['nhap', 'gui_khach']:
                record.trang_thai = 'het_han'

    def _get_loai_vb(self, ma_loai, ten):
        loai_vb = self.env['loai_van_ban'].search([('ma_loai', '=', ma_loai)], limit=1)
        if not loai_vb:
            loai_vb = self.env['loai_van_ban'].create({
                'ma_loai': ma_loai,
                'ten_loai': ten,
                'mo_ta': ten,
                'hoat_dong': True,
            })
        return loai_vb

    def _create_van_ban_den(self):
        self.ensure_one()
        if self.env['van_ban_den'].search([('bao_gia_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('BG', 'Báo giá')
        count = self.env['van_ban_den'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"BG/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_den'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_den': fields.Date.today(),
            'ngay_van_ban': self.ngay_tao or fields.Date.today(),
            'noi_ban_hanh': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': '',
            'trich_yeu': f"Báo giá: {self.ten_bao_gia} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_xu_ly_id': self.nhan_vien_lap_id.id if self.nhan_vien_lap_id else False,
            'trang_thai': 'moi',
            'bao_gia_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'han_xu_ly': fields.Date.today() + timedelta(days=3),
            'file_dinh_kem': self.file_bao_gia,
            'ten_file': self.file_bao_gia_name,
            'ghi_chu': f"Văn bản tạo tự động khi gửi báo giá {self.ma_bao_gia}",
        })
