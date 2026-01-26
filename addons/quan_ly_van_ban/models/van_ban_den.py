# -*- coding: utf-8 -*-
from odoo import models, fields, api

class VanBanDen(models.Model):
    _name = 'van_ban_den'
    _description = 'Quản lý văn bản đến'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'so_ky_hieu'
    _order = 'ngay_den desc'
    
    # Thông tin cơ bản
    so_ky_hieu = fields.Char("Số/Ký hiệu", required=True, copy=False)
    ngay_den = fields.Date("Ngày đến", required=True, default=fields.Date.today)
    ngay_van_ban = fields.Date("Ngày văn bản", required=True)
    noi_ban_hanh = fields.Char("Nơi ban hành", required=True)
    kh_dien_thoai = fields.Char("Điện thoại KH")
    kh_email = fields.Char("Email KH")
    nguoi_ky = fields.Char("Người ký")
    trich_yeu = fields.Text("Trích yếu", required=True)

    # Liên kết khách hàng
    khach_hang_id = fields.Many2one(
        'khach_hang',
        string="Khách hàng",
        ondelete='set null',
        tracking=True,
    )
    
    # Phân loại
    loai_van_ban_id = fields.Many2one('loai_van_ban', string="Loại văn bản", required=True, ondelete='restrict')
    do_khan = fields.Selection([
        ('thuong', 'Thường'),
        ('khan', 'Khẩn'),
        ('hoa_toc', 'Hỏa tốc'),
        ('thuong_khat', 'Thượng khẩn')
    ], string="Độ khẩn", default='thuong')
    do_mat = fields.Selection([
        ('binh_thuong', 'Bình thường'),
        ('mat', 'Mật'),
        ('toi_mat', 'Tối mật')
    ], string="Độ mật", default='binh_thuong')
    
    # Xử lý
    nguoi_xu_ly_id = fields.Many2one('nhan_vien', string="Người xử lý", ondelete='set null', tracking=True)
    han_xu_ly = fields.Date("Hạn xử lý", tracking=True)
    da_ky_duyet = fields.Boolean("Đã ký/xác nhận", tracking=True)
    ngay_ky_duyet = fields.Date("Ngày ký/xác nhận", tracking=True)
    trang_thai = fields.Selection([
        ('moi', 'Mới'),
        ('dang_xu_ly', 'Đang xử lý'),
        ('qua_han', 'Quá hạn'),
        ('da_xu_ly', 'Đã xử lý'),
        ('chuyen_tiep', 'Chuyển tiếp')
    ], string="Trạng thái", default='moi', tracking=True)
    
    # File đính kèm
    file_dinh_kem = fields.Binary("File đính kèm")
    ten_file = fields.Char("Tên file")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    lan_dau_xem = fields.Boolean(string="Đã xem lần đầu", default=False)
    
    # Liên kết với hợp đồng (nếu có)
    hop_dong_id = fields.Many2one('hop_dong', string="Hợp đồng liên quan", ondelete='set null')
    bao_gia_id = fields.Many2one('bao_gia', string="Báo giá liên quan", ondelete='set null')
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng liên quan", ondelete='set null')
    nguoi_tao_id = fields.Many2one('res.users', string="Người tạo", default=lambda self: self.env.user, readonly=True)
    ngay_tao = fields.Datetime("Ngày tạo", default=fields.Datetime.now, readonly=True)
    
    _sql_constraints = [
        ('so_ky_hieu_unique', 'unique(so_ky_hieu)', 'Số/Ký hiệu văn bản đã tồn tại!')
    ]

    @api.onchange('*')
    def _clean_unknown_m2o_global(self):
        """Dọn mọi Many2one _unknown trước khi Odoo diff snapshot."""
        for fname, field in self._fields.items():
            if field.type == 'many2one':
                val = self[fname]
                if val and not getattr(val, 'id', False):
                    self[fname] = False

    @api.onchange('loai_van_ban_id', 'khach_hang_id', 'nguoi_xu_ly_id', 'hop_dong_id', 
                  'bao_gia_id', 'nguoi_tao_id')
    def _onchange_clean_unknown_m2o(self):
        """Clean _unknown Many2one values ngay khi bất kỳ Many2one field thay đổi."""
        for fname in ['loai_van_ban_id', 'khach_hang_id', 'nguoi_xu_ly_id', 'hop_dong_id',
                      'bao_gia_id', 'nguoi_tao_id']:
            val = self[fname]
            if val and not getattr(val, 'id', False):
                self[fname] = False

    @api.onchange('loai_van_ban_id')
    def _onchange_loai_van_ban(self):
        """Tự động gợi ý số ký hiệu dựa trên loại văn bản"""
        if self.loai_van_ban_id and not getattr(self.loai_van_ban_id, 'id', False):
            self.loai_van_ban_id = False
            return

        if self.loai_van_ban_id and not self.so_ky_hieu:
            # Đếm số văn bản cùng loại trong năm
            count = self.search_count([
                ('loai_van_ban_id', '=', self.loai_van_ban_id.id),
                ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
            ]) + 1
            self.so_ky_hieu = f"{self.loai_van_ban_id.ma_loai}/{count:04d}/{fields.Date.today().year}"

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang(self):
        """Điền sẵn thông tin liên hệ từ khách hàng."""

        if self.khach_hang_id:
            self.noi_ban_hanh = self.khach_hang_id.ten_khach_hang
            self.kh_dien_thoai = self.khach_hang_id.dien_thoai
            self.kh_email = self.khach_hang_id.email
    
    def action_mark_as_processing(self):
        for record in self:
            if not record.lan_dau_xem:
                record.write({'lan_dau_xem': True, 'trang_thai': 'dang_xu_ly'})
    
    def action_chuyen_xu_ly(self):
        """Chuyển văn bản đến sang trạng thái đang xử lý"""
        self.ensure_one()
        if not self.nguoi_xu_ly_id:
            raise models.ValidationError("Vui lòng chọn người xử lý trước khi chuyển xử lý!")
        
        self.write({
            'trang_thai': 'dang_xu_ly',
            'lan_dau_xem': True,
        })
        self.message_post(
            body=f"Văn bản đã được chuyển xử lý cho: {self.nguoi_xu_ly_id.ho_va_ten}"
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': 'Văn bản đã được chuyển xử lý',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_phe_duyet_van_ban_den(self):
        """Phê duyệt văn bản đến - phân công xử lý"""
        self.ensure_one()
        if not self.nguoi_xu_ly_id:
            raise models.ValidationError("Vui lòng chọn người xử lý trước khi phê duyệt!")
        if not self.han_xu_ly:
            raise models.ValidationError("Vui lòng chọn hạn xử lý trước khi phê duyệt!")
        
        self.write({
            'trang_thai': 'dang_xu_ly',
            'da_ky_duyet': True,
            'ngay_ky_duyet': fields.Date.today(),
            'lan_dau_xem': True,
        })
        self.message_post(
            body=f"Văn bản đã được phê duyệt và phân công cho: {self.nguoi_xu_ly_id.ho_va_ten}"
        )
        
        # Tạo activity giao việc ngay khi duyệt (đã có hạn xử lý)
        if self.nguoi_xu_ly_id.user_id:
            todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if todo_type:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_type.id,
                    'summary': f'Xử lý văn bản đến: {self.so_ky_hieu}',
                    'note': f"Trích yếu: {self.trich_yeu}",
                    'res_model_id': self.env['ir.model']._get('van_ban_den').id,
                    'res_id': self.id,
                    'user_id': self.nguoi_xu_ly_id.user_id.id,
                    'date_deadline': self.han_xu_ly,
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Văn bản đến',
            'res_model': 'van_ban_den',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'search_default_dang_xu_ly': 1},
        }
    
    def action_tu_choi_van_ban_den(self):
        """Từ chối văn bản đến"""
        self.ensure_one()
        self.write({
            'trang_thai': 'moi',
            'nguoi_xu_ly_id': False
        })
        self.message_post(body=f"Văn bản bị từ chối. Lý do: {self.ghi_chu or 'Không có lý do'}")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Đã từ chối',
                'message': 'Văn bản đã bị từ chối',
                'type': 'warning',
                'sticky': False,
            }
        }

    def action_hoan_thanh_van_ban_den(self):
        """Hoàn thành xử lý văn bản đến và đưa vào danh sách đã xử lý."""
        self.ensure_one()
        self.write({
            'trang_thai': 'da_xu_ly',
            'da_ky_duyet': True,
            'ngay_ky_duyet': fields.Date.today(),
        })
        self.message_post(body="Văn bản đã được xác nhận hoàn thành và chuyển sang danh sách đã xử lý")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Hoàn thành',
                'message': 'Văn bản đã được chuyển sang trạng thái Đã xử lý',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_xac_nhan_ky(self):
        """Đánh dấu đã ký/xác nhận (không tự động chuyển trạng thái)."""
        today = fields.Date.today()
        for record in self:
            vals = {'da_ky_duyet': True, 'ngay_ky_duyet': today}
            # Không tự động chuyển trạng thái, chỉ đánh dấu đã ký
            record.write(vals)

    def _create_activity(self):
        """Tạo nhắc việc theo hạn xử lý."""
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get('van_ban_den').id
        for record in self:
            if not todo_type or not record.han_xu_ly:
                continue
            user_to_assign = record.nguoi_xu_ly_id.user_id or self.env.user
            self.env['mail.activity'].create({
                'activity_type_id': todo_type.id,
                'summary': 'Xử lý văn bản đến',
                'note': f"{record.so_ky_hieu} - {record.trich_yeu}",
                'res_model_id': model_id,
                'res_id': record.id,
                'user_id': user_to_assign.id,
                'date_deadline': record.han_xu_ly,
            })

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._create_activity()
        return record

    @api.model
    def _cron_update_progress(self):
        """Cập nhật trạng thái theo hạn và tiến độ activity.
        - Chỉ cảnh báo quá hạn, không tự động chuyển trạng thái.
        """
        today = fields.Date.today()
        records = self.search([('trang_thai', 'not in', ['da_xu_ly', 'qua_han'])])
        for record in records:
            active_activities = record.activity_ids.filtered(lambda a: a.active)
            # Chỉ cảnh báo quá hạn, không tự động chuyển trạng thái
            if record.han_xu_ly and record.han_xu_ly < today and record.trang_thai != 'qua_han':
                record.write({'trang_thai': 'qua_han'})
                record.message_post(body="Cảnh báo: Văn bản đến quá hạn xử lý")


