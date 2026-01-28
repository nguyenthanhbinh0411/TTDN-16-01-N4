from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'chuc_vu_cap_do asc, ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    user_id = fields.Many2one('res.users', string="User liên kết", help="Liên kết user Odoo để giao activity")
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    so_nguoi_bang_tuoi = fields.Integer(
        "Số người bằng tuổi",
        compute="_compute_so_nguoi_bang_tuoi",
        store=True,
    )
    luong_co_ban = fields.Float("Lương cơ bản")
    don_vi_hien_tai = fields.Many2one("don_vi", string="Đơn vị hiện tại", compute="_compute_don_vi_hien_tai", store=True)
    chuc_vu_cap_do = fields.Integer(string='Cấp độ chức vụ', compute='_compute_chuc_vu_cap_do', store=True)
    chuc_vu_hien_tai = fields.Many2one("chuc_vu", string="Chức vụ hiện tại", compute="_compute_chuc_vu_hien_tai", store=True)
    
    def action_open_van_ban_di_xu_ly(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Văn bản đi xử lý",
            "res_model": "van_ban_di",
            "view_mode": "tree,form",
            "domain": [("can_bo_xu_ly_id", "=", self.id)],
        }
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if not record.tuoi:
                record.so_nguoi_bang_tuoi = 0
                continue

            record_id = record.id if isinstance(record.id, int) else 0
            domain = [("tuoi", "=", record.tuoi)]
            if record_id:
                domain.append(("id", "!=", record_id))
            record.so_nguoi_bang_tuoi = self.env["nhan_vien"].search_count(domain)
    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
    
    
    
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split()])
                record.ma_dinh_danh = record.ten.lower() + chu_cai_dau
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")

    @api.depends('lich_su_cong_tac_ids.loai_chuc_vu', 'lich_su_cong_tac_ids.don_vi_id')
    def _compute_don_vi_hien_tai(self):
        for record in self:
            lich_su_chinh = record.lich_su_cong_tac_ids.filtered(lambda l: l.loai_chuc_vu == "Chính")
            if lich_su_chinh:
                record.don_vi_hien_tai = lich_su_chinh[0].don_vi_id
            else:
                record.don_vi_hien_tai = False

    @api.depends('lich_su_cong_tac_ids.loai_chuc_vu', 'lich_su_cong_tac_ids.chuc_vu_id')
    def _compute_chuc_vu_hien_tai(self):
        for record in self:
            lich_su_chinh = record.lich_su_cong_tac_ids.filtered(lambda l: l.loai_chuc_vu == "Chính")
            if lich_su_chinh:
                record.chuc_vu_hien_tai = lich_su_chinh[0].chuc_vu_id
            else:
                record.chuc_vu_hien_tai = False

    @api.depends('chuc_vu_hien_tai.cap_do')
    def _compute_chuc_vu_cap_do(self):
        for record in self:
            record.chuc_vu_cap_do = record.chuc_vu_hien_tai.cap_do if record.chuc_vu_hien_tai else 9999

    @api.model_create_multi
    def create(self, vals_list):
        records = super(NhanVien, self).create(vals_list)
        # Trigger sync sau khi tạo (tạm tắt để tránh lỗi runtime)
        return records

    def write(self, vals):
        result = super(NhanVien, self).write(vals)
        # Trigger sync sau khi update (tạm tắt để tránh lỗi runtime)
        return result

    def _sync_nhan_su_data(self):
        """Hook đồng bộ dữ liệu nhân sự. Hiện tại để no-op để tránh lỗi thiếu method."""
        return True
