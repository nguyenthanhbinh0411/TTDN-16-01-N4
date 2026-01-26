# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class DonHang(models.Model):
    _name = 'don_hang'
    _description = 'Quản lý đơn hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_don_hang'
    _order = 'ngay_dat desc'

    # Thông tin cơ bản
    ma_don_hang = fields.Char("Mã đơn hàng", required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('don_hang') or 'New')
    ten_don_hang = fields.Char("Tên đơn hàng", required=True, tracking=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", tracking=True)
    
    # Ngày tháng
    ngay_dat = fields.Date("Ngày đặt", default=fields.Date.today, required=True, tracking=True)
    ngay_xac_nhan = fields.Date("Ngày xác nhận", tracking=True)
    ngay_hoan_thanh = fields.Date("Ngày hoàn thành", tracking=True)
    
    # Dòng sản phẩm/dịch vụ
    don_hang_chi_tiet_ids = fields.One2many('don_hang_chi_tiet', 'don_hang_id', string="Chi tiết đơn hàng")
    
    # Giá trị
    tong_gia_tri = fields.Float("Tổng giá trị", compute='_compute_tong_gia_tri', store=True, tracking=True)
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('xac_nhan', 'Đã xác nhận'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap', required=True, tracking=True)
    
    # Liên kết
    bao_gia_id = fields.Many2one('bao_gia', string="Báo giá liên quan", ondelete='set null')
    hop_dong_id = fields.Many2one('hop_dong', string="Hợp đồng liên quan", ondelete='set null')
    giao_hang_ids = fields.One2many('giao_hang', 'don_hang_id', string="Giao hàng")
    hoa_don_ids = fields.One2many('hoa_don', 'don_hang_id', string="Hóa đơn")
    
    # Counts
    giao_hang_count = fields.Integer(compute='_compute_counts', string="Số lần giao")
    hoa_don_count = fields.Integer(compute='_compute_counts', string="Số hóa đơn")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('ma_don_hang_unique', 'unique(ma_don_hang)', 'Mã đơn hàng phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_don_hang', 'New') == 'New':
            vals['ma_don_hang'] = self.env['ir.sequence'].next_by_code('don_hang') or 'New'
        return super().create(vals)
    
    @api.depends('don_hang_chi_tiet_ids.thanh_tien')
    def _compute_tong_gia_tri(self):
        for record in self:
            record.tong_gia_tri = sum(line.thanh_tien for line in record.don_hang_chi_tiet_ids)
    
    @api.depends('giao_hang_ids', 'hoa_don_ids')
    def _compute_counts(self):
        for record in self:
            record.giao_hang_count = len(record.giao_hang_ids)
            record.hoa_don_count = len(record.hoa_don_ids)
    
    def action_xac_nhan(self):
        """Xác nhận đơn hàng"""
        for record in self:
            if record.trang_thai == 'nhap':
                record.write({
                    'trang_thai': 'xac_nhan',
                    'ngay_xac_nhan': fields.Date.today(),
                })
    
    def action_bat_dau_thuc_hien(self):
        """Bắt đầu thực hiện đơn hàng"""
        for record in self:
            if record.trang_thai == 'xac_nhan':
                record.trang_thai = 'dang_thuc_hien'
    
    def action_hoan_thanh(self):
        """Hoàn thành đơn hàng"""
        for record in self:
            if record.trang_thai == 'dang_thuc_hien':
                record.write({
                    'trang_thai': 'hoan_thanh',
                    'ngay_hoan_thanh': fields.Date.today(),
                })
    
    def action_huy(self):
        """Hủy đơn hàng"""
        for record in self:
            if record.trang_thai in ['nhap', 'xac_nhan']:
                record.trang_thai = 'huy'
    
    @api.model
    def create(self, vals):
        """Tự sinh mã đơn hàng khi tạo mới"""
        if vals.get('ma_don_hang', 'New') == 'New':
            vals['ma_don_hang'] = self.env['ir.sequence'].next_by_code('don_hang') or 'New'
        return super(DonHang, self).create(vals)
    
    def action_view_giao_hang(self):
        """Xem danh sách giao hàng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Giao hàng',
            'res_model': 'giao_hang',
            'view_mode': 'tree,form',
            'domain': [('don_hang_id', '=', self.id)],
            'context': {'default_don_hang_id': self.id}
        }
    
    def action_view_hoa_don(self):
        """Xem danh sách hóa đơn"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hóa đơn',
            'res_model': 'hoa_don',
            'view_mode': 'tree,form',
            'domain': [('don_hang_id', '=', self.id)],
            'context': {'default_don_hang_id': self.id, 'default_khach_hang_id': self.khach_hang_id.id}
        }


class DonHangChiTiet(models.Model):
    _name = 'don_hang_chi_tiet'
    _description = 'Chi tiết đơn hàng'
    _rec_name = 'ten_san_pham'

    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng", required=True, ondelete='cascade')
    ten_san_pham = fields.Char("Tên sản phẩm/Dịch vụ", required=True)
    mo_ta = fields.Text("Mô tả")
    so_luong = fields.Float("Số lượng", default=1.0, required=True)
    don_vi_tinh = fields.Char("Đơn vị tính", default='Cái')
    don_gia = fields.Float("Đơn giá", required=True)
    thanh_tien = fields.Float("Thành tiền", compute='_compute_thanh_tien', store=True)
    ghi_chu = fields.Text("Ghi chú")
    
    @api.depends('so_luong', 'don_gia')
    def _compute_thanh_tien(self):
        for record in self:
            record.thanh_tien = record.so_luong * record.don_gia
