# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api


class YeuCauKhachHang(models.Model):
    _name = 'yeu_cau_khach_hang'
    _description = 'Yêu cầu / Khiếu nại khách hàng'
    _order = 'create_date desc'

    name = fields.Char('Tiêu đề', required=True)
    loai = fields.Selection([
        ('yeu_cau', 'Yêu cầu'),
        ('khieu_nai', 'Khiếu nại'),
    ], string='Loại', default='yeu_cau', required=True)
    khach_hang_id = fields.Many2one('khach_hang', string='Khách hàng', required=True, ondelete='cascade')
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string='Nhân viên phụ trách', ondelete='set null')
    don_vi_id = fields.Many2one('don_vi', string='Đơn vị phụ trách', ondelete='set null')
    han_xu_ly = fields.Date('Hạn xử lý', default=lambda self: fields.Date.today() + timedelta(days=3))
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('hoan_tat', 'Hoàn tất'),
        ('huy', 'Hủy'),
    ], string='Trạng thái', default='moi')
    noi_dung = fields.Text('Nội dung')
    van_ban_den_id = fields.Many2one('van_ban_den', string='Văn bản đến', ondelete='set null', readonly=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._create_van_ban_den()
        return record

    def _get_loai_vb(self):
        loai_vb = self.env['loai_van_ban'].search([('ma_loai', '=', 'YC')], limit=1)
        if not loai_vb:
            loai_vb = self.env['loai_van_ban'].create({
                'ma_loai': 'YC',
                'ten_loai': 'Yêu cầu/ Khiếu nại',
                'mo_ta': 'Văn bản yêu cầu/ khiếu nại',
                'hoat_dong': True,
            })
        return loai_vb

    def _create_van_ban_den(self):
        for record in self:
            if record.van_ban_den_id:
                continue
            loai_vb = record._get_loai_vb()
            count = self.env['van_ban_den'].search_count([
                ('loai_van_ban_id', '=', loai_vb.id),
                ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
            ]) + 1
            so_ky_hieu = f"YC/{count:04d}/{fields.Date.today().year}"
            vb = self.env['van_ban_den'].create({
                'so_ky_hieu': so_ky_hieu,
                'ngay_den': fields.Date.today(),
                'ngay_van_ban': fields.Date.today(),
                'noi_ban_hanh': record.khach_hang_id.ten_khach_hang or 'Khách hàng',
                'nguoi_ky': '',
                'trich_yeu': f"{dict(record._fields['loai'].selection).get(record.loai, '')} - {record.name}",
                'loai_van_ban_id': loai_vb.id,
                'do_khan': 'thuong',
                'do_mat': 'binh_thuong',
                'nguoi_xu_ly_id': record.nhan_vien_phu_trach_id.id if record.nhan_vien_phu_trach_id else False,
                'han_xu_ly': record.han_xu_ly or fields.Date.today() + timedelta(days=3),
                'trang_thai': 'moi',
                'khach_hang_id': record.khach_hang_id.id,
                'ghi_chu': 'Văn bản tự động sinh từ yêu cầu/khiếu nại',
            })
            record.van_ban_den_id = vb.id
