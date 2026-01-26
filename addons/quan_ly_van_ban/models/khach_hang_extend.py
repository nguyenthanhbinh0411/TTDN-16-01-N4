# -*- coding: utf-8 -*-
from odoo import models, fields, api


class KhachHangVanBan(models.Model):
    _inherit = 'khach_hang'

    van_ban_den_ids = fields.One2many('van_ban_den', 'khach_hang_id', string="Văn bản đến")
    van_ban_di_ids = fields.One2many('van_ban_di', 'khach_hang_id', string="Văn bản đi")
    van_ban_den_count = fields.Integer(compute="_compute_counts", string="Số VB đến")
    van_ban_di_count = fields.Integer(compute="_compute_counts", string="Số VB đi")

    @api.depends('hop_dong_ids', 'bao_gia_ids', 'tai_lieu_ids', 'van_ban_den_ids', 'van_ban_di_ids')
    def _compute_counts(self):
        super()._compute_counts()
        for record in self:
            record.van_ban_den_count = len(record.van_ban_den_ids)
            record.van_ban_di_count = len(record.van_ban_di_ids)

    def action_view_van_ban_den(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Văn bản đến',
            'res_model': 'van_ban_den',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }

    def action_view_van_ban_di(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Văn bản đi',
            'res_model': 'van_ban_di',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }