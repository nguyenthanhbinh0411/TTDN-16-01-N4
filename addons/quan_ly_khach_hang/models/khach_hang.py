# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class KhachHang(models.Model):
    _name = 'khach_hang'
    _description = 'Quản lý thông tin khách hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_khach_hang'
    _order = 'ten_khach_hang asc'

    # Thông tin cơ bản
    ma_khach_hang = fields.Char("Mã khách hàng", required=True, copy=False, default=lambda self: _('New'))
    ten_khach_hang = fields.Char("Tên khách hàng", required=True)
    loai_khach_hang = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('doanh_nghiep', 'Doanh nghiệp'),
    ], string="Loại khách hàng", default='ca_nhan', required=True)
    
    # Thông tin liên hệ
    dia_chi = fields.Text("Địa chỉ")
    dien_thoai = fields.Char("Điện thoại")
    email = fields.Char("Email")
    website = fields.Char("Website")
    
    # Thông tin doanh nghiệp (nếu là doanh nghiệp)
    ma_so_thue = fields.Char("Mã số thuế")
    nguoi_dai_dien = fields.Char("Người đại diện")
    chuc_vu_dai_dien = fields.Char("Chức vụ người đại diện")
    
    # Thông tin cá nhân (nếu là cá nhân)
    so_cmnd_cccd = fields.Char("Số CMND/CCCD")
    ngay_sinh = fields.Date("Ngày sinh")
    gioi_tinh = fields.Selection([
        ('nam', 'Nam'),
        ('nu', 'Nữ'),
        ('khac', 'Khác'),
    ], string="Giới tính")
    
    # Nhân viên phụ trách (liên kết với nhan_su)
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    
    # Quan hệ với hồ sơ số hóa
    hop_dong_ids = fields.One2many('hop_dong', 'khach_hang_id', string="Hợp đồng")
    bao_gia_ids = fields.One2many('bao_gia', 'khach_hang_id', string="Báo giá")
    tai_lieu_ids = fields.One2many('tai_lieu', 'khach_hang_id', string="Tài liệu")
    
    # Quan hệ mới
    co_hoi_ids = fields.One2many('co_hoi_ban_hang', 'khach_hang_id', string="Cơ hội bán hàng")
    don_hang_ids = fields.One2many('don_hang', 'khach_hang_id', string="Đơn hàng")
    hoa_don_ids = fields.One2many('hoa_don', 'khach_hang_id', string="Hóa đơn")
    lich_su_tuong_tac_ids = fields.One2many('lich_su_tuong_tac', 'khach_hang_id', string="Lịch sử tương tác")
    khieu_nai_ids = fields.One2many('khieu_nai_phan_hoi', 'khach_hang_id', string="Khiếu nại")
    chuong_trinh_loyalty_id = fields.Many2one('chuong_trinh_khach_hang_than_thiet', string="Chương trình thân thiết")
    
    # Đếm số lượng
    hop_dong_count = fields.Integer(compute="_compute_counts", string="Số hợp đồng")
    bao_gia_count = fields.Integer(compute="_compute_counts", string="Số báo giá")
    tai_lieu_count = fields.Integer(compute="_compute_counts", string="Số tài liệu")
    co_hoi_count = fields.Integer(compute="_compute_counts", string="Số cơ hội")
    don_hang_count = fields.Integer(compute="_compute_counts", string="Số đơn hàng")
    hoa_don_count = fields.Integer(compute="_compute_counts", string="Số hóa đơn")
    tuong_tac_count = fields.Integer(compute="_compute_counts", string="Số tương tác")
    khieu_nai_count = fields.Integer(compute="_compute_counts", string="Số khiếu nại")
    
    # PHÂN TẦNG KHÁCH HÀNG
    phan_tang = fields.Selection([
        ('dong', 'Đồng (< 50tr/năm)'),
        ('bac', 'Bạc (50-100tr/năm)'),
        ('vang', 'Vàng (100-500tr/năm)'),
        ('kim_cuong', 'Kim cương (> 500tr/năm)'),
    ], string="Phân tầng", compute='_compute_phan_tang', store=True, tracking=True)
    
    doanh_thu_12_thang = fields.Float("Doanh thu 12 tháng", compute='_compute_doanh_thu_12_thang', store=True)
    
    # ĐIỂM TÍN NHIỆM (Credit Score)
    diem_tin_nhiem = fields.Float("Điểm tín nhiệm", compute='_compute_diem_tin_nhiem', store=True, help="Điểm từ 0-100")
    so_lan_thanh_toan_dung_han = fields.Integer("Số lần thanh toán đúng hạn", compute='_compute_tin_nhiem_metrics', store=True)
    so_lan_qua_han = fields.Integer("Số lần quá hạn", compute='_compute_tin_nhiem_metrics', store=True)
    so_lan_tre_han = fields.Integer("Số lần trễ hạn", compute='_compute_tin_nhiem_metrics', store=True)
    ty_le_thanh_toan_dung_han = fields.Float("Tỷ lệ thanh toán đúng hạn", compute='_compute_tin_nhiem_metrics', store=True)
    gia_tri_trung_binh_don_hang = fields.Float("Giá trị TB đơn hàng", compute='_compute_tin_nhiem_metrics', store=True)
    canh_bao_rui_ro = fields.Boolean("Cảnh báo rủi ro", compute='_compute_diem_tin_nhiem', store=True)
    
    # VÒNG ĐỜI KHÁCH HÀNG (Customer Lifecycle)
    ngay_mua_dau_tien = fields.Date("Ngày mua đầu tiên", compute='_compute_lifecycle', store=True)
    ngay_mua_gan_nhat = fields.Date("Ngày mua gần nhất", compute='_compute_lifecycle', store=True)
    tan_suat_mua = fields.Float("Tần suất mua (tháng)", compute='_compute_rfm', store=True, help="Số tháng giữa các lần mua")
    recency = fields.Integer("Recency (ngày)", compute='_compute_rfm', store=True, help="Số ngày kể từ lần mua gần nhất")
    frequency = fields.Integer("Frequency", compute='_compute_rfm', store=True, help="Tổng số lần mua")
    monetary = fields.Float("Monetary", compute='_compute_rfm', store=True, help="Tổng giá trị đã mua")
    gia_tri_tron_doi = fields.Float("LTV - Giá trị trọn đời", compute='_compute_ltv', store=True)
    
    trang_thai_vong_doi = fields.Selection([
        ('active', 'Active - Đang hoạt động'),
        ('inactive', 'Inactive - Không hoạt động'),
        ('churn', 'Churn - Rời bỏ'),
    ], string="Trạng thái vòng đời", compute='_compute_lifecycle', store=True)
    
    # CÔNG NỢ
    tong_no = fields.Float("Tổng công nợ", compute='_compute_cong_no', store=True)
    no_qua_han = fields.Float("Nợ quá hạn", compute='_compute_cong_no', store=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('tiem_nang', 'Tiềm năng'),
        ('dang_hop_tac', 'Đang hợp tác'),
        ('tam_dung', 'Tạm dừng'),
        ('ngung_hop_tac', 'Ngừng hợp tác'),
    ], string="Trạng thái", default='moi')
    
    ghi_chu = fields.Text("Ghi chú")
    anh = fields.Binary("Ảnh/Logo")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'ma_khach_hang' in fields_list and (not res.get('ma_khach_hang') or res.get('ma_khach_hang') == _('New')):
            res['ma_khach_hang'] = self.env['ir.sequence'].next_by_code('khach_hang') or _('New')
        return res

    @api.model
    def create(self, vals):
        if not vals.get('ma_khach_hang') or vals.get('ma_khach_hang') == _('New'):
            vals['ma_khach_hang'] = self.env['ir.sequence'].next_by_code('khach_hang') or _('New')
        return super().create(vals)
    
    @api.depends('hop_dong_ids', 'bao_gia_ids', 'tai_lieu_ids', 'co_hoi_ids', 'don_hang_ids', 'hoa_don_ids', 'lich_su_tuong_tac_ids', 'khieu_nai_ids')
    def _compute_counts(self):
        for record in self:
            record.hop_dong_count = len(record.hop_dong_ids)
            record.bao_gia_count = len(record.bao_gia_ids)
            record.tai_lieu_count = len(record.tai_lieu_ids)
            record.co_hoi_count = len(record.co_hoi_ids)
            record.don_hang_count = len(record.don_hang_ids)
            record.hoa_don_count = len(record.hoa_don_ids)
            record.tuong_tac_count = len(record.lich_su_tuong_tac_ids)
            record.khieu_nai_count = len(record.khieu_nai_ids)
    
    @api.depends('hoa_don_ids', 'hoa_don_ids.tong_thanh_toan', 'hoa_don_ids.trang_thai', 'hoa_don_ids.ngay_xuat')
    def _compute_doanh_thu_12_thang(self):
        """Tính tổng doanh thu 12 tháng gần nhất"""
        for record in self:
            twelve_months_ago = date.today() - relativedelta(months=12)
            hoa_dons = record.hoa_don_ids.filtered(
                lambda h: h.trang_thai == 'da_thanh_toan' and h.ngay_xuat >= twelve_months_ago
            )
            record.doanh_thu_12_thang = sum(hoa_dons.mapped('tong_thanh_toan'))
    
    @api.depends('doanh_thu_12_thang')
    def _compute_phan_tang(self):
        """Tự động phân tầng dựa trên doanh thu"""
        for record in self:
            dt = record.doanh_thu_12_thang
            if dt >= 500000000:  # 500 triệu
                record.phan_tang = 'kim_cuong'
            elif dt >= 100000000:  # 100 triệu
                record.phan_tang = 'vang'
            elif dt >= 50000000:  # 50 triệu
                record.phan_tang = 'bac'
            else:
                record.phan_tang = 'dong'
    
    @api.depends('hoa_don_ids', 'hoa_don_ids.trang_thai', 'hoa_don_ids.han_thanh_toan', 'hoa_don_ids.thanh_toan_ids')
    def _compute_tin_nhiem_metrics(self):
        """Tính các chỉ số tín nhiệm"""
        for record in self:
            hoa_dons = record.hoa_don_ids.filtered(lambda h: h.trang_thai == 'da_thanh_toan')
            
            # Đếm số lần thanh toán đúng hạn vs quá hạn
            dung_han = 0
            qua_han = 0
            for hd in hoa_dons:
                if hd.thanh_toan_ids:
                    ngay_tt_thuc_te = max(hd.thanh_toan_ids.mapped('ngay_thanh_toan'))
                    if ngay_tt_thuc_te <= hd.han_thanh_toan:
                        dung_han += 1
                    else:
                        qua_han += 1
            
            record.so_lan_thanh_toan_dung_han = dung_han
            record.so_lan_qua_han = qua_han
            record.so_lan_tre_han = qua_han  # Alias cho so_lan_qua_han
            
            # Tỷ lệ thanh toán đúng hạn
            total_payments = dung_han + qua_han
            if total_payments > 0:
                record.ty_le_thanh_toan_dung_han = (dung_han / total_payments) * 100
            else:
                record.ty_le_thanh_toan_dung_han = 0
            
            # Giá trị trung bình đơn hàng
            don_hangs = record.don_hang_ids.filtered(lambda d: d.trang_thai == 'hoan_thanh')
            if don_hangs:
                record.gia_tri_trung_binh_don_hang = sum(don_hangs.mapped('tong_gia_tri')) / len(don_hangs)
            else:
                record.gia_tri_trung_binh_don_hang = 0
    
    @api.depends('so_lan_thanh_toan_dung_han', 'so_lan_qua_han', 'doanh_thu_12_thang', 'gia_tri_trung_binh_don_hang')
    def _compute_diem_tin_nhiem(self):
        """Tính điểm tín nhiệm (0-100)"""
        for record in self:
            diem = 50  # Điểm cơ bản
            
            # +30 điểm nếu thanh toán đúng hạn tốt
            total_payments = record.so_lan_thanh_toan_dung_han + record.so_lan_qua_han
            if total_payments > 0:
                ty_le_dung_han = record.so_lan_thanh_toan_dung_han / total_payments
                diem += ty_le_dung_han * 30
            
            # +10 điểm nếu doanh thu cao
            if record.doanh_thu_12_thang >= 100000000:
                diem += 10
            elif record.doanh_thu_12_thang >= 50000000:
                diem += 5
            
            # +10 điểm nếu giá trị đơn hàng TB cao
            if record.gia_tri_trung_binh_don_hang >= 50000000:
                diem += 10
            elif record.gia_tri_trung_binh_don_hang >= 20000000:
                diem += 5
            
            # Trừ điểm nếu quá hạn nhiều
            diem -= record.so_lan_qua_han * 5
            
            record.diem_tin_nhiem = max(0, min(100, diem))
            record.canh_bao_rui_ro = record.diem_tin_nhiem < 40
    
    @api.depends('don_hang_ids', 'don_hang_ids.ngay_dat', 'don_hang_ids.trang_thai')
    def _compute_lifecycle(self):
        """Tính vòng đời khách hàng"""
        for record in self:
            don_hangs = record.don_hang_ids.filtered(lambda d: d.trang_thai == 'hoan_thanh').sorted('ngay_dat')
            
            if don_hangs:
                record.ngay_mua_dau_tien = don_hangs[0].ngay_dat
                record.ngay_mua_gan_nhat = don_hangs[-1].ngay_dat
                
                # Xác định trạng thái vòng đời
                days_since_last = (date.today() - don_hangs[-1].ngay_dat).days
                if days_since_last <= 90:
                    record.trang_thai_vong_doi = 'active'
                elif days_since_last <= 180:
                    record.trang_thai_vong_doi = 'inactive'
                else:
                    record.trang_thai_vong_doi = 'churn'
            else:
                record.ngay_mua_dau_tien = False
                record.ngay_mua_gan_nhat = False
                record.trang_thai_vong_doi = 'inactive'
    
    @api.depends('don_hang_ids', 'don_hang_ids.trang_thai', 'don_hang_ids.ngay_dat', 'don_hang_ids.tong_gia_tri')
    def _compute_rfm(self):
        """Tính RFM (Recency, Frequency, Monetary)"""
        for record in self:
            don_hangs = record.don_hang_ids.filtered(lambda d: d.trang_thai == 'hoan_thanh').sorted('ngay_dat')
            
            if don_hangs:
                # Recency: Số ngày kể từ lần mua gần nhất
                record.recency = (date.today() - don_hangs[-1].ngay_dat).days
                
                # Frequency: Tổng số lần mua
                record.frequency = len(don_hangs)
                
                # Monetary: Tổng giá trị
                record.monetary = sum(don_hangs.mapped('tong_gia_tri'))
                
                # Tần suất mua (trung bình bao nhiêu tháng mua 1 lần)
                if len(don_hangs) > 1:
                    total_days = (don_hangs[-1].ngay_dat - don_hangs[0].ngay_dat).days
                    record.tan_suat_mua = total_days / (len(don_hangs) - 1) / 30
                else:
                    record.tan_suat_mua = 0
            else:
                record.recency = 9999
                record.frequency = 0
                record.monetary = 0
                record.tan_suat_mua = 0
    
    @api.depends('monetary', 'frequency', 'ngay_mua_dau_tien')
    def _compute_ltv(self):
        """Tính LTV (Customer Lifetime Value)"""
        for record in self:
            if record.frequency > 0 and record.ngay_mua_dau_tien:
                # LTV đơn giản = Giá trị TB đơn hàng * Frequency * Tuổi khách hàng (năm)
                tuoi_kh_nam = (date.today() - record.ngay_mua_dau_tien).days / 365
                if tuoi_kh_nam > 0:
                    avg_order = record.monetary / record.frequency
                    record.gia_tri_tron_doi = avg_order * record.frequency / tuoi_kh_nam * 3  # Dự báo 3 năm
                else:
                    record.gia_tri_tron_doi = record.monetary
            else:
                record.gia_tri_tron_doi = 0
    
    @api.depends('hoa_don_ids.con_no', 'hoa_don_ids.han_thanh_toan')
    def _compute_cong_no(self):
        """Tính tổng công nợ từ hóa đơn"""
        for record in self:
            total_no = 0
            qua_han = 0
            for hoa_don in record.hoa_don_ids:
                if hoa_don.con_no > 0:
                    total_no += hoa_don.con_no
                    if hoa_don.han_thanh_toan and hoa_don.han_thanh_toan < date.today():
                        qua_han += hoa_don.con_no
            record.tong_no = total_no
            record.no_qua_han = qua_han
    
    def action_view_hop_dong(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hợp đồng',
            'res_model': 'hop_dong',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_bao_gia(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Báo giá',
            'res_model': 'bao_gia',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_tai_lieu(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tài liệu',
            'res_model': 'tai_lieu',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_co_hoi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cơ hội bán hàng',
            'res_model': 'co_hoi_ban_hang',
            'view_mode': 'kanban,tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_don_hang(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đơn hàng',
            'res_model': 'don_hang',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_hoa_don(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hóa đơn',
            'res_model': 'hoa_don',
            'view_mode': 'tree,form',
            'domain': [('khach_hang_id', '=', self.id)],
            'context': {'default_khach_hang_id': self.id}
        }
    
    def action_view_cong_no(self):
        self.ensure_one()
        cong_no = self.env['cong_no_khach_hang'].search([('khach_hang_id', '=', self.id)], limit=1)
        if cong_no:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Công nợ',
                'res_model': 'cong_no_khach_hang',
                'view_mode': 'form',
                'res_id': cong_no.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Công nợ',
                'res_model': 'cong_no_khach_hang',
                'view_mode': 'tree,form',
                'domain': [('khach_hang_id', '=', self.id)],
            }

    
    _sql_constraints = [
        ('ma_khach_hang_unique', 'unique(ma_khach_hang)', 'Mã khách hàng phải là duy nhất!')
    ]
