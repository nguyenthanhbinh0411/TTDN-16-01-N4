# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ThanhToan(models.Model):
    _name = 'thanh_toan'
    _description = 'Quản lý thanh toán'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_thanh_toan'
    _order = 'ngay_thanh_toan desc'

    # Thông tin cơ bản
    ma_thanh_toan = fields.Char("Mã thanh toán", required=True, copy=False, default='New')
    hoa_don_id = fields.Many2one('hoa_don', string="Hóa đơn", required=True, tracking=True, ondelete='cascade')
    khach_hang_id = fields.Many2one('khach_hang', string="Khách hàng", related='hoa_don_id.khach_hang_id', store=True)
    
    # Số tiền
    so_tien = fields.Float("Số tiền thanh toán", required=True, tracking=True)
    don_vi_tien = fields.Selection([
        ('vnd', 'VND'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
    ], string="Đơn vị tiền", default='vnd')
    
    # Ngày thanh toán
    ngay_thanh_toan = fields.Date("Ngày thanh toán", default=fields.Date.today, required=True, tracking=True)
    
    # Hình thức thanh toán
    hinh_thuc = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
        ('vi_dien_tu', 'Ví điện tử'),
        ('the_tin_dung', 'Thẻ tín dụng'),
        ('khac', 'Khác'),
    ], string="Hình thức thanh toán", default='chuyen_khoan', required=True, tracking=True)
    
    # Thông tin ngân hàng (nếu chuyển khoản)
    ten_ngan_hang = fields.Char("Tên ngân hàng")
    so_tai_khoan = fields.Char("Số tài khoản nhận")
    chu_tai_khoan = fields.Char("Chủ tài khoản")
    ma_giao_dich = fields.Char("Mã giao dịch", tracking=True, default='New')
    
    # Trạng thái
    trang_thai = fields.Selection([
        ('cho_xac_nhan', 'Chờ xác nhận'),
        ('da_xac_nhan', 'Đã xác nhận'),
        ('huy', 'Đã hủy'),
    ], string="Trạng thái", default='cho_xac_nhan', required=True, tracking=True)
    
    # File đính kèm
    file_chung_tu = fields.Binary("File chứng từ")
    file_chung_tu_name = fields.Char("Tên file")
    
    # Người xác nhận
    nguoi_xac_nhan_id = fields.Many2one('res.users', string="Người xác nhận", tracking=True)
    ngay_xac_nhan = fields.Date("Ngày xác nhận", tracking=True)
    
    # Ghi chú
    ghi_chu = fields.Text("Ghi chú")
    
    _sql_constraints = [
        ('ma_thanh_toan_unique', 'unique(ma_thanh_toan)', 'Mã thanh toán phải là duy nhất!')
    ]
    
    @api.model
    def create(self, vals):
        """Tự sinh mã thanh toán khi tạo mới"""
        if vals.get('ma_thanh_toan', 'New') == 'New':
            vals['ma_thanh_toan'] = self.env['ir.sequence'].next_by_code('thanh_toan') or 'New'
        if vals.get('ma_giao_dich', 'New') == 'New':
            vals['ma_giao_dich'] = self.env['ir.sequence'].next_by_code('ma_giao_dich') or 'New'
        return super(ThanhToan, self).create(vals)
    
    def action_xac_nhan(self):
        """Xác nhận thanh toán và tự động cập nhật trạng thái hóa đơn"""
        for record in self:
            if record.trang_thai == 'cho_xac_nhan':
                record.write({
                    'trang_thai': 'da_xac_nhan',
                    'nguoi_xac_nhan_id': self.env.user.id,
                    'ngay_xac_nhan': fields.Date.today(),
                })
                # Tự động cập nhật trạng thái hóa đơn
                record._update_hoa_don_status()
                record._send_xac_nhan_email()

    def _send_xac_nhan_email(self):
        """Gửi email khi xác nhận thanh toán (không dùng mail_templates)"""
        self.ensure_one()
        khach_hang = self.khach_hang_id or self.hoa_don_id.khach_hang_id
        email_to = khach_hang.email if khach_hang else False
        if not email_to:
            self._log_email(
                subject=f"Xác nhận thanh toán - Hóa đơn {self.hoa_don_id.so_hoa_don}",
                email_to=email_to,
                status='failed',
                error_message='Khách hàng chưa có email',
            )
            return False

        email_from = self.env.user.email_formatted or self.env.company.email or 'no-reply@example.com'
        subject = f"Xác nhận thanh toán - Hóa đơn {self.hoa_don_id.so_hoa_don}"
        ngay_tt = self.ngay_thanh_toan.strftime('%d/%m/%Y') if self.ngay_thanh_toan else 'Chưa xác định'

        body_html = f"""
            <p>Xin chào {khach_hang.ten_khach_hang or ''},</p>
            <p>Thanh toán của bạn đã được xác nhận.</p>
            <p><strong>Thông tin thanh toán:</strong></p>
            <ul>
                <li>Mã thanh toán: <strong>{self.ma_thanh_toan}</strong></li>
                <li>Mã giao dịch: <strong>{self.ma_giao_dich or 'Chưa có'}</strong></li>
                <li>Hóa đơn: <strong>{self.hoa_don_id.so_hoa_don}</strong></li>
                <li>Số tiền: <strong>{self.so_tien}</strong></li>
                <li>Ngày thanh toán: {ngay_tt}</li>
                <li>Hình thức: {dict(self._fields['hinh_thuc'].selection).get(self.hinh_thuc, '')}</li>
            </ul>
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
    
    def _update_hoa_don_status(self):
        """Cập nhật trạng thái hóa đơn dựa trên tình trạng thanh toán"""
        self.ensure_one()
        hoa_don = self.hoa_don_id
        
        # Tính tổng số tiền đã thanh toán cho hóa đơn này
        tong_da_thanh_toan = sum(hoa_don.thanh_toan_ids.filtered(
            lambda t: t.trang_thai == 'da_xac_nhan'
        ).mapped('so_tien'))
        
        # Cập nhật tổng đã thanh toán
        hoa_don.tong_da_thanh_toan = tong_da_thanh_toan
        
        # Kiểm tra nếu hóa đơn đã được thanh toán đầy đủ
        if tong_da_thanh_toan >= hoa_don.tong_thanh_toan:
            # Chuyển trạng thái thành đã thanh toán và còn nợ về 0
            hoa_don.write({
                'trang_thai': 'da_thanh_toan',
                'con_no': 0.0
            })
            hoa_don.message_post(body=f"Hóa đơn đã được thanh toán đầy đủ. Tổng thanh toán: {tong_da_thanh_toan}")
        else:
            hoa_don.message_post(body=f"Đã thanh toán {tong_da_thanh_toan}, còn nợ {hoa_don.con_no}")
    
    def action_huy(self):
        """Hủy thanh toán"""
        for record in self:
            if record.trang_thai == 'cho_xac_nhan':
                record.trang_thai = 'huy'

    def _log_email(self, subject, email_to, status='sent', error_message=None, mail_id=None):
        model_exists = self.env['ir.model'].sudo().search([('model', '=', 'qlvb.email.log')], limit=1)
        if not model_exists:
            return
        if mail_id and not self.env['mail.mail'].sudo().browse(mail_id).exists():
            mail_id = False
        self.env['qlvb.email.log'].sudo().create({
            'name': f"{self.ma_thanh_toan or self.id} - {subject}" if subject else f"{self.ma_thanh_toan or self.id}",
            'model_name': self._name,
            'res_id': self.id,
            'res_name': self.ma_thanh_toan,
            'email_to': email_to or '',
            'email_from': self.env.user.email_formatted or self.env.company.email or '',
            'subject': subject or '',
            'status': status,
            'error_message': error_message,
            'mail_id': mail_id or False,
            'sent_date': fields.Datetime.now(),
        })
