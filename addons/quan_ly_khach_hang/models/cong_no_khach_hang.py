# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class CongNoKhachHang(models.Model):
    _name = 'cong_no_khach_hang'
    _description = 'Công nợ khách hàng'
    _rec_name = 'khach_hang_id'

    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    
    # Tổng nợ
    tong_no = fields.Float("Tổng nợ", compute='_compute_cong_no', store=True)
    no_qua_han = fields.Float("Nợ quá hạn", compute='_compute_cong_no', store=True)
    no_chua_den_han = fields.Float("Nợ chưa đến hạn", compute='_compute_cong_no', store=True)
    
    # Ngày đến hạn gần nhất
    ngay_den_han_gan_nhat = fields.Date("Ngày đến hạn gần nhất", compute='_compute_cong_no', store=True)
    
    # Chi tiết công nợ theo từng hóa đơn
    hoa_don_chua_thanh_toan_ids = fields.One2many('hoa_don', compute='_compute_hoa_don_chua_tt', string="Hóa đơn chưa thanh toán")
    
    @api.depends('khach_hang_id', 'khach_hang_id.hoa_don_ids', 'khach_hang_id.hoa_don_ids.con_no', 'khach_hang_id.hoa_don_ids.han_thanh_toan')
    def _compute_cong_no(self):
        """Tính tổng công nợ từ hóa đơn"""
        today = date.today()
        for record in self:
            hoa_dons = record.khach_hang_id.hoa_don_ids.filtered(lambda h: h.con_no > 0)
            
            record.tong_no = sum(hoa_dons.mapped('con_no'))
            
            # Phân loại nợ quá hạn và chưa đến hạn
            no_qua_han = 0
            no_chua_den_han = 0
            ngay_gan_nhat = False
            
            for hd in hoa_dons:
                if hd.han_thanh_toan:
                    if hd.han_thanh_toan < today:
                        no_qua_han += hd.con_no
                    else:
                        no_chua_den_han += hd.con_no
                        if not ngay_gan_nhat or hd.han_thanh_toan < ngay_gan_nhat:
                            ngay_gan_nhat = hd.han_thanh_toan
            
            record.no_qua_han = no_qua_han
            record.no_chua_den_han = no_chua_den_han
            record.ngay_den_han_gan_nhat = ngay_gan_nhat
    
    def _compute_hoa_don_chua_tt(self):
        """Lấy danh sách hóa đơn chưa thanh toán"""
        for record in self:
            record.hoa_don_chua_thanh_toan_ids = record.khach_hang_id.hoa_don_ids.filtered(lambda h: h.con_no > 0)
