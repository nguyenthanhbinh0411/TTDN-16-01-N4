# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
import base64
from datetime import datetime

class ChuKyDienTu(models.Model):
    _name = 'chu.ky.dien.tu'
    _description = 'Chữ ký điện tử'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Mã chữ ký', required=True, readonly=True, default='New', tracking=True)
    
    # Thông tin văn bản được ký
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
    
    # Thông tin người ký
    nguoi_ky = fields.Many2one('nhan_vien', string='Người ký', tracking=True)
    chuc_vu_ky = fields.Char('Chức vụ khi ký', tracking=True)
    ngay_ky = fields.Datetime('Ngày ký', default=fields.Datetime.now, required=True, tracking=True)
    
    # Chữ ký số
    chu_ky_image = fields.Binary('Hình ảnh chữ ký', attachment=True)
    chu_ky_image_name = fields.Char('Tên file chữ ký')
    
    # Hash và xác thực
    document_hash = fields.Char('Document Hash (SHA-256)', required=True, tracking=True)
    signature_hash = fields.Char('Signature Hash', tracking=True)
    is_verified = fields.Boolean('Đã xác thực', default=False, tracking=True)
    verification_date = fields.Datetime('Ngày xác thực', tracking=True)
    
    # Certificate info (mô phỏng PKI)
    certificate_serial = fields.Char('Serial Certificate', tracking=True)
    certificate_issuer = fields.Char('Certificate Issuer', default='Internal CA', tracking=True)
    certificate_valid_from = fields.Date('Hiệu lực từ', tracking=True)
    certificate_valid_to = fields.Date('Hiệu lực đến', tracking=True)
    
    # Metadata
    ip_address = fields.Char('Địa chỉ IP', tracking=True)
    user_agent = fields.Char('User Agent')
    location = fields.Char('Vị trí địa lý', tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('signed', 'Đã ký'),
        ('verified', 'Đã xác thực'),
        ('invalid', 'Không hợp lệ'),
        ('revoked', 'Đã thu hồi'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    ly_do_thu_hoi = fields.Text('Lý do thu hồi', tracking=True)
    ngay_thu_hoi = fields.Datetime('Ngày thu hồi', tracking=True)
    
    ghi_chu = fields.Text('Ghi chú', tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('chu.ky.dien.tu') or 'CK-' + fields.Datetime.now().strftime('%Y%m%d%H%M%S')
        return super(ChuKyDienTu, self).create(vals)
    
    def action_sign(self):
        """Thực hiện ký văn bản"""
        self.ensure_one()
        if self.trang_thai == 'draft':
            self.write({
                'trang_thai': 'signed',
                'ngay_ky': fields.Datetime.now(),
            })
            # Create version in history
            if self.van_ban_ref:
                self.env['lich.su.phien.ban'].create_version(
                    self.van_ban_type,
                    self.van_ban_id,
                    f'Đã ký bởi {self.nguoi_ky.name}',
                    ghi_chu=f'Chữ ký điện tử: {self.name}'
                )
    
    def action_verify(self):
        """Xác thực chữ ký"""
        self.ensure_one()
        # Simplified verification
        if self.document_hash and self.trang_thai == 'signed':
            self.write({
                'is_verified': True,
                'verification_date': fields.Datetime.now(),
                'trang_thai': 'verified',
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Xác thực thành công',
                    'message': 'Chữ ký điện tử hợp lệ',
                    'type': 'success',
                }
            }
        else:
            self.trang_thai = 'invalid'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Xác thực thất bại',
                    'message': 'Chữ ký điện tử không hợp lệ',
                    'type': 'danger',
                }
            }
    
    def action_revoke(self):
        """Thu hồi chữ ký"""
        self.ensure_one()
        return {
            'name': 'Thu hồi chữ ký',
            'type': 'ir.actions.act_window',
            'res_model': 'chu.ky.dien.tu',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'default_trang_thai': 'revoked'}
        }
    
    @api.model
    def generate_document_hash(self, content):
        """Tạo hash cho văn bản"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @api.model
    def create_signature(self, van_ban_type, van_ban_id, nguoi_ky_id, document_content, chu_ky_image=None):
        """Tạo chữ ký mới cho văn bản"""
        doc_hash = self.generate_document_hash(document_content)
        
        # Get reference model
        model_map = {
            'van_ban_den': 'van_ban_den',
            'van_ban_di': 'van_ban_di',
            'hop_dong': 'hop_dong',
            'bao_gia': 'bao_gia',
        }
        
        nguoi_ky = self.env['nhan_vien'].browse(nguoi_ky_id)
        
        vals = {
            'van_ban_type': van_ban_type,
            'van_ban_id': van_ban_id,
            'van_ban_ref': f'{model_map.get(van_ban_type)},{van_ban_id}',
            'nguoi_ky': nguoi_ky_id,
            'chuc_vu_ky': nguoi_ky.chuc_vu,
            'document_hash': doc_hash,
            'certificate_serial': f'CERT-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
            'certificate_valid_from': fields.Date.today(),
            'certificate_valid_to': fields.Date.add(fields.Date.today(), years=2),
            'trang_thai': 'draft',
        }
        
        if chu_ky_image:
            vals['chu_ky_image'] = chu_ky_image
        
        return self.create(vals)
