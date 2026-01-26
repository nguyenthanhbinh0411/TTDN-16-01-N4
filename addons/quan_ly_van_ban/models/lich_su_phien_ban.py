# -*- coding: utf-8 -*-

from odoo import models, fields, api
import difflib
import json

class LichSuPhienBan(models.Model):
    _name = 'lich.su.phien.ban'
    _description = 'Lịch sử phiên bản văn bản'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên phiên bản', required=True, tracking=True)
    van_ban_type = fields.Selection([
        ('van_ban_den', 'Văn bản đến'),
        ('van_ban_di', 'Văn bản đi'),
        ('hop_dong', 'Hợp đồng'),
        ('bao_gia', 'Báo giá'),
    ], string='Loại văn bản', required=True)
    van_ban_id = fields.Integer('ID Văn bản', required=True)
    van_ban_ref = fields.Reference(
        selection=[
            ('van_ban_den', 'Văn bản đến'),
            ('van_ban_di', 'Văn bản đi'),
            ('hop_dong', 'Hợp đồng'),
            ('bao_gia', 'Báo giá'),
        ],
        string='Tham chiếu văn bản'
    )
    
    phien_ban = fields.Integer('Số phiên bản', required=True, readonly=True)
    noi_dung = fields.Text('Nội dung', tracking=True)
    noi_dung_json = fields.Text('Nội dung JSON')  # Lưu toàn bộ dữ liệu dạng JSON
    file_dinh_kem = fields.Binary('File đính kèm')
    file_name = fields.Char('Tên file')
    
    nguoi_sua = fields.Many2one('nhan_vien', string='Người sửa', tracking=True)
    ngay_sua = fields.Datetime('Ngày sửa', default=fields.Datetime.now, tracking=True)
    ghi_chu_thay_doi = fields.Text('Ghi chú thay đổi', tracking=True)
    
    # So sánh với phiên bản trước
    diff_text = fields.Html('So sánh thay đổi', compute='_compute_diff', store=False)
    thay_doi_chinh = fields.Char('Thay đổi chính', compute='_compute_thay_doi_chinh', store=True)
    
    # Metadata
    ip_address = fields.Char('Địa chỉ IP')
    user_agent = fields.Char('User Agent')
    
    @api.depends('noi_dung', 'phien_ban')
    def _compute_thay_doi_chinh(self):
        for record in self:
            if record.phien_ban > 1:
                prev_version = self.search([
                    ('van_ban_type', '=', record.van_ban_type),
                    ('van_ban_id', '=', record.van_ban_id),
                    ('phien_ban', '=', record.phien_ban - 1)
                ], limit=1)
                if prev_version:
                    record.thay_doi_chinh = f"Cập nhật từ v{prev_version.phien_ban}"
                else:
                    record.thay_doi_chinh = "Phiên bản đầu tiên"
            else:
                record.thay_doi_chinh = "Phiên bản đầu tiên"
    
    def _compute_diff(self):
        for record in self:
            if record.phien_ban > 1:
                prev_version = self.search([
                    ('van_ban_type', '=', record.van_ban_type),
                    ('van_ban_id', '=', record.van_ban_id),
                    ('phien_ban', '=', record.phien_ban - 1)
                ], limit=1)
                
                if prev_version and prev_version.noi_dung and record.noi_dung:
                    diff = difflib.HtmlDiff()
                    record.diff_text = diff.make_table(
                        prev_version.noi_dung.splitlines(),
                        record.noi_dung.splitlines(),
                        f'Phiên bản {prev_version.phien_ban}',
                        f'Phiên bản {record.phien_ban}'
                    )
                else:
                    record.diff_text = '<p>Không có dữ liệu để so sánh</p>'
            else:
                record.diff_text = '<p>Đây là phiên bản đầu tiên</p>'
    
    def action_restore_version(self):
        """Khôi phục về phiên bản này"""
        self.ensure_one()
        if self.van_ban_ref:
            # Restore data from JSON
            if self.noi_dung_json:
                data = json.loads(self.noi_dung_json)
                self.van_ban_ref.write(data)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': f'Đã khôi phục về phiên bản {self.phien_ban}',
                    'type': 'success',
                    'sticky': False,
                }
            }
    
    @api.model
    def create_version(self, van_ban_type, van_ban_id, noi_dung, file_data=None, file_name=None, ghi_chu=''):
        """Tạo phiên bản mới cho văn bản"""
        latest = self.search([
            ('van_ban_type', '=', van_ban_type),
            ('van_ban_id', '=', van_ban_id)
        ], order='phien_ban desc', limit=1)
        
        next_version = (latest.phien_ban + 1) if latest else 1
        
        # Get reference model
        model_map = {
            'van_ban_den': 'van_ban_den',
            'van_ban_di': 'van_ban_di',
            'hop_dong': 'hop_dong',
            'bao_gia': 'bao_gia',
        }
        
        vals = {
            'name': f'Phiên bản {next_version}',
            'van_ban_type': van_ban_type,
            'van_ban_id': van_ban_id,
            'van_ban_ref': f'{model_map.get(van_ban_type)},{van_ban_id}',
            'phien_ban': next_version,
            'noi_dung': noi_dung,
            'ghi_chu_thay_doi': ghi_chu,
        }
        
        if file_data:
            vals['file_dinh_kem'] = file_data
            vals['file_name'] = file_name
        
        return self.create(vals)
