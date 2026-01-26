# -*- coding: utf-8 -*-

from odoo import models, fields, api

class VanBanDashboard(models.TransientModel):
    _name = 'van.ban.dashboard'
    _description = 'Dashboard Văn bản'
    
    # KPI Fields
    van_ban_den_thang = fields.Integer('Văn bản đến tháng này', readonly=True)
    van_ban_di_thang = fields.Integer('Văn bản đi tháng này', readonly=True)
    van_ban_qua_han = fields.Integer('Văn bản quá hạn', readonly=True)
    cho_duyet_count = fields.Integer('Chờ duyệt', readonly=True)
    
    # Stats Fields
    ty_le_qua_han = fields.Float('Tỷ lệ quá hạn (%)', readonly=True)
    thoi_gian_xu_ly_tb = fields.Float('Thời gian xử lý TB (ngày)', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Load dashboard data khi mở form"""
        res = super(VanBanDashboard, self).default_get(fields_list)
        data = self._get_dashboard_data()
        res.update(data)
        return res
    
    def action_refresh(self):
        """Làm mới dữ liệu dashboard"""
        data = self._get_dashboard_data()
        self.write(data)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': 'Đã cập nhật dữ liệu dashboard',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _get_dashboard_data(self):
        """Lấy dữ liệu cho dashboard"""
        today = fields.Date.today()
        this_month_start = today.replace(day=1)
        
        # Văn bản đến/đi theo tháng
        van_ban_den_count = 0
        van_ban_di_count = 0
        van_ban_qua_han = 0
        hop_dong_cho_duyet = 0
        bao_gia_cho_duyet = 0
        avg_processing_time = 0
        
        try:
            if 'van.ban.den' in self.env:
                van_ban_den_count = self.env['van.ban.den'].search_count([
                    ('ngay_den', '>=', this_month_start)
                ])
                
                # Văn bản quá hạn
                van_ban_qua_han = self.env['van.ban.den'].search_count([
                    ('han_xu_ly', '<', today),
                    ('trang_thai', 'not in', ['hoan_thanh', 'huy'])
                ])
                
                # Thời gian xử lý trung bình
                van_ban_da_xu_ly = self.env['van.ban.den'].search([
                    ('trang_thai', '=', 'hoan_thanh'),
                    ('ngay_den', '>=', this_month_start)
                ])
                
                if van_ban_da_xu_ly:
                    total_time = sum([
                        (vb.ngay_hoan_thanh - vb.ngay_den).days
                        for vb in van_ban_da_xu_ly
                        if vb.ngay_hoan_thanh and vb.ngay_den
                    ])
                    avg_processing_time = total_time / len(van_ban_da_xu_ly) if total_time > 0 else 0
            
            if 'van_ban_di' in self.env:
                van_ban_di_count = self.env['van_ban_di'].search_count([
                    ('ngay_gui', '>=', this_month_start)
                ])
            
            # Văn bản chờ duyệt
            if 'hop.dong' in self.env:
                hop_dong_cho_duyet = self.env['hop.dong'].search_count([
                    ('trang_thai', '=', 'cho_duyet')
                ])
            
            if 'bao.gia' in self.env:
                bao_gia_cho_duyet = self.env['bao.gia'].search_count([
                    ('trang_thai', '=', 'cho_duyet')
                ])
        except Exception as e:
            # Nếu có lỗi, trả về giá trị mặc định
            pass
        
        return {
            'van_ban_den_thang': van_ban_den_count,
            'van_ban_di_thang': van_ban_di_count,
            'van_ban_qua_han': van_ban_qua_han,
            'cho_duyet_count': hop_dong_cho_duyet + bao_gia_cho_duyet,
            'ty_le_qua_han': (van_ban_qua_han / van_ban_den_count * 100) if van_ban_den_count > 0 else 0,
            'thoi_gian_xu_ly_tb': round(avg_processing_time, 1),
        }

