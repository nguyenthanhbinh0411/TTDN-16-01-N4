# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

class VanBanDi(models.Model):
    _name = 'van_ban_di'
    _description = 'Quản lý văn bản đi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'so_ky_hieu'
    _order = 'ngay_van_ban desc'
    
    # Thông tin cơ bản
    so_ky_hieu = fields.Char("Số/Ký hiệu", required=True, copy=False)
    ngay_van_ban = fields.Date("Ngày văn bản", required=True, default=fields.Date.today)
    ngay_gui = fields.Date("Ngày gửi")
    noi_nhan = fields.Char("Nơi nhận", required=True)
    kh_dien_thoai = fields.Char("Điện thoại KH")
    kh_email = fields.Char("Email KH")
    nguoi_ky = fields.Char("Người ký", required=True)
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
    
    # Soạn thảo
    nguoi_soan_thao_id = fields.Many2one('nhan_vien', string="Người soạn thảo", ondelete='set null')
    don_vi_soan_thao_id = fields.Many2one('don_vi', string="Đơn vị soạn thảo", ondelete='set null')

    approver_tp_id = fields.Many2one('nhan_vien', string="Trưởng phòng duyệt", ondelete='set null')
    approver_gd_id = fields.Many2one('nhan_vien', string="Giám đốc duyệt", ondelete='set null')
    tp_da_duyet = fields.Boolean("TP đã duyệt", tracking=True)
    tp_ngay_duyet = fields.Date("Ngày duyệt TP", tracking=True)
    gd_da_duyet = fields.Boolean("GĐ đã duyệt", tracking=True)
    gd_ngay_duyet = fields.Date("Ngày duyệt GĐ", tracking=True)
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('du_thao', 'Dự thảo'),
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('da_gui', 'Đã gửi'),
        ('hoan_tat', 'Hoàn tất'),
        ('huy', 'Hủy')
    ], string="Trạng thái", default='du_thao', tracking=True)
    da_ky_duyet = fields.Boolean("Đã ký/duyệt", tracking=True)
    ngay_ky_duyet = fields.Date("Ngày ký/duyệt", tracking=True)
    
    # File đính kèm
    file_dinh_kem = fields.Binary("File đính kèm")
    ten_file = fields.Char("Tên file")
    
    # Mẫu văn bản
    mau_van_ban_id = fields.Many2one('mau.van.ban', string="Mẫu văn bản", help="Chọn mẫu văn bản để áp dụng nội dung")
    
    # Xác nhận ký điện tử (boolean để xác nhận đã ký)
    xac_nhan_chu_ky = fields.Boolean("Xác nhận chữ ký điện tử", help="Xác nhận phê duyệt bằng chữ ký điện tử")
    chu_ky_luu_id = fields.Many2one('chu.ky.dien.tu', string="Chữ ký đã lưu", help="Bản ghi chữ ký điện tử đã tạo")
    
    # Chữ ký mới: upload ảnh
    chu_ky_anh = fields.Binary("Ảnh chữ ký", help="Upload ảnh chữ ký từ máy")
    ten_chu_ky_anh = fields.Char("Tên file chữ ký")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    # Liên kết với hợp đồng (nếu có)
    hop_dong_id = fields.Many2one('hop_dong', string="Hợp đồng liên quan", ondelete='set null')
    van_ban_den_id = fields.Many2one(
        'van_ban_den',
        string="Văn bản đến cần trả lời",
        ondelete='set null',
        help="Chọn văn bản đến cần phản hồi để theo dõi liên kết hai chiều"
    )
    co_hoi_id = fields.Many2one(
        'co_hoi_ban_hang',
        string="Cơ hội bán hàng liên quan",
        ondelete='set null',
        help="Liên kết với cơ hội bán hàng để cập nhật trạng thái khi gửi văn bản"
    )
    nguoi_tao_id = fields.Many2one('res.users', string="Người tạo", default=lambda self: self.env.user, readonly=True)
    ngay_tao = fields.Datetime("Ngày tạo", default=fields.Datetime.now, readonly=True)
    approval_log_ids = fields.One2many(
        'van_ban_di_approval_log',
        'van_ban_di_id',
        string="Lịch sử duyệt",
        readonly=True,
    )
    
    _sql_constraints = [
        ('so_ky_hieu_unique', 'unique(so_ky_hieu)', 'Số/Ký hiệu văn bản đã tồn tại!')
    ]

    # --- Helpers to clean Many2one _unknown ---
    def _is_unknown(self, val):
        try:
            return getattr(val, '_name', '') == '_unknown' or val.__class__.__name__ == '_unknown'
        except Exception:
            return False

    def _clean_unknown_m2o_self(self):
        for rec in self:
            for fname, field in rec._fields.items():
                if field.type == 'many2one':
                    val = rec[fname]
                    if val and (rec._is_unknown(val) or not getattr(val, 'id', False)):
                        rec[fname] = False

    def _clean_unknown_in_values(self, values):
        if not values:
            return
        for k, v in list(values.items()):
            if isinstance(v, models.BaseModel):
                if self._is_unknown(v) or not getattr(v, 'id', False):
                    values[k] = False
            elif isinstance(v, dict):
                if v.get('_name') == '_unknown' or v.get('id') is None:
                    values[k] = False

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            self._clean_unknown_in_values(vals)
        records = super(VanBanDi, self).create(vals_list)
        records._clean_unknown_m2o_self()
        return records

    def write(self, vals):
        self._clean_unknown_in_values(vals)
        res = super(VanBanDi, self).write(vals)
        self._clean_unknown_m2o_self()
        return res

    def read(self, fields=None, load='_classic_read'):
        # Làm sạch trước khi đọc để tránh _unknown không có id
        recs = self.with_context(prefetch_fields=False)
        recs._clean_unknown_m2o_self()
        try:
            return super(VanBanDi, recs).read(fields=fields, load=load)
        except (AttributeError, ValueError):
            # Nếu vẫn còn _unknown hoặc lỗi singleton, dọn cache và thử lại
            recs.invalidate_cache()
            recs._clean_unknown_m2o_self()
            try:
                return super(VanBanDi, recs).read(fields=fields, load=load)
            except Exception:
                # Fallback: trả về dữ liệu an toàn, gán False cho Many2one lỗi
                result = []
                field_names = fields or list(recs._fields.keys())
                for rec in recs:
                    vals = {}
                    for name in field_names:
                        field = rec._fields.get(name)
                        if not field:
                            continue
                        try:
                            if field.type == 'many2one':
                                val = rec[name]
                                vals[name] = val.id if getattr(val, 'id', False) else False
                            else:
                                vals[name] = rec[name]
                        except Exception:
                            vals[name] = False
                    result.append(vals)
                return result

    def onchange(self, values, field_name, field_onchange):
        """Dọn _unknown Many2one trước và sau khi gọi super."""
        self._clean_unknown_m2o_self()
        self._clean_unknown_in_values(values)
        try:
            res = super(VanBanDi, self).onchange(values, field_name, field_onchange)
        except AttributeError:
            # Nếu snapshot chứa _unknown không có id, dọn và trả về trống để tránh lỗi RPC.
            self._clean_unknown_m2o_self()
            return {}
        if res and 'value' in res:
            self._clean_unknown_in_values(res['value'])
        return res

    @api.onchange('*')
    def _clean_unknown_m2o_global(self):
        """Dọn mọi Many2one _unknown trước khi Odoo diff snapshot."""
        for fname, field in self._fields.items():
            if field.type == 'many2one':
                val = self[fname]
                if val and not getattr(val, 'id', False):
                    self[fname] = False

    @api.onchange('loai_van_ban_id', 'khach_hang_id', 'nguoi_soan_thao_id', 'don_vi_soan_thao_id',
                  'approver_tp_id', 'approver_gd_id', 'hop_dong_id', 'nguoi_tao_id')
    def _onchange_clean_unknown_m2o(self):
        """Clean _unknown Many2one values ngay khi bất kỳ Many2one field thay đổi."""
        for fname in ['loai_van_ban_id', 'khach_hang_id', 'nguoi_soan_thao_id', 'don_vi_soan_thao_id',
                      'approver_tp_id', 'approver_gd_id', 'hop_dong_id', 'nguoi_tao_id']:
            val = self[fname]
            if val and not getattr(val, 'id', False):
                self[fname] = False
    
    @api.onchange('loai_van_ban_id')
    def _onchange_loai_van_ban(self):
        """Tự động gợi ý số ký hiệu dựa trên loại văn bản"""
        if self.loai_van_ban_id and not getattr(self.loai_van_ban_id, 'id', False):
            self.loai_van_ban_id = False
            return

        if not self.loai_van_ban_id or self.so_ky_hieu:
            return

        # Đếm số văn bản cùng loại trong năm
        count = self.search_count([
            ('loai_van_ban_id', '=', self.loai_van_ban_id.id),
            ('ngay_van_ban', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        self.so_ky_hieu = f"{self.loai_van_ban_id.ma_loai}/{count:04d}/{fields.Date.today().year}"

    @api.onchange('khach_hang_id')
    def _onchange_khach_hang(self):
        """Điền sẵn nơi nhận và thông tin liên hệ từ khách hàng."""
        if self.khach_hang_id and not getattr(self.khach_hang_id, 'id', False):
            self.khach_hang_id = False
            return

        if self.khach_hang_id:
            self.noi_nhan = self.khach_hang_id.ten_khach_hang
            self.kh_dien_thoai = self.khach_hang_id.dien_thoai
            self.kh_email = self.khach_hang_id.email
    
    @api.onchange('nguoi_soan_thao_id')
    def _onchange_nguoi_soan_thao(self):
        """Tự động gán đơn vị soạn thảo từ người soạn thảo"""
        if self.nguoi_soan_thao_id:
            self.don_vi_soan_thao_id = self.nguoi_soan_thao_id.don_vi_hien_tai
        else:
            self.don_vi_soan_thao_id = False
    
    @api.onchange('approver_tp_id')
    def _onchange_approver_tp(self):
        """Chỉ cho phép chọn trưởng phòng hoặc giám đốc, và set người ký"""
        if self.approver_tp_id:
            self.approver_gd_id = False
            self.nguoi_ky = self.approver_tp_id.ho_va_ten
        elif not self.approver_gd_id:
            self.nguoi_ky = False
    
    @api.onchange('approver_gd_id')
    def _onchange_approver_gd(self):
        """Chỉ cho phép chọn trưởng phòng hoặc giám đốc, và set người ký"""
        if self.approver_gd_id:
            self.approver_tp_id = False
            self.nguoi_ky = self.approver_gd_id.ho_va_ten
        elif not self.approver_tp_id:
            self.nguoi_ky = False
    
    def action_gui_duyet(self):
        """Gửi văn bản đi duyệt"""
        self.write({'trang_thai': 'cho_duyet'})
        self._create_approval_tasks()
    
    def action_phe_duyet_van_ban_di(self):
        """Phê duyệt văn bản đi - yêu cầu đã ký trước khi phê duyệt"""
        self.ensure_one()
        # Bắt buộc phải có chữ ký (đã ký hoặc đã lưu hoặc upload)
        if not (self.da_ky_duyet or self.chu_ky_luu_id or self.chu_ky_anh):
            raise models.ValidationError("Vui lòng upload chữ ký (PDF/ảnh) trước khi phê duyệt (bấm 'Ký').")

        today = fields.Date.today()
        user_nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1)

        # Nếu chưa có bản ghi chữ ký được lưu, tạo bản ghi từ chữ ký upload
        if not self.chu_ky_luu_id:
            chu_ky_image = False
            if self.chu_ky_anh:
                chu_ky_image = self.chu_ky_anh
            if chu_ky_image:
                chu_ky = self.env['chu.ky.dien.tu'].create_signature(
                    'van_ban_di', self.id, user_nhan_vien.id if user_nhan_vien else False,
                    document_content=(self.trich_yeu or self.so_ky_hieu), chu_ky_image=chu_ky_image
                )
                chu_ky.action_sign()
                self.chu_ky_luu_id = chu_ky.id
                self.da_ky_duyet = True
                self.ngay_ky_duyet = today

        # Chuyển trạng thái và thực hiện các hành động liên quan
        self.write({
            'trang_thai': 'da_gui',
        })

        # Cập nhật trạng thái văn bản đến nếu có liên kết
        if self.van_ban_den_id:
            self.van_ban_den_id.write({
                'trang_thai': 'da_xu_ly',
                'da_ky_duyet': True,
                'ngay_ky_duyet': today,
            })
            self.message_post(
                body=f"Đã cập nhật trạng thái văn bản đến '{self.van_ban_den_id.so_ky_hieu}' thành 'Đã xử lý'"
            )

        # Đề xuất cập nhật giai đoạn cơ hội bán hàng nếu có liên kết
        if self.co_hoi_id:
            self._propose_opportunity_stage_update()

        # Gửi email thông báo đến khách hàng
        self._send_notification_email()

        self.message_post(
            body=(f"Văn bản đã được phê duyệt (Đã ký: {self.chu_ky_luu_id and self.chu_ky_luu_id.name or 'chưa rõ'})")
        )
        self._log_approval(role='khac', action='approve', note=f"Đã duyệt")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Văn bản đi',
            'res_model': 'van_ban_di',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'search_default_da_gui': 1},
        }

    def action_ky_van_ban(self):
        """Hành động Ký: tạo bản ghi chữ ký từ file upload"""
        self.ensure_one()
        if self.chu_ky_luu_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Đã ký', 'message': 'Văn bản đã có chữ ký lưu', 'type': 'info'}
            }
        user_nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1)
        chu_ky_image = False
        if self.chu_ky_anh:
            chu_ky_image = self.chu_ky_anh
        if not chu_ky_image:
            raise models.ValidationError('Vui lòng upload chữ ký (PDF/ảnh) trước khi bấm Ký.')
        chu_ky = self.env['chu.ky.dien.tu'].create_signature(
            'van_ban_di', self.id, user_nhan_vien.id if user_nhan_vien else False,
            document_content=(self.trich_yeu or self.so_ky_hieu), chu_ky_image=chu_ky_image
        )
        chu_ky.action_sign()
        self.chu_ky_luu_id = chu_ky.id
        self.da_ky_duyet = True
        self.ngay_ky_duyet = fields.Date.today()
        self.message_post(body=f"Văn bản đã được ký: {chu_ky.name}")
        self._log_approval(role='khac', action='sign', note=f"Ký bằng ảnh: {chu_ky.name}")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Ký thành công', 'message': 'Chữ ký đã được lưu', 'type': 'success'}
        }

    def action_open_signature_wizard(self):
        """Mở wizard upload chữ ký trước khi xác nhận ký"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Upload chữ ký',
            'res_model': 'van.ban.di.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_van_ban_di_id': self.id,
            },
        }
    
    def action_tu_choi_van_ban_di(self):
        """Từ chối văn bản đi"""
        self.ensure_one()
        self.write({'trang_thai': 'du_thao'})
        self.message_post(body="Văn bản bị từ chối, chuyển về dự thảo để sửa lại")
        self._log_approval(role='khac', action='reject', note=self.ghi_chu or "Từ chối duyệt")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Đã từ chối',
                'message': 'Văn bản đã bị từ chối và chuyển về dự thảo',
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_duyet(self):
        """Duyệt văn bản đi"""
        today = fields.Date.today()
        self.write({'trang_thai': 'da_duyet', 'da_ky_duyet': True, 'ngay_ky_duyet': today})
        self._log_approval(role='khac')
        self._check_approval_complete()

    def action_ap_dung_mau(self):
        """Áp dụng mẫu văn bản"""
        self.ensure_one()
        if self.mau_van_ban_id and self.mau_van_ban_id.noi_dung_html:
            self.write({'trich_yeu': self.mau_van_ban_id.noi_dung_html})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thành công',
                    'message': 'Đã áp dụng mẫu văn bản vào nội dung trích yếu',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Lỗi',
                    'message': 'Vui lòng chọn mẫu văn bản có nội dung',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def action_tp_duyet(self):
        today = fields.Date.today()
        self.write({'tp_da_duyet': True, 'tp_ngay_duyet': today})
        self.message_post(body="Trưởng phòng đã duyệt văn bản")
        self._log_approval(role='tp')
        self._check_approval_complete()

    def action_gd_duyet(self):
        today = fields.Date.today()
        self.write({'gd_da_duyet': True, 'gd_ngay_duyet': today})
        self.message_post(body="Giám đốc đã duyệt văn bản")
        self._log_approval(role='gd')
        self._check_approval_complete()
    
    def action_gui_van_ban(self):
        """Đánh dấu văn bản đã được gửi"""
        today = fields.Date.today()
        self.write({
            'trang_thai': 'da_gui',
            'ngay_gui': today
        })
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get('khach_hang').id
        for record in self:
            kh = record.khach_hang_id
            if not kh:
                continue
            user_to_assign = kh.nhan_vien_phu_trach_id.user_id or self.env.user
            if todo_type:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_type.id,
                    'summary': 'Follow-up văn bản đi',
                    'note': f"Văn bản: {record.so_ky_hieu} - {record.trich_yeu}",
                    'res_model_id': model_id,
                    'res_id': kh.id,
                    'user_id': user_to_assign.id,
                    'date_deadline': today + timedelta(days=3),
                })
            try:
                kh.message_post(body=f"Đã gửi văn bản đi {record.so_ky_hieu}: {record.trich_yeu}")
            except Exception:
                pass

    def _create_approval_tasks(self):
        """Tạo activity duyệt cho trưởng phòng và giám đốc."""
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get('van_ban_di').id
        for record in self:
            if not todo_type:
                continue
            # Trưởng phòng
            if record.approver_tp_id and record.approver_tp_id.user_id:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_type.id,
                    'summary': 'Duyệt văn bản - Trưởng phòng',
                    'note': f"{record.so_ky_hieu} - {record.trich_yeu}",
                    'res_model_id': model_id,
                    'res_id': record.id,
                    'user_id': record.approver_tp_id.user_id.id,
                    'date_deadline': fields.Date.today() + timedelta(days=1),
                })
            # Giám đốc
            if record.approver_gd_id and record.approver_gd_id.user_id:
                self.env['mail.activity'].create({
                    'activity_type_id': todo_type.id,
                    'summary': 'Duyệt văn bản - Giám đốc',
                    'note': f"{record.so_ky_hieu} - {record.trich_yeu}",
                    'res_model_id': model_id,
                    'res_id': record.id,
                    'user_id': record.approver_gd_id.user_id.id,
                    'date_deadline': fields.Date.today() + timedelta(days=1),
                })

    def _check_approval_complete(self):
        """Khi đủ chữ ký chuyển sang Hoàn tất."""
        today = fields.Date.today()
        for record in self:
            if record.tp_da_duyet and record.gd_da_duyet:
                record.write({
                    'trang_thai': 'hoan_tat',
                    'da_ky_duyet': True,
                    'ngay_ky_duyet': record.ngay_ky_duyet or today,
                })
                record.message_post(body="Văn bản đã được duyệt đủ cấp và chuyển Hoàn tất")

    def _log_approval(self, role='khac', action='approve', note=None):
        """Lưu lịch sử duyệt ở dạng cấu trúc."""
        approval_log = self.env['van_ban_di_approval_log']
        for record in self:
            approver = False
            if role == 'tp':
                approver = record.approver_tp_id
            elif role == 'gd':
                approver = record.approver_gd_id

            approval_log.create({
                'van_ban_di_id': record.id,
                'role': role,
                'nguoi_duyet_id': approver.id if approver else False,
                'user_id': approver.user_id.id if getattr(approver, 'user_id', False) else self.env.user.id,
                'action': action,
                'ghi_chu': note or record.trich_yeu,
            })

    def _propose_opportunity_stage_update(self):
        """Đề xuất cập nhật giai đoạn cơ hội bán hàng khi gửi văn bản đi"""
        self.ensure_one()
        if not self.co_hoi_id:
            return
        
        # Xác định giai đoạn tiếp theo dựa trên loại văn bản
        current_stage = self.co_hoi_id.giai_doan
        proposed_stage = current_stage
        
        # Logic đề xuất giai đoạn dựa trên loại văn bản
        if self.loai_van_ban_id and 'báo giá' in (self.loai_van_ban_id.ten_loai or '').lower():
            if current_stage == 'bao_gia':
                proposed_stage = 'dam_phan'
        elif self.loai_van_ban_id and 'hợp đồng' in (self.loai_van_ban_id.ten_loai or '').lower():
            if current_stage == 'dam_phan':
                proposed_stage = 'thang'
        
        if proposed_stage != current_stage:
            # Tạo activity cho người phụ trách cơ hội để xác nhận cập nhật giai đoạn
            if self.co_hoi_id.nhan_vien_phu_trach_id and self.co_hoi_id.nhan_vien_phu_trach_id.user_id:
                todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                if todo_type:
                    self.env['mail.activity'].create({
                        'activity_type_id': todo_type.id,
                        'summary': f'Cập nhật giai đoạn cơ hội: {self.co_hoi_id.ten_co_hoi}',
                        'note': f"Văn bản '{self.so_ky_hieu}' đã được gửi. Đề xuất cập nhật giai đoạn từ '{dict(self.co_hoi_id._fields['giai_doan'].selection).get(current_stage, current_stage)}' sang '{dict(self.co_hoi_id._fields['giai_doan'].selection).get(proposed_stage, proposed_stage)}'",
                        'res_model_id': self.env['ir.model']._get('co_hoi_ban_hang').id,
                        'res_id': self.co_hoi_id.id,
                        'user_id': self.co_hoi_id.nhan_vien_phu_trach_id.user_id.id,
                        'date_deadline': fields.Date.today() + timedelta(days=1),
                    })
            
            # Gửi thông báo
            self.message_post(
                body=f"Đã đề xuất cập nhật giai đoạn cơ hội '{self.co_hoi_id.ten_co_hoi}' từ '{dict(self.co_hoi_id._fields['giai_doan'].selection).get(current_stage, current_stage)}' sang '{dict(self.co_hoi_id._fields['giai_doan'].selection).get(proposed_stage, proposed_stage)}'"
            )

    def _send_notification_email(self):
        """Gửi email thông báo đến khách hàng khi văn bản đi được phê duyệt"""
        self.ensure_one()
        
        # Kiểm tra xem khách hàng có email không
        if not self.khach_hang_id or not self.khach_hang_id.email:
            self.message_post(
                body="Không thể gửi email: Khách hàng không có địa chỉ email"
            )
            return
        
        # Cấu hình email
        sender_email = "nguyenbinh041104@gmail.com"
        # THAY ĐỔI: Sử dụng App Password của Gmail thay vì mật khẩu thường
        # Cách lấy App Password:
        # 1. Vào https://myaccount.google.com/
        # 2. Security > 2-Step Verification (phải bật trước)
        # 3. App passwords > Tạo password cho "Mail" hoặc tên app tùy ý
        # 4. Copy 16 ký tự password đó vào đây
        sender_password = "xcnq ndxs iqxb tjws"  # Thay thế bằng App Password thực tế
        receiver_email = self.khach_hang_id.email
        
        # Tạo nội dung email
        subject = f"Thông báo: Văn bản {self.so_ky_hieu} đã được phê duyệt"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; }}
                .document-info {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Thông báo phê duyệt văn bản</h2>
                <p>Kính gửi {self.khach_hang_id.ten_khach_hang},</p>
            </div>
            
            <div class="content">
                <p>Chúng tôi xin thông báo rằng văn bản của quý khách đã được phê duyệt và gửi đi.</p>
                
                <div class="document-info">
                    <h3>Thông tin văn bản:</h3>
                    <p><strong>Số/Ký hiệu:</strong> {self.so_ky_hieu}</p>
                    <p><strong>Ngày văn bản:</strong> {self.ngay_van_ban.strftime('%d/%m/%Y') if self.ngay_van_ban else ''}</p>
                    <p><strong>Người ký:</strong> {self.nguoi_ky}</p>
                    <p><strong>Trích yếu:</strong> {self.trich_yeu}</p>
                    <p><strong>Độ khẩn:</strong> {dict(self._fields['do_khan'].selection).get(self.do_khan, self.do_khan)}</p>
                    <p><strong>Độ mật:</strong> {dict(self._fields['do_mat'].selection).get(self.do_mat, self.do_mat)}</p>
                </div>
                
                <p>Văn bản đã được xử lý và sẽ được gửi đến quý khách trong thời gian sớm nhất.</p>
                <p>Nếu quý khách có bất kỳ câu hỏi nào, vui lòng liên hệ với chúng tôi.</p>
            </div>
            
            <div class="footer">
                <p>Trân trọng,<br>
                Phòng Quản lý Văn bản<br>
                Công ty TNHH ABC</p>
            </div>
        </body>
        </html>
        """
        
        try:
            # Tạo message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = receiver_email
            
            # Thêm nội dung HTML
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Thêm file đính kèm nếu có
            if self.file_dinh_kem and self.ten_file:
                try:
                    # Decode base64 file
                    file_data = base64.b64decode(self.file_dinh_kem)
                    
                    # Tạo attachment
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(file_data)
                    encoders.encode_base64(attachment)
                    attachment.add_header('Content-Disposition', f'attachment; filename="{self.ten_file}"')
                    message.attach(attachment)
                except Exception as attach_error:
                    self.message_post(
                        body=f"Không thể đính kèm file: {str(attach_error)}"
                    )
            
            # Gửi email qua Gmail SMTP
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # Bảo mật kết nối
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
            
            self.message_post(
                body=f"Đã gửi email thông báo đến khách hàng: {receiver_email}"
            )
            
        except smtplib.SMTPAuthenticationError:
            self.message_post(
                body="Lỗi xác thực Gmail: Kiểm tra App Password hoặc bật 'Less secure app access'"
            )
        except smtplib.SMTPConnectError:
            self.message_post(
                body="Lỗi kết nối Gmail SMTP: Kiểm tra kết nối internet"
            )
        except Exception as e:
            self.message_post(
                body=f"Lỗi khi gửi email: {str(e)}"
            )


    def action_extract_and_summarize(self):
        """Trích xuất và tóm tắt nội dung văn bản từ file đính kèm"""
        self.ensure_one()
        
        # Kiểm tra file đính kèm từ trường binary
        if not self.file_dinh_kem or not self.ten_file:
            raise models.ValidationError("Không tìm thấy file đính kèm hợp lệ (PDF, DOCX, DOC, TXT)")
        
        # Xác định mimetype từ tên file
        file_name = self.ten_file.lower()
        if file_name.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif file_name.endswith('.docx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_name.endswith('.doc'):
            mimetype = 'application/msword'
        elif file_name.endswith('.txt'):
            mimetype = 'text/plain'
        else:
            raise models.ValidationError("Loại file không được hỗ trợ. Chỉ hỗ trợ PDF, DOCX, DOC, TXT")
        
        try:
            # Gọi chatbot service để xử lý file
            result = self.env['chatbot.service'].process_uploaded_file(
                file_data=self.file_dinh_kem,
                file_name=self.ten_file,
                model_key='openai_gpt4o_mini',
                question="Hãy trích xuất nội dung chính và tóm tắt văn bản này"
            )
            
            if result.get('success'):
                # Cập nhật trích yếu với nội dung tóm tắt
                summary = result.get('summary', result.get('answer', ''))
                if summary:
                    self.write({
                        'trich_yeu': summary[:2000]  # Giới hạn 2000 ký tự
                    })
                    self.message_post(body=f"Đã cập nhật trích yếu từ AI:\n{summary}")
                else:
                    self.message_post(body="AI không thể tạo tóm tắt cho văn bản này")
            else:
                error_msg = result.get('error', 'Lỗi không xác định')
                self.message_post(body=f"Lỗi khi xử lý file: {error_msg}")
                
        except Exception as e:
            self.message_post(body=f"Lỗi hệ thống: {str(e)}")
            raise


class VanBanDiApprovalLog(models.Model):
    _name = 'van_ban_di_approval_log'
    _description = 'Lịch sử duyệt văn bản đi'
    _order = 'ngay_duyet desc'

    van_ban_di_id = fields.Many2one('van_ban_di', string='Văn bản đi', ondelete='cascade', required=True)
    role = fields.Selection([
        ('tp', 'Trưởng phòng'),
        ('gd', 'Giám đốc'),
        ('khac', 'Khác'),
    ], string='Vai trò', default='khac', required=True)
    action = fields.Selection([
        ('approve', 'Duyệt'),
        ('sign', 'Ký'),
        ('reject', 'Từ chối'),
        ('note', 'Ghi chú'),
    ], string='Hành động', default='approve', required=True)
    nguoi_duyet_id = fields.Many2one('nhan_vien', string='Người duyệt', ondelete='set null')
    user_id = fields.Many2one('res.users', string='User', ondelete='set null')
    ngay_duyet = fields.Datetime('Thời gian', default=fields.Datetime.now, required=True)
    ghi_chu = fields.Char('Ghi chú')

