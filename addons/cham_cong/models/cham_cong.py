from odoo import models, fields, api

class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bản ghi chấm công'
    _order = 'ngay desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    ngay = fields.Date(string='Ngày', required=True, default=fields.Date.today)
    thoi_gian_check_in = fields.Datetime(string='Thời gian check-in')
    thoi_gian_check_out = fields.Datetime(string='Thời gian check-out')
    gio_lam_viec = fields.Float(string='Giờ làm việc', compute='_compute_gio_lam_viec', store=True)
    ghi_chu = fields.Text(string='Ghi chú')

    # Related fields for salary display
    luong_co_ban = fields.Float(related='nhan_vien_id.luong_co_ban', string='Lương cơ bản', readonly=True)
    so_ngay_cham_cong = fields.Integer(related='nhan_vien_id.so_ngay_cham_cong', string='Số ngày chấm công', readonly=True)
    luong_thuc_te = fields.Float(related='nhan_vien_id.luong_thuc_te', string='Lương thực tế', readonly=True)

    @api.depends('thoi_gian_check_in', 'thoi_gian_check_out')
    def _compute_gio_lam_viec(self):
        for record in self:
            if record.thoi_gian_check_in and record.thoi_gian_check_out:
                delta = record.thoi_gian_check_out - record.thoi_gian_check_in
                record.gio_lam_viec = delta.total_seconds() / 3600
            else:
                record.gio_lam_viec = 0.0
