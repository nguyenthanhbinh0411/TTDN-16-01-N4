# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta

class HopDong(models.Model):
    _name = 'hop_dong'
    _description = 'Quản lý hợp đồng khách hàng'
    _rec_name = 'ten_hop_dong'
    _order = 'ngay_ky desc'

    ma_hop_dong = fields.Char("Mã hợp đồng", required=True, copy=False)
    ten_hop_dong = fields.Char("Tên hợp đồng", required=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    
    loai_hop_dong = fields.Selection([
        ('ban_hang', 'Hợp đồng bán hàng'),
        ('dich_vu', 'Hợp đồng dịch vụ'),
        ('thue', 'Hợp đồng thuê'),
        ('hop_tac', 'Hợp đồng hợp tác'),
        ('lao_dong', 'Hợp đồng lao động'),
        ('khac', 'Khác'),
    ], string="Loại hợp đồng", default='dich_vu')
    
    ngay_ky = fields.Date("Ngày ký", required=True, default=fields.Date.today)
    ngay_hieu_luc = fields.Date("Ngày hiệu lực")
    ngay_het_han = fields.Date("Ngày hết hạn")
    
    gia_tri = fields.Float("Giá trị hợp đồng")
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('hieu_luc', 'Đang hiệu lực'),
        ('het_han', 'Hết hạn'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap')
    
    mo_ta = fields.Text("Mô tả")
    dieu_khoan = fields.Html("Điều khoản")
    
    # File đính kèm
    file_hop_dong = fields.Binary("File hợp đồng")
    file_hop_dong_name = fields.Char("Tên file")
    
    # Liên kết với tài liệu
    tai_lieu_ids = fields.One2many('tai_lieu', 'hop_dong_id', string="Tài liệu đính kèm")
    
    con_hieu_luc = fields.Boolean(compute="_compute_con_hieu_luc", string="Còn hiệu lực", store=True)
    
    @api.depends('ngay_het_han', 'trang_thai')
    def _compute_con_hieu_luc(self):
        today = date.today()
        for record in self:
            if record.trang_thai == 'hieu_luc' and record.ngay_het_han:
                record.con_hieu_luc = record.ngay_het_han >= today
            else:
                record.con_hieu_luc = record.trang_thai == 'hieu_luc'
    
    _sql_constraints = [
        ('ma_hop_dong_unique', 'unique(ma_hop_dong)', 'Mã hợp đồng phải là duy nhất!')
    ]
    
    # Workflow methods
    def action_submit_for_approval(self):
        """Chuyển trạng thái từ Nháp sang Chờ duyệt và tạo văn bản đến."""
        for record in self:
            if record.trang_thai == 'nhap':
                record.trang_thai = 'cho_duyet'
                record._create_van_ban_den()
    
    def action_approve(self):
        """Duyệt hợp đồng - chuyển sang Hiệu lực và tạo văn bản đi."""
        for record in self:
            if record.trang_thai == 'cho_duyet':
                record.trang_thai = 'hieu_luc'
                record._create_van_ban_di()
                van_ban_den = self.env['van_ban_den'].search([('hop_dong_id', '=', record.id)], limit=1)
                if van_ban_den:
                    van_ban_den.write({'trang_thai': 'da_xu_ly'})
    
    def action_cancel(self):
        """Hủy hợp đồng"""
        for record in self:
            if record.trang_thai in ['nhap', 'cho_duyet', 'hieu_luc']:
                record.trang_thai = 'huy'
    
    def action_expire(self):
        """Đánh dấu hết hạn (có thể gọi tự động)"""
        for record in self:
            if record.trang_thai == 'hieu_luc':
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
        if self.env['van_ban_den'].search([('hop_dong_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('HD', 'Hợp đồng')
        count = self.env['van_ban_den'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"HD/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_den'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_den': fields.Date.today(),
            'ngay_van_ban': self.ngay_ky or fields.Date.today(),
            'noi_ban_hanh': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': '',
            'trich_yeu': f"Hợp đồng: {self.ten_hop_dong} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_xu_ly_id': self.nhan_vien_phu_trach_id.id if self.nhan_vien_phu_trach_id else False,
            'trang_thai': 'moi',
            'hop_dong_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'han_xu_ly': fields.Date.today() + timedelta(days=3),
            'file_dinh_kem': self.file_hop_dong,
            'ten_file': self.file_hop_dong_name,
            'ghi_chu': f"Văn bản tạo tự động khi gửi duyệt hợp đồng {self.ma_hop_dong}",
        })

    def _create_van_ban_di(self):
        self.ensure_one()
        if self.env['van_ban_di'].search([('hop_dong_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('HD', 'Hợp đồng')
        count = self.env['van_ban_di'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_van_ban', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"HD/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_di'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_van_ban': fields.Date.today(),
            'ngay_gui': fields.Date.today(),
            'noi_nhan': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': self.env.user.name,
            'trich_yeu': f"Duyệt hợp đồng: {self.ten_hop_dong} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_soan_thao_id': self.nhan_vien_phu_trach_id.id if self.nhan_vien_phu_trach_id else False,
            'don_vi_soan_thao_id': False,
            'trang_thai': 'da_gui',
            'hop_dong_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'file_dinh_kem': self.file_hop_dong,
            'ten_file': self.file_hop_dong_name,
            'ghi_chu': f"Văn bản tạo tự động khi duyệt hợp đồng {self.ma_hop_dong}",
        })
