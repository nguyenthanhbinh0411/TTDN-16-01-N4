# -*- coding: utf-8 -*-

from odoo import models, fields, api
from jinja2 import Template

class MauVanBan(models.Model):
    _name = 'mau.van.ban'
    _description = 'Mẫu văn bản'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên mẫu', required=True, tracking=True)
    ma_mau = fields.Char('Mã mẫu', required=True, tracking=True)
    sequence = fields.Integer('Thứ tự', default=10)
    
    loai_van_ban = fields.Selection([
        ('hop_dong', 'Hợp đồng'),
        ('bao_gia', 'Báo giá'),
        ('bien_ban', 'Biên bản'),
        ('quyet_dinh', 'Quyết định'),
        ('cong_van', 'Công văn'),
        ('thong_bao', 'Thông báo'),
        ('bao_cao', 'Báo cáo'),
    ], string='Loại văn bản', required=True, tracking=True)
    
    # Nội dung mẫu
    noi_dung_html = fields.Html('Nội dung HTML', tracking=True)
    noi_dung_text = fields.Text('Nội dung Text')
    
    # Template variables
    bien_mau = fields.Text('Biến mẫu', help='Danh sách biến có thể dùng trong mẫu (JSON format)', 
                           default='{"khach_hang": "Tên khách hàng", "so_hop_dong": "Số hợp đồng", "ngay_ky": "Ngày ký"}')
    huong_dan = fields.Html('Hướng dẫn sử dụng')
    
    # File mẫu
    file_mau = fields.Binary('File mẫu (DOCX/PDF)', attachment=True)
    file_mau_name = fields.Char('Tên file mẫu')
    
    # Thiết lập
    active = fields.Boolean('Hoạt động', default=True)
    mo_ta = fields.Text('Mô tả', tracking=True)
    
    # Thống kê sử dụng
    so_lan_su_dung = fields.Integer('Số lần sử dụng', default=0, readonly=True)
    lan_su_dung_gan_nhat = fields.Datetime('Lần sử dụng gần nhất', readonly=True)
    
    # Default values
    gia_tri_mac_dinh = fields.Text('Giá trị mặc định (JSON)', 
                                    default='{}',
                                    help='Giá trị mặc định cho các biến')
    
    def action_preview(self):
        """Xem trước mẫu"""
        self.ensure_one()
        return {
            'name': f'Xem trước: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'mau.van.ban',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'preview_mode': True}
        }
    
    def action_duplicate(self):
        """Nhân bản mẫu"""
        self.ensure_one()
        new_mau = self.copy({
            'name': f'{self.name} (Copy)',
            'ma_mau': f'{self.ma_mau}_copy',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mau.van.ban',
            'view_mode': 'form',
            'res_id': new_mau.id,
            'target': 'current',
        }
    
    def render_template(self, data):
        """Render mẫu với dữ liệu"""
        self.ensure_one()
        if self.noi_dung_html:
            template = Template(self.noi_dung_html)
            return template.render(**data)
        return ''
    
    @api.model
    def apply_template(self, template_id, record_id, model_name):
        """Áp dụng mẫu cho bản ghi"""
        template = self.browse(template_id)
        record = self.env[model_name].browse(record_id)
        
        # Prepare data from record
        data = {}
        if hasattr(record, 'khach_hang_id'):
            data['khach_hang'] = record.khach_hang_id.name
            data['dia_chi_khach_hang'] = record.khach_hang_id.dia_chi
            data['dien_thoai_khach_hang'] = record.khach_hang_id.dien_thoai
        
        if hasattr(record, 'so_hop_dong'):
            data['so_hop_dong'] = record.so_hop_dong
        
        if hasattr(record, 'ngay_ky'):
            data['ngay_ky'] = record.ngay_ky.strftime('%d/%m/%Y') if record.ngay_ky else ''
        
        if hasattr(record, 'gia_tri'):
            data['gia_tri'] = f'{record.gia_tri:,.0f} VNĐ'
        
        # Render template
        rendered_content = template.render_template(data)
        
        # Update record
        if hasattr(record, 'noi_dung'):
            record.noi_dung = rendered_content
        
        # Update usage statistics
        template.write({
            'so_lan_su_dung': template.so_lan_su_dung + 1,
            'lan_su_dung_gan_nhat': fields.Datetime.now()
        })
        
        return rendered_content
