# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ChuongTrinhKhachHangThanThiet(models.Model):
    _name = 'chuong_trinh_khach_hang_than_thiet'
    _description = 'Chương trình khách hàng thân thiết'
    _rec_name = 'khach_hang_id'

    # Thông tin cơ bản
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    
    # Tích điểm
    tong_diem = fields.Float("Tổng điểm", default=0.0, tracking=True)
    diem_da_su_dung = fields.Float("Điểm đã sử dụng", default=0.0)
    diem_kha_dung = fields.Float("Điểm khả dụng", compute='_compute_diem_kha_dung', store=True)
    
    # Hạng thành viên
    hang_thanh_vien = fields.Selection([
        ('dong', 'Đồng'),
        ('bac', 'Bạc'),
        ('vang', 'Vàng'),
        ('kim_cuong', 'Kim cương'),
    ], string="Hạng thành viên", default='dong', compute='_compute_hang_thanh_vien', store=True, tracking=True)
    
    # Lịch sử điểm
    lich_su_diem_ids = fields.One2many('lich_su_diem_thuong', 'chuong_trinh_id', string="Lịch sử điểm")
    
    # Ưu đãi đã nhận
    uu_dai_ids = fields.One2many('uu_dai_khach_hang', 'chuong_trinh_id', string="Ưu đãi đã nhận")
    
    @api.depends('tong_diem', 'diem_da_su_dung')
    def _compute_diem_kha_dung(self):
        for record in self:
            record.diem_kha_dung = record.tong_diem - record.diem_da_su_dung
    
    @api.depends('tong_diem')
    def _compute_hang_thanh_vien(self):
        """Tự động nâng hạng dựa trên điểm"""
        for record in self:
            if record.tong_diem >= 10000:
                record.hang_thanh_vien = 'kim_cuong'
            elif record.tong_diem >= 5000:
                record.hang_thanh_vien = 'vang'
            elif record.tong_diem >= 2000:
                record.hang_thanh_vien = 'bac'
            else:
                record.hang_thanh_vien = 'dong'
    
    def action_doi_qua(self, diem_doi, ten_qua):
        """Đổi điểm lấy quà"""
        self.ensure_one()
        if self.diem_kha_dung >= diem_doi:
            self.diem_da_su_dung += diem_doi
            # Tạo ưu đãi
            self.env['uu_dai_khach_hang'].create({
                'chuong_trinh_id': self.id,
                'ten_uu_dai': ten_qua,
                'diem_doi': diem_doi,
                'ngay_doi': fields.Date.today(),
            })
            return True
        return False


class LichSuDiemThuong(models.Model):
    _name = 'lich_su_diem_thuong'
    _description = 'Lịch sử điểm thưởng'
    _rec_name = 'mo_ta'
    _order = 'ngay_tao desc'

    chuong_trinh_id = fields.Many2one('chuong_trinh_khach_hang_than_thiet', string="Chương trình", required=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='chuong_trinh_id.khach_hang_id', store=True)
    
    # Điểm
    diem = fields.Float("Điểm", required=True)
    loai = fields.Selection([
        ('cong', 'Cộng điểm'),
        ('tru', 'Trừ điểm'),
    ], string="Loại", default='cong', required=True)
    
    # Nguồn gốc
    nguon_goc = fields.Selection([
        ('mua_hang', 'Mua hàng'),
        ('gioi_thieu', 'Giới thiệu khách hàng'),
    ], string="Nguồn gốc", default='mua_hang')
    
    mo_ta = fields.Char("Mô tả", required=True)
    ngay_tao = fields.Date("Ngày tạo", default=fields.Date.today, required=True)
    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng liên quan")


class UuDaiKhachHang(models.Model):
    _name = 'uu_dai_khach_hang'
    _description = 'Ưu đãi khách hàng'
    _rec_name = 'ten_uu_dai'
    _order = 'ngay_doi desc'

    chuong_trinh_id = fields.Many2one('chuong_trinh_khach_hang_than_thiet', string="Chương trình", required=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='chuong_trinh_id.khach_hang_id', store=True)
    
    ten_uu_dai = fields.Char("Tên ưu đãi", required=True)
    diem_doi = fields.Float("Điểm đổi", required=True)
    ngay_doi = fields.Date("Ngày đổi", default=fields.Date.today, required=True)
    ngay_het_han = fields.Date("Ngày hết hạn")
    
    trang_thai = fields.Selection([
        ('chua_su_dung', 'Chưa sử dụng'),
        ('da_su_dung', 'Đã sử dụng'),
        ('het_han', 'Hết hạn'),
    ], string="Trạng thái", default='chua_su_dung')
    
    ma_voucher = fields.Char("Mã voucher")
    ghi_chu = fields.Text("Ghi chú")
