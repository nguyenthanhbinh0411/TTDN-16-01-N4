# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class GiaoHang(models.Model):
    _name = 'giao_hang'
    _description = 'Quản lý giao hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_giao_hang'
    _order = 'ngay_giao_hang_du_kien desc'

    # Thông tin cơ bản
    ma_giao_hang = fields.Char("Mã giao hàng", required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('giao_hang') or 'New')
    don_hang_id = fields.Many2one('don_hang', string="Đơn hàng", required=True, tracking=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='don_hang_id.khach_hang_id', store=True)
    
    # Địa chỉ giao hàng
    dia_chi_giao_hang = fields.Text("Địa chỉ giao hàng", required=True)
    nguoi_nhan = fields.Char("Người nhận", required=True)
    so_dien_thoai_nguoi_nhan = fields.Char("Số điện thoại người nhận", required=True)
    
    # Ngày giờ
    ngay_giao_hang_du_kien = fields.Date("Ngày giao hàng dự kiến", tracking=True)
    ngay_giao_hang_thuc_te = fields.Date("Ngày giao hàng thực tế", tracking=True)
    gio_giao_hang = fields.Char("Giờ giao hàng")
    
    # Trạng thái vận chuyển
    trang_thai = fields.Selection([
        ('chuan_bi', 'Chuẩn bị'),
        ('dang_van_chuyen', 'Đang vận chuyển'),
        ('da_giao', 'Đã giao'),
        ('that_bai', 'Giao thất bại'),
        ('hoan_tra', 'Hoàn trả'),
    ], string="Trạng thái", default='chuan_bi', required=True, tracking=True)
    
    # Thông tin vận chuyển
    don_vi_van_chuyen = fields.Char("Đơn vị vận chuyển")
    ma_van_don = fields.Char("Mã vận đơn")
    phi_van_chuyen = fields.Float("Phí vận chuyển")
    
    # Người ký nhận
    nguoi_ky_nhan = fields.Char("Người ký nhận", tracking=True)
    ngay_ky_nhan = fields.Date("Ngày ký nhận", tracking=True)
    chu_ky_dien_tu = fields.Binary("Chữ ký điện tử")
    anh_xac_nhan = fields.Binary("Ảnh xác nhận giao hàng")
    
    # Lý do giao thất bại
    ly_do_that_bai = fields.Text("Lý do giao thất bại")
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('ma_giao_hang_unique', 'unique(ma_giao_hang)', 'Mã giao hàng phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('ma_giao_hang', 'New') == 'New':
            vals['ma_giao_hang'] = self.env['ir.sequence'].next_by_code('giao_hang') or 'New'
        return super().create(vals)
    
    @api.onchange('don_hang_id')
    def _onchange_don_hang(self):
        """Điền sẵn thông tin từ khách hàng"""
        if self.don_hang_id and self.don_hang_id.khach_hang_id:
            kh = self.don_hang_id.khach_hang_id
            self.dia_chi_giao_hang = kh.dia_chi
            self.nguoi_nhan = kh.ten_khach_hang
            self.so_dien_thoai_nguoi_nhan = kh.dien_thoai
    
    def action_bat_dau_van_chuyen(self):
        """Bắt đầu vận chuyển"""
        for record in self:
            if record.trang_thai == 'chuan_bi':
                record.trang_thai = 'dang_van_chuyen'
                record._send_bat_dau_van_chuyen_email()
    
    def action_xac_nhan_da_giao(self):
        """Xác nhận đã giao hàng"""
        self.ensure_one()
        if self.trang_thai != 'dang_van_chuyen':
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Xác nhận đã giao hàng',
            'res_model': 'giao_hang.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_giao_hang_id': self.id,
                'default_nguoi_nhan': self.nguoi_nhan,
                'default_nguoi_ky_nhan': self.nguoi_ky_nhan,
                'default_ngay_ky_nhan': fields.Date.today(),
            },
        }
    
    def action_danh_dau_that_bai(self):
        """Đánh dấu giao thất bại"""
        for record in self:
            if record.trang_thai == 'dang_van_chuyen':
                record.trang_thai = 'that_bai'

    def _create_hoa_don_from_giao_hang(self):
        """Tạo hóa đơn tự động khi giao hàng đã hoàn tất"""
        self.ensure_one()
        don_hang = self.don_hang_id
        if not don_hang:
            return False

        hoa_don_obj = self.env['hoa_don']
        existing = hoa_don_obj.search([('giao_hang_id', '=', self.id)], limit=1)
        if existing:
            return existing

        chi_tiet_lines = []
        for chi_tiet in don_hang.don_hang_chi_tiet_ids:
            chi_tiet_lines.append((0, 0, {
                'ten_san_pham': chi_tiet.ten_san_pham,
                'mo_ta': chi_tiet.mo_ta,
                'so_luong': chi_tiet.so_luong,
                'don_vi_tinh': chi_tiet.don_vi_tinh,
                'don_gia': chi_tiet.don_gia,
            }))

        if self.phi_van_chuyen and self.phi_van_chuyen > 0:
            chi_tiet_lines.append((0, 0, {
                'ten_san_pham': 'Phí vận chuyển',
                'mo_ta': f"Mã giao hàng: {self.ma_giao_hang}",
                'so_luong': 1,
                'don_vi_tinh': 'Lần',
                'don_gia': self.phi_van_chuyen,
            }))

        ngay_du_kien = self.ngay_giao_hang_du_kien.strftime('%d/%m/%Y') if self.ngay_giao_hang_du_kien else 'Chưa xác định'
        ngay_thuc_te = self.ngay_giao_hang_thuc_te.strftime('%d/%m/%Y') if self.ngay_giao_hang_thuc_te else 'Chưa xác định'

        ghi_chu = (
            f"Thông tin giao hàng:\n"
            f"- Mã giao hàng: {self.ma_giao_hang}\n"
            f"- Người nhận: {self.nguoi_nhan}\n"
            f"- SĐT người nhận: {self.so_dien_thoai_nguoi_nhan}\n"
            f"- Địa chỉ giao hàng: {self.dia_chi_giao_hang}\n"
            f"- Ngày giao dự kiến: {ngay_du_kien}\n"
            f"- Ngày giao thực tế: {ngay_thuc_te}\n"
            f"- Đơn vị vận chuyển: {self.don_vi_van_chuyen or 'Chưa xác định'}\n"
            f"- Mã vận đơn: {self.ma_van_don or 'Chưa có'}"
        )

        return hoa_don_obj.create({
            'khach_hang_id': don_hang.khach_hang_id.id,
            'don_hang_id': don_hang.id,
            'giao_hang_id': self.id,
            'don_vi_tien': don_hang.don_vi_tien,
            'hoa_don_chi_tiet_ids': chi_tiet_lines,
            'ghi_chu': ghi_chu,
        })

    def _send_bat_dau_van_chuyen_email(self):
        """Gửi email khi bắt đầu vận chuyển (không dùng mail_templates)"""
        self.ensure_one()
        khach_hang = self.khach_hang_id or self.don_hang_id.khach_hang_id
        email_to = khach_hang.email if khach_hang else False
        if not email_to:
            self._log_email(
                subject=f"Đơn hàng {self.don_hang_id.ma_don_hang} đang được vận chuyển",
                email_to=email_to,
                status='failed',
                error_message='Khách hàng chưa có email',
            )
            raise UserError("Khách hàng chưa có email để gửi thông báo vận chuyển.")

        email_from = self.env.user.email_formatted or self.env.company.email or 'no-reply@example.com'
        subject = f"Đơn hàng {self.don_hang_id.ma_don_hang} đang được vận chuyển"
        body_html = f"""
            <p>Xin chào {khach_hang.ten_khach_hang or ''},</p>
            <p>Đơn hàng của bạn đang được vận chuyển.</p>
            <p><strong>Thông tin đơn hàng:</strong></p>
            <ul>
                <li>Mã đơn hàng: <strong>{self.don_hang_id.ma_don_hang}</strong></li>
                <li>Mã giao hàng: <strong>{self.ma_giao_hang}</strong></li>
                <li>Người nhận: {self.nguoi_nhan}</li>
                <li>Số điện thoại: {self.so_dien_thoai_nguoi_nhan}</li>
                <li>Địa chỉ giao hàng: {self.dia_chi_giao_hang}</li>
                <li>Ngày giao dự kiến: {self.ngay_giao_hang_du_kien.strftime('%d/%m/%Y') if self.ngay_giao_hang_du_kien else 'Chưa xác định'}</li>
                <li>Giờ giao hàng: {self.gio_giao_hang or 'Chưa xác định'}</li>
                <li>Đơn vị vận chuyển: {self.don_vi_van_chuyen or 'Chưa xác định'}</li>
                <li>Mã vận đơn: {self.ma_van_don or 'Chưa có'}</li>
            </ul>
            <p>Vui lòng chuẩn bị nhận hàng đúng thời gian. Nếu có vấn đề gì, hãy liên hệ với chúng tôi.</p>
            <p>Trân trọng.</p>
        """

        mail = self.env['mail.mail'].create({
            'subject': subject,
            'body_html': body_html,
            'email_to': email_to,
            'email_from': email_from,
            'auto_delete': True,
        })
        try:
            mail.send()
            self._log_email(subject, email_to, status='sent', mail_id=mail.id)
        except Exception as exc:
            self._log_email(subject, email_to, status='failed', error_message=str(exc), mail_id=mail.id)

    def _send_da_giao_email(self):
        """Gửi email khi xác nhận đã giao hàng (không dùng mail_templates)"""
        self.ensure_one()
        khach_hang = self.khach_hang_id or self.don_hang_id.khach_hang_id
        email_to = khach_hang.email if khach_hang else False
        if not email_to:
            self._log_email(
                subject=f"Xác nhận giao hàng thành công - Đơn {self.don_hang_id.ma_don_hang}",
                email_to=email_to,
                status='failed',
                error_message='Khách hàng chưa có email',
            )
            raise UserError("Khách hàng chưa có email để gửi thông báo đã giao hàng.")

        email_from = self.env.user.email_formatted or self.env.company.email or 'no-reply@example.com'
        subject = f"Xác nhận giao hàng thành công - Đơn {self.don_hang_id.ma_don_hang}"

        ngay_du_kien = self.ngay_giao_hang_du_kien.strftime('%d/%m/%Y') if self.ngay_giao_hang_du_kien else 'Chưa xác định'
        ngay_thuc_te = self.ngay_giao_hang_thuc_te.strftime('%d/%m/%Y') if self.ngay_giao_hang_thuc_te else 'Chưa xác định'
        ngay_ky = self.ngay_ky_nhan.strftime('%d/%m/%Y') if self.ngay_ky_nhan else 'Chưa xác định'

        body_html = f"""
            <p>Xin chào {khach_hang.ten_khach_hang or ''},</p>
            <p>Đơn hàng của bạn đã được giao thành công.</p>
            <p><strong>Thông tin đơn hàng &amp; giao hàng:</strong></p>
            <ul>
                <li>Mã đơn hàng: <strong>{self.don_hang_id.ma_don_hang}</strong></li>
                <li>Mã giao hàng: <strong>{self.ma_giao_hang}</strong></li>
                <li>Người nhận: {self.nguoi_nhan}</li>
                <li>Số điện thoại: {self.so_dien_thoai_nguoi_nhan}</li>
                <li>Địa chỉ giao hàng: {self.dia_chi_giao_hang}</li>
                <li>Ngày giao dự kiến: {ngay_du_kien}</li>
                <li>Ngày giao thực tế: {ngay_thuc_te}</li>
                <li>Giờ giao hàng: {self.gio_giao_hang or 'Chưa xác định'}</li>
                <li>Đơn vị vận chuyển: {self.don_vi_van_chuyen or 'Chưa xác định'}</li>
                <li>Mã vận đơn: {self.ma_van_don or 'Chưa có'}</li>
                <li>Người ký nhận: {self.nguoi_ky_nhan or 'Chưa xác định'}</li>
                <li>Ngày ký nhận: {ngay_ky}</li>
            </ul>
            <p>Chữ ký và ảnh xác nhận đã được lưu trong hệ thống.</p>
            <p>Trân trọng.</p>
        """

        attachments = []
        if self.chu_ky_dien_tu:
            attachments.append((f"chu_ky_{self.ma_giao_hang}.png", self.chu_ky_dien_tu))
        if self.anh_xac_nhan:
            attachments.append((f"xac_nhan_{self.ma_giao_hang}.png", self.anh_xac_nhan))

        attachment_ids = []
        for name, datas in attachments:
            attachment_ids.append(self.env['ir.attachment'].create({
                'name': name,
                'datas': datas,
                'res_model': 'giao_hang',
                'res_id': self.id,
            }).id)

        mail_vals = {
            'subject': subject,
            'body_html': body_html,
            'email_to': email_to,
            'email_from': email_from,
            'auto_delete': True,
        }
        if attachment_ids:
            mail_vals['attachment_ids'] = [(6, 0, attachment_ids)]

        mail = self.env['mail.mail'].create(mail_vals)
        try:
            mail.send()
            self._log_email(subject, email_to, status='sent', mail_id=mail.id)
        except Exception as exc:
            self._log_email(subject, email_to, status='failed', error_message=str(exc), mail_id=mail.id)
    
    @api.model
    def create(self, vals):
        """Tự sinh mã giao hàng khi tạo mới (không đổi trạng thái đơn hàng)"""
        if vals.get('ma_giao_hang', 'New') == 'New':
            vals['ma_giao_hang'] = self.env['ir.sequence'].next_by_code('giao_hang') or 'New'

        don_hang = self.env['don_hang'].browse(vals.get('don_hang_id')) if vals.get('don_hang_id') else False
        trang_thai_truoc = don_hang.trang_thai if don_hang else False

        record = super(GiaoHang, self).create(vals)

        if don_hang and trang_thai_truoc and don_hang.trang_thai != trang_thai_truoc:
            don_hang.write({'trang_thai': trang_thai_truoc})

        return record

    def _log_email(self, subject, email_to, status='sent', error_message=None, mail_id=None):
        model_exists = self.env['ir.model'].sudo().search([('model', '=', 'qlvb.email.log')], limit=1)
        if not model_exists:
            return
        if mail_id and not self.env['mail.mail'].sudo().browse(mail_id).exists():
            mail_id = False
        self.env['qlvb.email.log'].sudo().create({
            'name': f"{self.ma_giao_hang or self.id} - {subject}" if subject else f"{self.ma_giao_hang or self.id}",
            'model_name': self._name,
            'res_id': self.id,
            'res_name': self.ma_giao_hang,
            'email_to': email_to or '',
            'email_from': self.env.user.email_formatted or self.env.company.email or '',
            'subject': subject or '',
            'status': status,
            'error_message': error_message,
            'mail_id': mail_id or False,
            'sent_date': fields.Datetime.now(),
        })
