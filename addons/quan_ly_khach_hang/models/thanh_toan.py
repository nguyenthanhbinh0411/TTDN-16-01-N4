# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ThanhToan(models.Model):
    _name = 'thanh_toan'
    _description = 'Quản lý thanh toán'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_thanh_toan'
    _order = 'ngay_thanh_toan desc'

    # Thông tin cơ bản
    ma_thanh_toan = fields.Char("Mã thanh toán", required=True, copy=False, default='New')
    hoa_don_id = fields.Many2one('hoa_don', string="Hóa đơn", required=True, tracking=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='hoa_don_id.khach_hang_id', store=True)
    
    # Số tiền
    so_tien = fields.Float("Số tiền thanh toán", required=True, tracking=True)
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    # Ngày thanh toán
    ngay_thanh_toan = fields.Date("Ngày thanh toán", default=fields.Date.today, required=True, tracking=True)
    
    # Hình thức thanh toán
    hinh_thuc = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('vi_dien_tu', 'Ví điện tử'),
        ('the_tin_dung', 'Thẻ tín dụng'),
        ('khac', 'Khác'),
    ], string="Hình thức thanh toán", default='chuyen_khoan', required=True, tracking=True)
    
    # Thông tin ngân hàng (nếu chuyển khoản)
    ten_ngan_hang = fields.Char("Tên ngân hàng")
    so_tai_khoan = fields.Char("Số tài khoản nhận")
    chu_tai_khoan = fields.Char("Chủ tài khoản")
    ma_giao_dich = fields.Char("Mã giao dịch", tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('cho_xac_nhan', 'Chờ xác nhận'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='cho_xac_nhan', required=True, tracking=True)
    
    # File đính kèm
    file_chung_tu = fields.Binary("File chứng từ")
    file_chung_tu_name = fields.Char("Tên file")
    
    # Người xác nhận
    nguoi_xac_nhan_id = fields.Many2one('res.users', string="Người xác nhận", tracking=True)
    ngay_xac_nhan = fields.Date("Ngày xác nhận", tracking=True)
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('ma_thanh_toan_unique', 'unique(ma_thanh_toan)', 'Mã thanh toán phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        """Tự sinh mã thanh toán khi tạo mới"""
        if vals.get('ma_thanh_toan', 'New') == 'New':
            vals['ma_thanh_toan'] = self.env['ir.sequence'].next_by_code('thanh_toan') or 'New'
        return super(ThanhToan, self).create(vals)
    
    def action_xac_nhan(self):
        """Xác nhận thanh toán và tự động cập nhật trạng thái hóa đơn"""
        for record in self:
            if record.trang_thai == 'cho_xac_nhan':
                record.write({
                    'trang_thai': 'da_xac_nhan',
                    'nguoi_xac_nhan_id': self.env.user.id,
                    'ngay_xac_nhan': fields.Date.today(),
                })
                # Tự động cập nhật trạng thái hóa đơn
                record._update_hoa_don_status()
    
    def _update_hoa_don_status(self):
        """Cập nhật trạng thái hóa đơn dựa trên tình trạng thanh toán"""
        self.ensure_one()
        hoa_don = self.hoa_don_id
        
        # Tính tổng số tiền đã thanh toán cho hóa đơn này
        tong_da_thanh_toan = sum(hoa_don.thanh_toan_ids.filtered(
            lambda t: t.trang_thai == 'da_xac_nhan'
        ).mapped('so_tien'))
        
        # Cập nhật tổng đã thanh toán
        hoa_don.tong_da_thanh_toan = tong_da_thanh_toan
        
        # Kiểm tra nếu hóa đơn đã được thanh toán đầy đủ
        if tong_da_thanh_toan >= hoa_don.tong_thanh_toan:
            # Chuyển trạng thái thành đã thanh toán và còn nợ về 0
            hoa_don.write({
                'trang_thai': 'da_thanh_toan',
                'con_no': 0.0
            })
            hoa_don.message_post(body=f"Hóa đơn đã được thanh toán đầy đủ. Tổng thanh toán: {tong_da_thanh_toan}")
        else:
            hoa_don.message_post(body=f"Đã thanh toán {tong_da_thanh_toan}, còn nợ {hoa_don.con_no}")
    
    def action_huy(self):
        """Hủy thanh toán"""
        for record in self:
            if record.trang_thai == 'cho_xac_nhan':
                record.trang_thai = 'huy'
