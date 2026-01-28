# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class BaoGia(models.Model):
    _name = 'bao_gia'
    _description = 'Quản lý báo giá'
    _rec_name = 'ten_bao_gia'
    _order = 'ngay_tao desc'

    ma_bao_gia = fields.Char("Mã báo giá", required=True, copy=False, default=lambda self: _('New'))
    ten_bao_gia = fields.Char("Tên báo giá", required=True)
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", required=True, ondelete='cascade')
    co_hoi_id = fields.Many2one('co_hoi_ban_hang', string="Cơ hội bán hàng", ondelete='set null')
    
    ngay_tao = fields.Date("Ngày tạo", required=True, default=fields.Date.today)
    ngay_hieu_luc = fields.Date("Hiệu lực đến", default=lambda self: date.today() + timedelta(days=30))
    
    tong_gia_tri = fields.Float("Tổng giá trị")
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    nhan_vien_lap_id = fields.Many2one('nhan_vien', string="Nhân viên lập")
    
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('gui_khach', 'Đã gửi khách'),
        ('khach_dong_y', 'Khách đồng ý'),
        ('khach_tu_choi', 'Khách từ chối'),
        ('het_han', 'Hết hạn'),
    ], string="Trạng thái", default='nhap')
    
    noi_dung = fields.Html("Nội dung báo giá")
    ghi_chu = fields.Text("Ghi chú")
    
    # File đính kèm
    file_bao_gia = fields.Binary("File báo giá")
    file_bao_gia_name = fields.Char("Tên file")
    
    # Quan hệ với hợp đồng (nếu báo giá được chấp nhận)
    hop_dong_id = fields.Many2one('hop_dong', string="Hợp đồng liên quan")
    
    _sql_constraints = [
        ('ma_bao_gia_unique', 'unique(ma_bao_gia)', 'Mã báo giá phải là duy nhất!')
    ]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'ma_bao_gia' in fields_list and (not res.get('ma_bao_gia') or res.get('ma_bao_gia') == _('New')):
            res['ma_bao_gia'] = self.env['ir.sequence'].next_by_code('bao_gia') or _('New')
        return res

    @api.model
    def create(self, vals):
        if not vals.get('ma_bao_gia') or vals.get('ma_bao_gia') == _('New'):
            vals['ma_bao_gia'] = self.env['ir.sequence'].next_by_code('bao_gia') or _('New')
        return super().create(vals)
    
    # Workflow methods
    def action_send_to_customer(self):
        """Gửi báo giá cho khách hàng"""
        for record in self:
            if record.trang_thai == 'nhap':
                record._send_bao_gia_email()
                record.trang_thai = 'gui_khach'
                record._create_van_ban_den()
        if self.env.context.get('open_in_popup'):
            self.ensure_one()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Báo giá',
                'res_model': 'bao_gia',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': dict(self.env.context),
            }
    
    def action_customer_approve(self):
        """Khách hàng đồng ý báo giá"""
        for record in self:
            if record.trang_thai == 'gui_khach':
                record.trang_thai = 'khach_dong_y'
    
    def action_customer_reject(self):
        """Khách hàng từ chối báo giá"""
        for record in self:
            if record.trang_thai == 'gui_khach':
                record.trang_thai = 'khach_tu_choi'
    
    def action_expire(self):
        """Báo giá hết hạn"""
        for record in self:
            if record.trang_thai in ['nhap', 'gui_khach']:
                record.trang_thai = 'het_han'

    def action_extract_and_summarize(self):
        """Trích xuất và tóm tắt nội dung báo giá từ file đính kèm"""
        self.ensure_one()

        def _safe_message_post(body):
            if hasattr(self, 'message_post') and callable(self.message_post):
                try:
                    self.message_post(body=body)
                except Exception:
                    pass

        if not self.file_bao_gia or not self.file_bao_gia_name:
            raise UserError("Không tìm thấy file báo giá hợp lệ (PDF, DOCX, DOC, TXT)")

        file_name = (self.file_bao_gia_name or '').lower()
        if not file_name.endswith(('.pdf', '.docx', '.doc', '.txt')):
            raise UserError("Loại file không được hỗ trợ. Chỉ hỗ trợ PDF, DOCX, DOC, TXT")

        try:
            result = self.env['chatbot.service'].process_uploaded_file(
                file_data=self.file_bao_gia,
                file_name=self.file_bao_gia_name,
                model_key='openai_gpt4o_mini',
                question="Hãy trích xuất nội dung chính và tóm tắt báo giá này"
            )

            if result.get('success'):
                summary = result.get('summary', result.get('answer', ''))
                if summary:
                    self.write({'ghi_chu': summary[:2000]})
                    _safe_message_post(body=f"Đã cập nhật ghi chú từ AI:\n{summary}")
                else:
                    _safe_message_post(body="AI không thể tạo tóm tắt cho báo giá này")
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
        if self.env['van_ban_den'].search([('bao_gia_id', '=', self.id)], limit=1):
            return
        loai_vb = self._get_loai_vb('BG', 'Báo giá')
        count = self.env['van_ban_den'].search_count([
            ('loai_van_ban_id', '=', loai_vb.id),
            ('ngay_den', '>=', fields.Date.today().replace(month=1, day=1))
        ]) + 1
        so_ky_hieu = f"BG/{count:04d}/{fields.Date.today().year}"
        self.env['van_ban_den'].create({
            'so_ky_hieu': so_ky_hieu,
            'ngay_den': fields.Date.today(),
            'ngay_van_ban': self.ngay_tao or fields.Date.today(),
            'noi_ban_hanh': self.khach_hang_id.ten_khach_hang if self.khach_hang_id else 'Khách hàng',
            'nguoi_ky': '',
            'trich_yeu': f"Báo giá: {self.ten_bao_gia} - Khách hàng: {self.khach_hang_id.ten_khach_hang if self.khach_hang_id else ''}",
            'loai_van_ban_id': loai_vb.id,
            'do_khan': 'thuong',
            'do_mat': 'binh_thuong',
            'nguoi_xu_ly_id': self.nhan_vien_lap_id.id if self.nhan_vien_lap_id else False,
            'trang_thai': 'moi',
            'bao_gia_id': self.id,
            'khach_hang_id': self.khach_hang_id.id if self.khach_hang_id else False,
            'han_xu_ly': fields.Date.today() + timedelta(days=3),
            'file_dinh_kem': self.file_bao_gia,
            'ten_file': self.file_bao_gia_name,
            'ghi_chu': f"Văn bản tạo tự động khi gửi báo giá {self.ma_bao_gia}",
        })

    def _send_bao_gia_email(self):
        """Gửi email báo giá cho khách hàng với thông tin chi tiết"""
        self.ensure_one()
        if not self.khach_hang_id or not self.khach_hang_id.email:
            self._log_email('Báo giá', self.khach_hang_id.email if self.khach_hang_id else '', status='failed', error_message='Khách hàng chưa có email')
            raise UserError("Khách hàng chưa có email. Vui lòng cập nhật email trước khi gửi báo giá.")

        email_from = self.env.user.email_formatted or self.env.company.email or 'no-reply@example.com'
        email_to = self.khach_hang_id.email

        currency_label = dict(self._fields['don_vi_tien'].selection).get(self.don_vi_tien, '').upper()
        tong_gia_tri = f"{self.tong_gia_tri:,.0f} {currency_label}" if self.tong_gia_tri else "0"

        co_hoi_info = self.co_hoi_id.ten_co_hoi if self.co_hoi_id else ""
        nhan_vien_info = self.nhan_vien_lap_id.ho_va_ten if self.nhan_vien_lap_id else self.env.user.name

        body_html = f"""
        <div>
            <p>Kính gửi {self.khach_hang_id.ten_khach_hang},</p>
            <p>Chúng tôi gửi đến Quý khách báo giá với thông tin chi tiết như sau:</p>
            <ul>
                <li><strong>Mã báo giá:</strong> {self.ma_bao_gia or ''}</li>
                <li><strong>Tên báo giá:</strong> {self.ten_bao_gia or ''}</li>
                <li><strong>Ngày tạo:</strong> {self.ngay_tao or ''}</li>
                <li><strong>Hiệu lực đến:</strong> {self.ngay_hieu_luc or ''}</li>
                <li><strong>Tổng giá trị:</strong> {tong_gia_tri}</li>
                <li><strong>Cơ hội bán hàng:</strong> {co_hoi_info}</li>
                <li><strong>Nhân viên lập:</strong> {nhan_vien_info}</li>
            </ul>
            <p><strong>Nội dung báo giá:</strong></p>
            <div>{self.noi_dung or ''}</div>
            <p><strong>Ghi chú:</strong> {self.ghi_chu or ''}</p>
            <p>Trân trọng,</p>
            <p>{nhan_vien_info}</p>
        </div>
        """

        attachments = []
        if self.file_bao_gia:
            attachment = self.env['ir.attachment'].create({
                'name': self.file_bao_gia_name or f"BaoGia_{self.ma_bao_gia}.pdf",
                'type': 'binary',
                'datas': self.file_bao_gia,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/octet-stream',
            })
            attachments.append(attachment.id)

        mail = self.env['mail.mail'].create({
            'subject': f"Báo giá {self.ma_bao_gia} - {self.ten_bao_gia}",
            'body_html': body_html,
            'email_from': email_from,
            'email_to': email_to,
            'attachment_ids': [(6, 0, attachments)] if attachments else [],
        })
        try:
            mail.send()
            self._log_email(mail.subject, email_to, status='sent', mail_id=mail.id)
        except Exception as exc:
            self._log_email(mail.subject, email_to, status='failed', error_message=str(exc), mail_id=mail.id)

    def _log_email(self, subject, email_to, status='sent', error_message=None, mail_id=None):
        model_exists = self.env['ir.model'].sudo().search([('model', '=', 'qlvb.email.log')], limit=1)
        if not model_exists:
            return
        self.env['qlvb.email.log'].sudo().create({
            'name': f"{self.ma_bao_gia or self.id} - {subject}" if subject else f"{self.ma_bao_gia or self.id}",
            'model_name': self._name,
            'res_id': self.id,
            'res_name': self.ten_bao_gia,
            'email_to': email_to or '',
            'email_from': self.env.user.email_formatted or self.env.company.email or '',
            'subject': subject or '',
            'status': status,
            'error_message': error_message,
            'mail_id': mail_id or False,
            'sent_date': fields.Datetime.now(),
        })
