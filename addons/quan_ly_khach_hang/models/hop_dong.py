# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class HopDong(models.Model):
    _name = 'hop_dong'
    _description = 'Quản lý hợp đồng khách hàng'
    _rec_name = 'ten_hop_dong'
    _order = 'ngay_ky desc'

    ma_hop_dong = fields.Char("Mã hợp đồng", required=True, copy=False, default=lambda self: _('New'))
    ten_hop_dong = fields.Char("Tên hợp đồng", required=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    
    loai_hop_dong = fields.Selection([
        ('ban_hang', 'Hợp đồng bán hàng'),
        ('dich_vu', 'Hợp đồng dịch vụ'),
        ('thue', 'Hợp đồng thuê'),
        ('hop_tac', 'Hợp đồng hợp tác'),
        ('lao_dong', 'Hợp đồng lao động'),
        ('khac', 'Khác'),
    ], string="Loại hợp đồng", default='dich_vu')
    
    ngay_ky = fields.Date("Ngày ký", required=True, default=fields.Date.today)
    ngay_hieu_luc = fields.Date("Ngày hiệu lực")
    ngay_het_han = fields.Date("Ngày hết hạn")
    
    gia_tri = fields.Float("Giá trị hợp đồng")
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    nhan_vien_phu_trach_id = fields.Many2one('nhan_vien', string="Nhân viên phụ trách")
    
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('cho_duyet', 'Chờ duyệt'),
        ('hieu_luc', 'Đang hiệu lực'),
        ('het_han', 'Hết hạn'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='nhap')
    
    mo_ta = fields.Text("Mô tả")
    dieu_khoan = fields.Html("Điều khoản")
    
    # File đính kèm
    file_hop_dong = fields.Binary("File hợp đồng")
    file_hop_dong_name = fields.Char("Tên file")

    # Chữ ký (upload ảnh)
    chu_ky_hinh_anh = fields.Binary("Ảnh chữ ký")
    chu_ky_hinh_anh_name = fields.Char("Tên file chữ ký")
    ngay_ky_xac_nhan = fields.Datetime("Ngày ký xác nhận")
    
    # Liên kết với tài liệu
    tai_lieu_ids = fields.One2many('tai_lieu', 'hop_dong_id', string="Tài liệu đính kèm")

    # Liên kết cơ hội bán hàng
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng liên quan", ondelete='set null', tracking=True)
    
    con_hieu_luc = fields.Boolean(compute="_compute_con_hieu_luc", string="Còn hiệu lực", store=True)
    last_draft_reminder_date = fields.Date("Ngày nhắc nháp gần nhất")
    last_approval_reminder_date = fields.Date("Ngày nhắc duyệt gần nhất")
    last_expiry_warning_date = fields.Date("Ngày cảnh báo sắp hết hạn")
    last_effective_reminder_date = fields.Date("Ngày nhắc trước hiệu lực")
    last_expired_notice_date = fields.Date("Ngày thông báo hết hạn")
    
    @api.depends('ngay_het_han', 'trang_thai')
    def _compute_con_hieu_luc(self):
        today = date.today()
        for record in self:
            if record.trang_thai == 'hieu_luc' and record.ngay_het_han:
                record.con_hieu_luc = record.ngay_het_han >= today
            else:
                record.con_hieu_luc = record.trang_thai == 'hieu_luc'
    
    _sql_constraints = [
        ('ma_hop_dong_unique', 'unique(ma_hop_dong)', 'Mã hợp đồng phải là duy nhất!')
    ]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'ma_hop_dong' in fields_list and (not res.get('ma_hop_dong') or res.get('ma_hop_dong') == _('New')):
            res['ma_hop_dong'] = self.env['ir.sequence'].next_by_code('hop_dong') or _('New')
        return res

    @api.model
    def create(self, vals):
        if not vals.get('ma_hop_dong') or vals.get('ma_hop_dong') == _('New'):
            vals['ma_hop_dong'] = self.env['ir.sequence'].next_by_code('hop_dong') or _('New')
        return super().create(vals)
    
    # Workflow methods
    def action_submit_for_approval(self):
        """Chuyển trạng thái từ Nháp sang Chờ duyệt và tạo văn bản đến."""
        for record in self:
            if record.trang_thai == 'nhap':
                record.trang_thai = 'cho_duyet'
                record._create_van_ban_den()
                record._send_contract_email(
                    subject=f"Yêu cầu duyệt hợp đồng {record.ma_hop_dong or ''}",
                    body=record._build_submit_approval_body(),
                    email_to=record._get_approver_email(),
                )
                record.last_approval_reminder_date = fields.Date.today()
    
    def action_approve(self):
        """Duyệt hợp đồng - chuyển sang Hiệu lực và tạo văn bản đi."""
        for record in self:
            if record.trang_thai == 'cho_duyet':
                if not record.chu_ky_hinh_anh:
                    raise UserError("Cần tải lên ảnh chữ ký trước khi duyệt hợp đồng.")
                record.trang_thai = 'hieu_luc'
                record.ngay_ky_xac_nhan = fields.Datetime.now()
                record._create_van_ban_di()
                van_ban_den = self.env['van_ban_den'].search([('hop_dong_id', '=', record.id)], limit=1)
                if van_ban_den:
                    van_ban_den.write({'trang_thai': 'da_xu_ly'})
                record._send_contract_email(
                    subject=f"Hợp đồng {record.ma_hop_dong or ''} đã được duyệt",
                    body=record._build_approved_customer_body(),
                    email_to=record._get_customer_email(),
                    attach_file=True,
                )

    def action_sign(self):
        """Xác nhận ký (khi đang chờ duyệt)."""
        self.ensure_one()
        if self.trang_thai != 'cho_duyet':
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ký hợp đồng',
            'res_model': 'hop_dong.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_hop_dong_id': self.id,
            },
        }
    
    def action_cancel(self):
        """Hủy hợp đồng"""
        for record in self:
            if record.trang_thai in ['nhap', 'cho_duyet', 'hieu_luc']:
                record.trang_thai = 'huy'
    
    def action_expire(self):
        """Đánh dấu hết hạn (có thể gọi tự động)"""
        for record in self:
            if record.trang_thai == 'hieu_luc':
                record.trang_thai = 'het_han'
                record._send_contract_email(
                    subject=f"Hợp đồng {record.ma_hop_dong or ''} đã hết hạn",
                    body=record._build_expired_notice_body(),
                    email_to=record._get_customer_email(),
                    attach_file=True,
                )
                record.last_expired_notice_date = fields.Date.today()

    def action_extract_and_summarize(self):
        """Trích xuất và tóm tắt nội dung hợp đồng từ file đính kèm"""
        self.ensure_one()

        def _safe_message_post(body):
            if hasattr(self, 'message_post') and callable(self.message_post):
                try:
                    self.message_post(body=body)
                except Exception:
                    pass

        if not self.file_hop_dong or not self.file_hop_dong_name:
            raise UserError("Không tìm thấy file hợp đồng hợp lệ (PDF, DOCX, DOC, TXT)")

        file_name = (self.file_hop_dong_name or '').lower()
        if not file_name.endswith(('.pdf', '.docx', '.doc', '.txt')):
            raise UserError("Loại file không được hỗ trợ. Chỉ hỗ trợ PDF, DOCX, DOC, TXT")

        try:
            result = self.env['chatbot.service'].process_uploaded_file(
                file_data=self.file_hop_dong,
                file_name=self.file_hop_dong_name,
                model_key='openai_gpt4o_mini',
                question="Hãy trích xuất nội dung chính và tóm tắt hợp đồng này"
            )

            if result.get('success'):
                summary = result.get('summary', result.get('answer', ''))
                if summary:
                    self.write({'mo_ta': summary[:2000]})
                    _safe_message_post(body=f"Đã cập nhật mô tả từ AI:\n{summary}")
                else:
                    _safe_message_post(body="AI không thể tạo tóm tắt cho hợp đồng này")
            else:
                error_msg = result.get('error', 'Lỗi không xác định')
                _safe_message_post(body=f"Lỗi khi xử lý file: {error_msg}")
        except Exception as exc:
            _safe_message_post(body=f"Lỗi hệ thống: {str(exc)}")
            raise

    def _get_loai_vb(self, ma_loai, ten):
        loai_vb = self.env['loai_van_ban'].search([('ma_loai', '=', ma_loai)], limit=1)
        if not loai_vb:
            loai_vb = self.env['loai_van_ban'].create({
                'ma_loai': ma_loai,
                'ten_loai': ten,
                'mo_ta': ten,
                'hoat_dong': True,
            })
        return loai_vb

    def _create_van_ban_den(self):
        self.ensure_one()
        if self.env['van_ban_den'].search([('hop_dong_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('HD', 'Hợp đồng')
        count = self.env['van_ban_den'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"HD/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_den'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_den': fields.Date.today(),
            'ngay_van_ban': self.ngay_ky or fields.Date.today(),
            'noi_ban_hanh': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': '',
            'trich_yeu': f"Hợp đồng: {self.ten_hop_dong} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_xu_ly_id': self.nhan_vien_phu_trach_id.id if self.nhan_vien_phu_trach_id else False,
            'trang_thai': 'moi',
            'hop_dong_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'han_xu_ly': fields.Date.today() + timedelta(days=3),
            'file_dinh_kem': self.file_hop_dong,
            'ten_file': self.file_hop_dong_name,
            'ghi_chu': f"Văn bản tạo tự động khi gửi duyệt hợp đồng {self.ma_hop_dong}",
        })

    def _create_van_ban_di(self):
        self.ensure_one()
        if self.env['van_ban_di'].search([('hop_dong_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('HD', 'Hợp đồng')
        count = self.env['van_ban_di'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_van_ban', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"HD/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_di'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_van_ban': fields.Date.today(),
            'ngay_gui': fields.Date.today(),
            'noi_nhan': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': self.env.user.name,
            'trich_yeu': f"Duyệt hợp đồng: {self.ten_hop_dong} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_soan_thao_id': self.nhan_vien_phu_trach_id.id if self.nhan_vien_phu_trach_id else False,
            'don_vi_soan_thao_id': False,
            'trang_thai': 'da_gui',
            'hop_dong_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'file_dinh_kem': self.file_hop_dong,
            'ten_file': self.file_hop_dong_name,
            'ghi_chu': f"Văn bản tạo tự động khi duyệt hợp đồng {self.ma_hop_dong}",
        })

    def _get_customer_email(self):
        return self.khach_hang_id.email if self.khach_hang_id else False

    def _get_approver_email(self):
        return self.nhan_vien_phu_trach_id.email if self.nhan_vien_phu_trach_id else False

    def _has_valid_signature(self):
        """Backward-compatible helper: kiểm tra có ảnh chữ ký"""
        return bool(self.chu_ky_hinh_anh)

    def _log_email(self, subject, email_to, status='sent', error_message=None, mail_id=None, template_xmlid=None):
        model_exists = self.env['ir.model'].sudo().search([('model', '=', 'qlvb.email.log')], limit=1)
        if not model_exists:
            return
        self.env['qlvb.email.log'].sudo().create({
            'name': f"{self.ma_hop_dong or self.id} - {subject}" if subject else f"{self.ma_hop_dong or self.id}",
            'model_name': self._name,
            'res_id': self.id,
            'res_name': self.ten_hop_dong,
            'email_to': email_to or '',
            'email_from': self.env.user.email_formatted or self.env.company.email or '',
            'subject': subject or '',
            'status': status,
            'error_message': error_message,
            'mail_id': mail_id or False,
            'template_xmlid': template_xmlid or False,
            'sent_date': fields.Datetime.now(),
        })

    def _send_contract_email(self, subject, body, email_to=None, attach_file=False):
        self.ensure_one()
        if not email_to:
            self._log_email(subject, email_to, status='failed', error_message='Thiếu email người nhận', template_xmlid=None)
            return False

        email_values = {
            'email_to': email_to,
            'subject': subject,
            'body_html': body,
            'email_from': self.env.user.email_formatted or self.env.company.email or '',
        }
        attachment_ids = []
        if attach_file and self.file_hop_dong:
            attachment = self.env['ir.attachment'].create({
                'name': self.file_hop_dong_name or f"HopDong_{self.ma_hop_dong}",
                'type': 'binary',
                'datas': self.file_hop_dong,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/octet-stream',
            })
            attachment_ids.append(attachment.id)
        if attachment_ids:
            email_values['attachment_ids'] = [(6, 0, attachment_ids)]

        try:
            mail = self.env['mail.mail'].create({
                'subject': email_values['subject'],
                'body_html': email_values['body_html'],
                'email_to': email_values['email_to'],
                'email_from': email_values['email_from'],
                'attachment_ids': email_values.get('attachment_ids', []),
                'auto_delete': False,
            })
            mail.send()
            mail_id = mail.id
            self._log_email(subject, email_to, status='sent', mail_id=mail_id, template_xmlid=None)
            return True
        except Exception as exc:
            self._log_email(subject, email_to, status='failed', error_message=str(exc), template_xmlid=None)
            return False

    def _build_submit_approval_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Xin chào,</p>
    <p>Hợp đồng sau đã được gửi duyệt:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Loại hợp đồng: {dict(self._fields['loai_hop_dong'].selection).get(self.loai_hop_dong) or ''}</li>
        <li>Khách hàng: {self.khach_hang_id.ten_khach_hang or ''}</li>
        <li>Giá trị: {self.gia_tri or 0} {self.don_vi_tien or ''}</li>
        <li>Ngày hiệu lực: {self.ngay_hieu_luc or ''}</li>
    </ul>
    <p>Vui lòng kiểm tra và thực hiện phê duyệt.</p>
</div>
"""

    def _build_approved_customer_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Kính gửi {self.khach_hang_id.ten_khach_hang or ''},</p>
    <p>Hợp đồng của Quý khách đã được duyệt. Thông tin chi tiết:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Loại hợp đồng: {dict(self._fields['loai_hop_dong'].selection).get(self.loai_hop_dong) or ''}</li>
        <li>Giá trị: {self.gia_tri or 0} {self.don_vi_tien or ''}</li>
        <li>Ngày hiệu lực: {self.ngay_hieu_luc or ''}</li>
        <li>Ngày hết hạn: {self.ngay_het_han or ''}</li>
    </ul>
    <p>Hợp đồng được đính kèm trong email.</p>
    <p>Trân trọng.</p>
</div>
"""

    def _build_expired_notice_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Kính gửi {self.khach_hang_id.ten_khach_hang or ''},</p>
    <p>Hợp đồng đã hết hạn. Thông tin:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Ngày hết hạn: {self.ngay_het_han or ''}</li>
    </ul>
    <p>Vui lòng liên hệ để được hỗ trợ.</p>
</div>
"""

    def _build_draft_reminder_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Xin chào,</p>
    <p>Hợp đồng đang ở trạng thái <strong>Nháp</strong> cần được hoàn thiện:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Loại hợp đồng: {dict(self._fields['loai_hop_dong'].selection).get(self.loai_hop_dong) or ''}</li>
        <li>Khách hàng: {self.khach_hang_id.ten_khach_hang or ''}</li>
        <li>Giá trị: {self.gia_tri or 0} {self.don_vi_tien or ''}</li>
        <li>Ngày hiệu lực: {self.ngay_hieu_luc or ''}</li>
    </ul>
    <p>Vui lòng hoàn thiện và gửi duyệt.</p>
</div>
"""

    def _build_approval_reminder_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Xin chào,</p>
    <p>Hợp đồng sau vẫn đang chờ duyệt:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Khách hàng: {self.khach_hang_id.ten_khach_hang or ''}</li>
        <li>Ngày hiệu lực: {self.ngay_hieu_luc or ''}</li>
    </ul>
    <p>Vui lòng xử lý phê duyệt sớm.</p>
</div>
"""

    def _build_effective_reminder_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Kính gửi {self.khach_hang_id.ten_khach_hang or ''},</p>
    <p>Nhắc lịch ký hợp đồng trước ngày hiệu lực:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Ngày hiệu lực: {self.ngay_hieu_luc or ''}</li>
    </ul>
    <p>Vui lòng xác nhận lịch ký.</p>
</div>
"""

    def _build_expiry_warning_body(self):
        self.ensure_one()
        return f"""
<div>
    <p>Kính gửi {self.khach_hang_id.ten_khach_hang or ''},</p>
    <p>Hợp đồng của Quý khách sắp hết hạn. Thông tin:</p>
    <ul>
        <li>Mã hợp đồng: {self.ma_hop_dong or ''}</li>
        <li>Tên hợp đồng: {self.ten_hop_dong or ''}</li>
        <li>Ngày hết hạn: {self.ngay_het_han or ''}</li>
    </ul>
    <p>Vui lòng liên hệ để gia hạn nếu cần.</p>
</div>
"""

    def _get_config_days(self, key, default_days):
        value = self.env['ir.config_parameter'].sudo().get_param(key)
        try:
            return int(value) if value is not None else default_days
        except Exception:
            return default_days

    @api.model
    def _cron_send_draft_reminders(self):
        days = self._get_config_days('hop_dong.draft_reminder_days', 3)
        cutoff = fields.Datetime.now() - timedelta(days=days)
        records = self.search([
            ('trang_thai', '=', 'nhap'),
            ('create_date', '<=', cutoff),
        ])
        for record in records:
            if record.last_draft_reminder_date and record.last_draft_reminder_date >= fields.Date.today():
                continue
            record._send_contract_email(
                subject=f"Nhắc hoàn thiện hợp đồng {record.ma_hop_dong or ''}",
                body=record._build_draft_reminder_body(),
                email_to=record._get_approver_email(),
            )
            record.last_draft_reminder_date = fields.Date.today()

    @api.model
    def _cron_send_approval_reminders(self):
        days = self._get_config_days('hop_dong.approval_reminder_days', 2)
        cutoff = fields.Datetime.now() - timedelta(days=days)
        records = self.search([
            ('trang_thai', '=', 'cho_duyet'),
            ('write_date', '<=', cutoff),
        ])
        for record in records:
            if record.last_approval_reminder_date and record.last_approval_reminder_date >= fields.Date.today():
                continue
            record._send_contract_email(
                subject=f"Nhắc duyệt hợp đồng {record.ma_hop_dong or ''}",
                body=record._build_approval_reminder_body(),
                email_to=record._get_approver_email(),
            )
            record.last_approval_reminder_date = fields.Date.today()

    @api.model
    def _cron_send_effective_reminders(self):
        days = self._get_config_days('hop_dong.sign_reminder_days', 3)
        target_date = fields.Date.today() + timedelta(days=days)
        records = self.search([
            ('ngay_hieu_luc', '=', target_date),
            ('trang_thai', 'in', ['nhap', 'cho_duyet']),
        ])
        for record in records:
            if record.last_effective_reminder_date == fields.Date.today():
                continue
            record._send_contract_email(
                subject=f"Nhắc lịch ký hợp đồng {record.ma_hop_dong or ''}",
                body=record._build_effective_reminder_body(),
                email_to=record._get_customer_email(),
            )
            record.last_effective_reminder_date = fields.Date.today()

    @api.model
    def _cron_check_expiry(self):
        warning_days = self._get_config_days('hop_dong.expiry_warning_days', 7)
        today = fields.Date.today()

        # Warning before expiry
        warning_date = today + timedelta(days=warning_days)
        warning_records = self.search([
            ('trang_thai', '=', 'hieu_luc'),
            ('ngay_het_han', '=', warning_date),
        ])
        for record in warning_records:
            if record.last_expiry_warning_date == today:
                continue
            record._send_contract_email(
                subject=f"Hợp đồng {record.ma_hop_dong or ''} sắp hết hạn",
                body=record._build_expiry_warning_body(),
                email_to=record._get_customer_email(),
            )
            record.last_expiry_warning_date = today

        # Expire overdue
        expired_records = self.search([
            ('trang_thai', '=', 'hieu_luc'),
            ('ngay_het_han', '!=', False),
            ('ngay_het_han', '<', today),
        ])
        for record in expired_records:
            if record.trang_thai == 'hieu_luc':
                record.trang_thai = 'het_han'
                if record.last_expired_notice_date != today:
                    record._send_contract_email(
                        subject=f"Hợp đồng {record.ma_hop_dong or ''} đã hết hạn",
                        body=record._build_expired_notice_body(),
                        email_to=record._get_customer_email(),
                        attach_file=True,
                    )
                    record.last_expired_notice_date = today
