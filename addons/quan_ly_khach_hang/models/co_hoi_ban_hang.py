# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, timedelta

class CoHoiBanHang(models.Model):
    _name = 'co_hoi_ban_hang'
    _description = 'Quản lý cơ hội bán hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_co_hoi'
    _order = 'ngay_tao desc'

    # Thông tin cơ bản
    ma_co_hoi = fields.Char("Mã cơ hội", required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('co_hoi_ban_hang') or 'New')
    ten_co_hoi = fields.Char("Tên cơ hội", required=True, tracking=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, tracking=True, ondelete='cascade')
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách", required=True, tracking=True)
    
    # Nguồn cơ hội
    nguon_co_hoi = fields.Selection([
        ('website', 'Website'),
        ('dien_thoai', 'Điện thoại'),
        ('su_kien', 'Sự kiện'),
        ('gioi_thieu', 'Giới thiệu'),
        ('email', 'Email Marketing'),
        ('mang_xa_hoi', 'Mạng xã hội'),
        ('khac', 'Khác'),
    ], string="Nguồn cơ hội", default='website', required=True, tracking=True)
    
    # Giai đoạn
    giai_doan = fields.Selection([
        ('moi', 'Mới'),
        ('du_dieu_kien', 'Đủ điều kiện'),
        ('bao_gia', 'Đang báo giá'),
        ('dam_phan', 'Đàm phán'),
        ('thang', 'Thắng'),
        ('thua', 'Thua'),
    ], string="Giai đoạn", default='moi', required=True, tracking=True)
    
    # Tỷ lệ thành công
    ty_le_thanh_cong = fields.Float("Tỷ lệ thành công (%)", default=10.0, tracking=True, help="Xác suất chốt deal thành công")
    
    # Giá trị dự kiến
    gia_tri_du_kien = fields.Float("Giá trị dự kiến", tracking=True)
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    # Thời gian
    ngay_tao = fields.Date("Ngày tạo", default=fields.Date.today, required=True)
    ngay_du_kien_chot = fields.Date("Ngày dự kiến chốt", tracking=True)
    ngay_chot_thuc_te = fields.Date("Ngày chốt thực tế", tracking=True)
    
    # Lý do thất bại
    ly_do_that_bai = fields.Text("Lý do thất bại", tracking=True)
    
    # Liên kết
    bao_gia_ids = fields.One2many('bao_gia', 'co_hoi_id', string="Báo giá")
    bao_gia_count = fields.Integer(compute='_compute_bao_gia_count', string="Số báo giá")
    has_bao_gia_khach_dong_y = fields.Boolean(compute='_compute_bao_gia_trang_thai', string="Có báo giá khách đồng ý")
    has_bao_gia_khach_tu_choi = fields.Boolean(compute='_compute_bao_gia_trang_thai', string="Có báo giá khách từ chối")
    hop_dong_ids = fields.One2many('hop_dong', 'co_hoi_id', string="Hợp đồng")
    hop_dong_count = fields.Integer(compute='_compute_hop_dong_count', string="Số hợp đồng")
    has_hop_dong = fields.Boolean(compute='_compute_hop_dong_count', string="Có hợp đồng")
    don_hang_ids = fields.One2many('don_hang', 'co_hoi_id', string="Đơn hàng")
    don_hang_count = fields.Integer(compute='_compute_don_hang_count', string="Số đơn hàng")
    
    # Thông tin bổ sung
    mo_ta = fields.Text("Mô tả cơ hội")
    ghi_chu = fields.Text("Ghi chú")
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('mo', 'Đang mở'),
        ('thang', 'Đã thắng'),
        ('thua', 'Đã thua'),
    ], string="Trạng thái", default='mo', compute='_compute_trang_thai', store=True)
    
    _sql_constraints = [
        ('ma_co_hoi_unique', 'unique(ma_co_hoi)', 'Mã cơ hội phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_co_hoi', 'New') == 'New':
            vals['ma_co_hoi'] = self.env['ir.sequence'].next_by_code('co_hoi_ban_hang') or 'New'
        return super().create(vals)
    
    @api.depends('bao_gia_ids')
    def _compute_bao_gia_count(self):
        for record in self:
            record.bao_gia_count = len(record.bao_gia_ids)

    @api.depends('hop_dong_ids')
    def _compute_hop_dong_count(self):
        for record in self:
            record.hop_dong_count = len(record.hop_dong_ids)
            record.has_hop_dong = bool(record.hop_dong_ids)

    @api.depends('don_hang_ids')
    def _compute_don_hang_count(self):
        for record in self:
            record.don_hang_count = len(record.don_hang_ids)

    @api.depends('bao_gia_ids.trang_thai')
    def _compute_bao_gia_trang_thai(self):
        for record in self:
            statuses = set(record.bao_gia_ids.mapped('trang_thai'))
            record.has_bao_gia_khach_dong_y = 'khach_dong_y' in statuses
            record.has_bao_gia_khach_tu_choi = 'khach_tu_choi' in statuses
    
    @api.depends('giai_doan')
    def _compute_trang_thai(self):
        for record in self:
            if record.giai_doan == 'thang':
                record.trang_thai = 'thang'
            elif record.giai_doan == 'thua':
                record.trang_thai = 'thua'
            else:
                record.trang_thai = 'mo'
    
    @api.onchange('giai_doan')
    def _onchange_giai_doan(self):
        """Tự động cập nhật tỷ lệ thành công theo giai đoạn"""
        ty_le_map = {
            'moi': 10,
            'du_dieu_kien': 25,
            'bao_gia': 50,
            'dam_phan': 75,
            'thang': 100,
            'thua': 0,
        }
        if self.giai_doan in ty_le_map:
            self.ty_le_thanh_cong = ty_le_map[self.giai_doan]
        
        # Tự động tạo văn bản đến khi chuyển sang giai đoạn báo giá
        if self.giai_doan == 'bao_gia' and not hasattr(self, '_stage_change_processed'):
            self._create_van_ban_den_on_stage_change()
    
    @api.onchange('khach_hang_id')
    def _onchange_khach_hang_id(self):
        """Tự động gán nhân viên phụ trách từ khách hàng"""
        if self.khach_hang_id and self.khach_hang_id.nhan_vien_phu_trach_id:
            self.nhan_vien_phu_trach_id = self.khach_hang_id.nhan_vien_phu_trach_id
    
    def _create_van_ban_den_on_stage_change(self):
        """Tạo văn bản đến khi chuyển sang giai đoạn báo giá"""
        self.ensure_one()
        if self.env['van_ban_den'].search([('co_hoi_id', '=', self.id)], limit=1):
            return
        
        # Tạo loại văn bản nếu chưa có
        loai_vb = self.env['loai_van_ban'].search([('ma_loai', '=', 'BG')], limit=1)
        if not loai_vb:
            loai_vb = self.env['loai_van_ban'].create({
                'ma_loai': 'BG',
                'ten_loai': 'Báo giá',
                'mo_ta': 'Văn bản báo giá',
                'hoat_dong': True,
            })
        
        count = self.env['van_ban_den'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"BG/{count:04d}/{fields.Date.today().year}"
        
        van_ban = self.env['van_ban_den'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_den': fields.Date.today(),
            'ngay_van_ban': fields.Date.today(),
            'noi_ban_hanh': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': '',
            'trich_yeu': f"Báo giá cho cơ hội: {self.ten_co_hoi} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_xu_ly_id': self.nhan_vien_phu_trach_id.id if self.nhan_vien_phu_trach_id else False,
            'trang_thai': 'moi',
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'co_hoi_id': self.id,
            'han_xu_ly': fields.Date.today() + timedelta(days=3),
            'ghi_chu': f"Văn bản tạo tự động khi chuyển cơ hội {self.ma_co_hoi} sang giai đoạn báo giá",
        })
        
        # Tạo activity để tránh cronjob tự động chuyển sang "đã xử lý"
        van_ban._create_activity()
        
        # Đánh dấu đã xử lý để tránh tạo nhiều lần
        self._stage_change_processed = True
    
    def action_chuyen_giai_doan_tiep(self):
        """Chuyển sang giai đoạn tiếp theo"""
        giai_doan_map = {
            'moi': 'du_dieu_kien',
            'du_dieu_kien': 'bao_gia',
            'bao_gia': 'dam_phan',
        }
        for record in self:
            if record.giai_doan == 'bao_gia' and not record.bao_gia_ids:
                raise UserError("Cần có ít nhất một báo giá trước khi chuyển sang giai đoạn Đàm phán.")
            if record.giai_doan == 'dam_phan':
                if not record.hop_dong_ids:
                    raise UserError("Cần tạo hợp đồng trước khi đánh dấu thắng/thua.")
                raise UserError("Ở giai đoạn Đàm phán, hãy dùng nút Đánh dấu thắng/Đánh dấu thua.")
            if record.giai_doan in giai_doan_map:
                record.giai_doan = giai_doan_map[record.giai_doan]
    
    def action_danh_dau_thang(self):
        """Đánh dấu cơ hội thắng"""
        for record in self:
            if record.giai_doan == 'dam_phan' and not record.hop_dong_ids:
                raise UserError("Cần tạo hợp đồng trước khi đánh dấu thắng.")
            record.write({
                'giai_doan': 'thang',
                'ngay_chot_thuc_te': fields.Date.today(),
            })
            record._auto_create_don_hang_on_win()
    
    def action_danh_dau_thua(self):
        """Đánh dấu cơ hội thua"""
        for record in self:
            if record.giai_doan == 'dam_phan' and not record.hop_dong_ids:
                raise UserError("Cần tạo hợp đồng trước khi đánh dấu thua.")
            record.write({
                'giai_doan': 'thua',
                'ngay_chot_thuc_te': fields.Date.today(),
            })

    def write(self, vals):
        create_order_records = self.browse()
        if vals.get('giai_doan') == 'thang':
            for record in self:
                if record.giai_doan == 'dam_phan' and not record.hop_dong_ids:
                    raise UserError("Cần tạo hợp đồng trước khi đánh dấu thắng.")
            create_order_records = self.filtered(lambda r: r.giai_doan == 'dam_phan')

        result = super().write(vals)

        if vals.get('giai_doan') == 'thang' and create_order_records:
            create_order_records._auto_create_don_hang_on_win()

        return result
    
    @api.model
    def create(self, vals):
        """Tự sinh mã cơ hội khi tạo mới"""
        if vals.get('ma_co_hoi', 'New') == 'New':
            vals['ma_co_hoi'] = self.env['ir.sequence'].next_by_code('co_hoi_ban_hang') or 'New'
        return super(CoHoiBanHang, self).create(vals)
    
    def action_view_bao_gia(self):
        """Xem danh sách báo giá"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Báo giá',
            'res_model': 'bao_gia',
            'view_mode': 'tree,form',
            'domain': [('co_hoi_id', '=', self.id)],
            'context': {'default_co_hoi_id': self.id, 'default_khach_hang_id': self.khach_hang_id.id}
        }

    def action_open_bao_gia_form(self):
        """Mở popup tạo báo giá từ cơ hội bán hàng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo báo giá',
            'res_model': 'bao_gia',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_co_hoi_id': self.id,
                'default_khach_hang_id': self.khach_hang_id.id,
                'default_nhan_vien_lap_id': self.nhan_vien_phu_trach_id.id,
                'default_ten_bao_gia': self.ten_co_hoi,
                'default_tong_gia_tri': self.gia_tri_du_kien,
                'default_don_vi_tien': self.don_vi_tien,
                'open_in_popup': True,
            }
        }

    def action_view_hop_dong(self):
        """Xem danh sách hợp đồng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hợp đồng',
            'res_model': 'hop_dong',
            'view_mode': 'tree,form',
            'domain': [('co_hoi_id', '=', self.id)],
            'context': {
                'default_co_hoi_id': self.id,
                'default_khach_hang_id': self.khach_hang_id.id,
                'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
            }
        }

    def action_view_don_hang(self):
        """Xem danh sách đơn hàng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đơn hàng',
            'res_model': 'don_hang',
            'view_mode': 'tree,form',
            'domain': [('co_hoi_id', '=', self.id)],
            'context': {
                'default_co_hoi_id': self.id,
                'default_khach_hang_id': self.khach_hang_id.id,
                'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
            }
        }

    def action_create_hop_dong(self):
        """Tạo hợp đồng từ cơ hội bán hàng"""
        return self.action_open_hop_dong_form()

    def action_open_hop_dong_form(self):
        """Mở form tạo hợp đồng từ cơ hội bán hàng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo hợp đồng',
            'res_model': 'hop_dong',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_co_hoi_id': self.id,
                'default_khach_hang_id': self.khach_hang_id.id,
                'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
                'default_ten_hop_dong': self.ten_co_hoi,
                'default_gia_tri': self.gia_tri_du_kien,
                'default_don_vi_tien': self.don_vi_tien,
            }
        }

    def action_open_don_hang_form(self):
        """Mở form tạo đơn hàng từ cơ hội bán hàng (không đổi trạng thái cơ hội)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo đơn hàng',
            'res_model': 'don_hang',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_co_hoi_id': self.id,
                'default_khach_hang_id': self.khach_hang_id.id,
                'default_nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
                'default_ten_don_hang': f"Đơn hàng - {self.ten_co_hoi}",
                'default_don_vi_tien': self.don_vi_tien,
            }
        }

    def _auto_create_don_hang_on_win(self):
        """Tự động tạo đơn hàng khi cơ hội được đánh dấu thắng"""
        self.ensure_one()
        existing = self.env['don_hang'].search([('co_hoi_id', '=', self.id)], limit=1)
        if existing:
            return existing

        hop_dong = self.hop_dong_ids.sorted('id')[-1:] if self.hop_dong_ids else self.env['hop_dong']
        bao_gia = self.bao_gia_ids.sorted('id')[-1:] if self.bao_gia_ids else self.env['bao_gia']

        return self.env['don_hang'].create({
            'ten_don_hang': f"Đơn hàng - {self.ten_co_hoi}",
            'khach_hang_id': self.khach_hang_id.id,
            'nhan_vien_phu_trach_id': self.nhan_vien_phu_trach_id.id,
            'ngay_dat': fields.Date.today(),
            'don_vi_tien': self.don_vi_tien,
            'co_hoi_id': self.id,
            'hop_dong_id': hop_dong.id if hop_dong else False,
            'bao_gia_id': bao_gia.id if bao_gia else False,
        })
