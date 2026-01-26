from odoo import models, fields, api

class NhanVienExtend(models.Model):
    _inherit = 'nhan_vien'

    cham_cong_ids = fields.One2many('cham_cong', 'nhan_vien_id', string='Chấm công')
    so_ngay_cham_cong = fields.Integer(string='Số ngày chấm công', compute='_compute_so_ngay_cham_cong')
    tong_gio_lam_viec = fields.Float("Tổng giờ làm việc", compute="_compute_tong_gio_lam_viec", store=True)
    luong_thuc_te = fields.Float("Lương thực tế", compute="_compute_luong_thuc_te", store=True)

    def _compute_so_ngay_cham_cong(self):
        for record in self:
            record.so_ngay_cham_cong = len(record.cham_cong_ids)

    @api.depends('cham_cong_ids.gio_lam_viec')
    def _compute_tong_gio_lam_viec(self):
        for record in self:
            record.tong_gio_lam_viec = sum(record.cham_cong_ids.mapped('gio_lam_viec'))

    @api.depends('luong_co_ban', 'tong_gio_lam_viec')
    def _compute_luong_thuc_te(self):
        for record in self:
            if record.tong_gio_lam_viec > 0:
                record.luong_thuc_te = record.luong_co_ban * (record.tong_gio_lam_viec / 160.0)
            else:
                record.luong_thuc_te = record.luong_co_ban

    def action_view_cham_cong(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chấm công',
            'res_model': 'cham_cong',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.id)],
            'context': {'default_nhan_vien_id': self.id}
        }
