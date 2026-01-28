# -*- coding: utf-8 -*-
import os
import json
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, api

_logger = logging.getLogger(__name__)


class ChatbotService(models.AbstractModel):
    """Service trợ lý AI nội bộ - truy vấn dữ liệu ERP và gọi OpenAI."""
    _name = 'chatbot.service'
    _description = 'Chatbot AI Service'

    # Danh sách model AI được hỗ trợ cùng metadata
    SUPPORTED_MODELS = {
        'openai_gpt4o_mini': {
            'provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'label': 'GPT-4o mini (OpenAI)',
        },
        'gemini_pro': {
            'provider': 'gemini',
            'model_name': 'gemini-2.0-flash-001',
            'label': 'Gemini 2.0 Flash (Google)',
        },
    }
    DEFAULT_MODEL_KEY = 'openai_gpt4o_mini'

    def _load_env_key(self, env_key):
        """Đọc file .env thủ công khi biến môi trường chưa có."""
        # Đưa về root dự án (…/Business-Internship/.env)
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        env_path = os.path.join(base_dir, '.env')
        if not os.path.isfile(env_path):
            _logger.info(".env not found at %s", env_path)
            return None
        try:
            with open(env_path, 'r', encoding='utf-8') as env_file:
                for line in env_file:
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.strip().split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == env_key and val:
                        # Cache vào process env để lần sau dùng luôn
                        os.environ.setdefault(env_key, val)
                        _logger.info("Loaded %s from .env", env_key)
                        return val
        except Exception as exc:  # pragma: no cover
            _logger.warning("Không thể đọc .env: %s", exc)
        return None

    @api.model
    def _get_api_key(self, provider):
        """Đọc API key tương ứng từng provider."""
        provider_map = {
            'openai': ('OPENAI_API_KEY', 'openai.api_key'),
            'gemini': ('GEMINI_API_KEY', 'gemini.api_key'),
        }

        env_key, config_key = provider_map.get(provider, (None, None))
        if not env_key:
            raise ValueError(f"Provider không được hỗ trợ: {provider}")

        # Thử đọc từ environment variable
        api_key = os.getenv(env_key, '')
        if api_key:
            _logger.info("Loaded %s from environment variable", env_key)
            return api_key
            
        # Thử đọc từ file .env
        api_key = self._load_env_key(env_key) or ''
        if api_key:
            _logger.info("Loaded %s from .env file", env_key)
            return api_key
            
        # Thử đọc từ ir.config_parameter
        if config_key:
            api_key = self.env['ir.config_parameter'].sudo().get_param(config_key, '')
            if api_key:
                _logger.info("Loaded %s from ir.config_parameter", env_key)
                return api_key
                
        _logger.error(
            "%s missing: set in environment, .env, hoặc ir.config_parameter(%s)",
            env_key,
            config_key,
        )
        return api_key

    @api.model
    def query_documents(self, question):
        """
        Truy vấn dữ liệu ERP dựa trên câu hỏi.
        Trả về dict chứa context data cho AI.
        """
        user = self.env.user
        today = date.today()
        first_day_of_month = today.replace(day=1)

        context_data = {
            'user_name': user.name,
            'today': str(today),
            'month': today.strftime('%m/%Y'),
        }

        question_lower = question.lower()

        # --- Văn bản quá hạn xử lý ---
        if 'quá hạn' in question_lower or 'qua han' in question_lower:
            overdue_docs = self._get_overdue_documents()
            context_data['overdue_documents'] = overdue_docs

        # --- Văn bản trong tháng này ---
        if 'tháng này' in question_lower or 'thang nay' in question_lower or 'trong tháng' in question_lower:
            monthly_docs = self._get_monthly_documents(first_day_of_month, today)
            context_data['monthly_documents'] = monthly_docs

        # --- Văn bản theo khách hàng ---
        customer_name = self._extract_customer_name(question)
        if customer_name:
            customer_docs = self._get_customer_documents(customer_name, first_day_of_month, today)
            context_data['customer_documents'] = customer_docs
            context_data['customer_query'] = customer_name

        # --- Hợp đồng ---
        if 'hợp đồng' in question_lower or 'hop dong' in question_lower:
            contracts = self._get_contracts()
            context_data['contracts'] = contracts

        # --- Báo giá ---
        if 'báo giá' in question_lower or 'bao gia' in question_lower:
            quotes = self._get_quotes()
            context_data['quotes'] = quotes

        # --- Nhân viên ---
        if ('nhân viên' in question_lower
                or 'nhan vien' in question_lower
                or 'nhân sự' in question_lower
                or 'nhan su' in question_lower
                or 'employee' in question_lower):
            employees = self._get_employees()
            context_data['employees'] = employees

        # --- Yêu cầu khách hàng ---
        if 'yêu cầu' in question_lower or 'yeu cau' in question_lower:
            customer_requests = self._get_customer_requests()
            context_data['customer_requests'] = customer_requests

        # --- Cơ hội / lead ---
        if 'cơ hội' in question_lower or 'co hoi' in question_lower or 'lead' in question_lower:
            context_data['opportunities'] = self._get_opportunities()

        # --- Đơn hàng / sales order ---
        if 'đơn hàng' in question_lower or 'don hang' in question_lower or 'order' in question_lower:
            context_data['orders'] = self._get_orders()

        # --- Hóa đơn / invoice ---
        if 'hóa đơn' in question_lower or 'hoa don' in question_lower or 'invoice' in question_lower:
            context_data['invoices'] = self._get_invoices()

        # --- Giao hàng / delivery ---
        if 'giao hàng' in question_lower or 'giao hang' in question_lower or 'delivery' in question_lower:
            context_data['deliveries'] = self._get_deliveries()

        # --- Thanh toán / payment ---
        if 'thanh toán' in question_lower or 'thanh toan' in question_lower or 'payment' in question_lower:
            context_data['payments'] = self._get_payments()

        # --- Loyalty / điểm thưởng ---
        if 'điểm thưởng' in question_lower or 'diem thuong' in question_lower or 'loyalty' in question_lower:
            context_data['loyalty_programs'] = self._get_loyalty_programs()

        # --- Tương tác khách hàng ---
        if 'tương tác' in question_lower or 'tuong tac' in question_lower or 'log call' in question_lower or 'cuộc gọi' in question_lower or 'call' in question_lower:
            context_data['interactions'] = self._get_customer_interactions()

        # --- Khiếu nại / phản hồi ---
        if 'khiếu nại' in question_lower or 'khieu nai' in question_lower or 'phản hồi' in question_lower or 'phan hoi' in question_lower or 'complaint' in question_lower:
            context_data['complaints'] = self._get_complaints()

        # --- Dữ liệu nền tảng (luôn lấy gọn) ---
        context_data['van_ban_den_list'] = self._get_incoming_documents()
        context_data['van_ban_di_list'] = self._get_outgoing_documents()
        context_data['khach_hang_list'] = self._get_customers()
        context_data['tai_lieu_list'] = self._get_files()
        context_data['don_vi_list'] = self._get_units()
        context_data['chuc_vu_list'] = self._get_positions()
        context_data['lich_su_cong_tac_list'] = self._get_employee_careers()
        context_data['chung_chi_list'] = self._get_certificates()
        context_data['chung_chi_nv_list'] = self._get_certificate_assignments()

        # --- Thống kê tổng quan (luôn có) ---
        context_data['statistics'] = self._get_statistics()

        return context_data

    @api.model
    def _get_overdue_documents(self):
        """Lấy danh sách văn bản đến đang quá hạn xử lý."""
        VanBanDen = self.env['van_ban_den']
        today = date.today()
        
        # Tìm văn bản có hạn xử lý < hôm nay và chưa xử lý xong
        overdue = VanBanDen.search([
            ('han_xu_ly', '<', today),
            ('trang_thai', 'not in', ['da_xu_ly', 'chuyen_tiep'])
        ], limit=50)
        
        result = []
        for doc in overdue:
            result.append({
                'so_ky_hieu': doc.so_ky_hieu,
                'trich_yeu': doc.trich_yeu[:100] if doc.trich_yeu else '',
                'han_xu_ly': str(doc.han_xu_ly) if doc.han_xu_ly else '',
                'nguoi_xu_ly': (getattr(doc.nguoi_xu_ly_id, 'ho_va_ten', '') or getattr(doc.nguoi_xu_ly_id, 'ho_ten', '')) if doc.nguoi_xu_ly_id else 'Chưa phân công',
                'khach_hang': doc.khach_hang_id.ten_khach_hang if doc.khach_hang_id else '',
                'so_ngay_qua_han': (today - doc.han_xu_ly).days if doc.han_xu_ly else 0,
            })
        return result

    @api.model
    def _get_monthly_documents(self, start_date, end_date):
        """Lấy danh sách văn bản trong khoảng thời gian."""
        VanBanDen = self.env['van_ban_den']
        VanBanDi = self.env['van_ban_di']
        
        # Văn bản đến
        vb_den = VanBanDen.search([
            ('ngay_den', '>=', start_date),
            ('ngay_den', '<=', end_date),
        ], limit=30)
        
        # Văn bản đi
        vb_di = VanBanDi.search([
            ('ngay_van_ban', '>=', start_date),
            ('ngay_van_ban', '<=', end_date),
        ], limit=30)
        
        return {
            'van_ban_den': [{
                'so_ky_hieu': d.so_ky_hieu,
                'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                'ngay_den': str(d.ngay_den),
                'trang_thai': dict(d._fields['trang_thai'].selection).get(d.trang_thai, d.trang_thai),
                'khach_hang': d.khach_hang_id.ten_khach_hang if d.khach_hang_id else '',
            } for d in vb_den],
            'van_ban_di': [{
                'so_ky_hieu': d.so_ky_hieu,
                'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                'ngay_van_ban': str(d.ngay_van_ban),
                'trang_thai': dict(d._fields['trang_thai'].selection).get(d.trang_thai, d.trang_thai),
            } for d in vb_di],
            'total_den': len(vb_den),
            'total_di': len(vb_di),
        }

    @api.model
    def _get_customer_documents(self, customer_name, start_date, end_date):
        """Lấy văn bản của khách hàng theo tên (tìm gần đúng)."""
        KhachHang = self.env['khach_hang']
        VanBanDen = self.env['van_ban_den']
        
        # Tìm khách hàng theo tên (ilike)
        customers = KhachHang.search([
            ('ten_khach_hang', 'ilike', customer_name)
        ], limit=5)
        
        if not customers:
            return {'found': False, 'customer_name': customer_name, 'documents': []}
        
        # Lấy văn bản của các khách hàng tìm được
        docs = VanBanDen.search([
            ('khach_hang_id', 'in', customers.ids),
            ('ngay_den', '>=', start_date),
            ('ngay_den', '<=', end_date),
        ], limit=30)
        
        return {
            'found': True,
            'customers': [{'id': c.id, 'name': c.ten_khach_hang} for c in customers],
            'documents': [{
                'so_ky_hieu': d.so_ky_hieu,
                'trich_yeu': d.trich_yeu[:80] if d.trich_yeu else '',
                'ngay_den': str(d.ngay_den),
                'trang_thai': dict(d._fields['trang_thai'].selection).get(d.trang_thai, d.trang_thai),
                'khach_hang': d.khach_hang_id.ten_khach_hang if d.khach_hang_id else '',
            } for d in docs],
            'total': len(docs),
        }

    @api.model
    def _extract_customer_name(self, question):
        """Trích xuất tên khách hàng từ câu hỏi."""
        # Các pattern phổ biến
        patterns = [
            'khách hàng ',
            'khach hang ',
            'của ',
            'cho ',
            'công ty ',
            'cong ty ',
        ]
        
        question_lower = question.lower()
        for pattern in patterns:
            if pattern in question_lower:
                idx = question_lower.find(pattern) + len(pattern)
                # Lấy phần còn lại sau pattern
                rest = question[idx:].strip()
                # Loại bỏ các từ không cần thiết ở cuối
                for stop_word in [' có ', ' trong ', ' tháng ', ' năm ', ' đang ', ' là ', '?', '.']:
                    if stop_word in rest.lower():
                        rest = rest[:rest.lower().find(stop_word)]
                if rest and len(rest) > 1:
                    return rest.strip()
        return None

    @api.model
    def _get_statistics(self):
        """Thống kê tổng quan văn bản."""
        VanBanDen = self.env['van_ban_den']
        VanBanDi = self.env['van_ban_di']
        today = date.today()
        first_day_of_month = today.replace(day=1)
        
        return {
            'total_van_ban_den': VanBanDen.search_count([]),
            'total_van_ban_di': VanBanDi.search_count([]),
            'van_ban_den_thang_nay': VanBanDen.search_count([
                ('ngay_den', '>=', first_day_of_month),
                ('ngay_den', '<=', today),
            ]),
            'van_ban_di_thang_nay': VanBanDi.search_count([
                ('ngay_van_ban', '>=', first_day_of_month),
                ('ngay_van_ban', '<=', today),
            ]),
            'qua_han': VanBanDen.search_count([
                ('han_xu_ly', '<', today),
                ('trang_thai', 'not in', ['da_xu_ly', 'chuyen_tiep'])
            ]),
            'dang_xu_ly': VanBanDen.search_count([
                ('trang_thai', '=', 'dang_xu_ly')
            ]),
        }

    # --- DỮ LIỆU BỔ SUNG ---
    @api.model
    def _get_incoming_documents(self, limit=20):
        try:
            VanBanDen = self.env['van_ban_den']
            records = VanBanDen.search([], limit=limit, order='ngay_den desc')
            return [{
                'so_ky_hieu': r.so_ky_hieu,
                'trich_yeu': (r.trich_yeu or '')[:160],
                'ngay_den': str(r.ngay_den) if r.ngay_den else '',
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'nguoi_ky': getattr(r, 'nguoi_ky', ''),
                'nguoi_gui': getattr(r, 'nguoi_gui', ''),
                'so_luong_taptin': len(r.attachment_ids) if hasattr(r, 'attachment_ids') else 0,
                'so_hop_dong_lien_quan': getattr(r.hop_dong_id, 'ten_hop_dong', '') if getattr(r, 'hop_dong_id', False) else '',
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai) if 'trang_thai' in r._fields else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn văn bản đến: %s", str(e))
            return []

    @api.model
    def _get_outgoing_documents(self, limit=20):
        try:
            VanBanDi = self.env['van_ban_di']
            records = VanBanDi.search([], limit=limit, order='ngay_van_ban desc')
            return [{
                'so_ky_hieu': r.so_ky_hieu,
                'trich_yeu': (r.trich_yeu or '')[:160],
                'ngay_van_ban': str(r.ngay_van_ban) if r.ngay_van_ban else '',
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'nguoi_xu_ly': (getattr(r.nguoi_xu_ly_id, 'ho_va_ten', '') or getattr(r.nguoi_xu_ly_id, 'ho_ten', '')) if getattr(r, 'nguoi_xu_ly_id', False) else '',
                'so_luong_taptin': len(r.attachment_ids) if hasattr(r, 'attachment_ids') else 0,
                'reference': str(getattr(r, 'reference', '') or ''),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai) if 'trang_thai' in r._fields else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn văn bản đi: %s", str(e))
            return []

    @api.model
    def _get_customers(self, limit=20):
        try:
            KhachHang = self.env['khach_hang']
            records = KhachHang.search([], limit=limit, order='create_date desc')
            return [{
                'ten_khach_hang': r.ten_khach_hang,
                'ma_so_thue': getattr(r, 'ma_so_thue', ''),
                'dien_thoai': getattr(r, 'dien_thoai', ''),
                'email': getattr(r, 'email', ''),
                'dia_chi': getattr(r, 'dia_chi', ''),
                'nguoi_lien_he': getattr(r, 'nguoi_lien_he', ''),
                'website': getattr(r, 'website', ''),
                'fax': getattr(r, 'fax', ''),
                'ghi_chu': getattr(r, 'ghi_chu', ''),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn khách hàng: %s", str(e))
            return []

    @api.model
    def _get_files(self, limit=20):
        try:
            TaiLieu = self.env['tai_lieu']
            records = TaiLieu.search([], limit=limit, order='ngay_tao desc')
            return [{
                'ma_tai_lieu': r.ma_tai_lieu,
                'ten_tai_lieu': r.ten_tai_lieu,
                'loai_tai_lieu': r.loai_tai_lieu,
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'hop_dong': r.hop_dong_id.ten_hop_dong if r.hop_dong_id else '',
                'nguoi_upload': getattr(r, 'nguoi_upload', ''),
                'loai_file': getattr(r, 'loai_file', ''),
                'mo_ta': (getattr(r, 'mo_ta', '') or '')[:200],
                'ngay_tao': str(r.ngay_tao) if r.ngay_tao else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn tài liệu: %s", str(e))
            return []

    @api.model
    def _get_units(self, limit=20):
        try:
            DonVi = self.env['don_vi']
            records = DonVi.search([], limit=limit, order='ten_don_vi asc')
            return [{
                'ma_don_vi': r.ma_don_vi,
                'ten_don_vi': r.ten_don_vi,
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn đơn vị: %s", str(e))
            return []

    @api.model
    def _get_positions(self, limit=20):
        try:
            ChucVu = self.env['chuc_vu']
            records = ChucVu.search([], limit=limit, order='ten_chuc_vu asc')
            return [{
                'ma_chuc_vu': r.ma_chuc_vu,
                'ten_chuc_vu': r.ten_chuc_vu,
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn chức vụ: %s", str(e))
            return []

    @api.model
    def _get_employee_careers(self, limit=20):
        try:
            LichSu = self.env['lich_su_cong_tac']
            records = LichSu.search([], limit=limit, order='id desc')
            return [{
                'nhan_vien': r.nhan_vien_id.ho_va_ten if hasattr(r.nhan_vien_id, 'ho_va_ten') else '',
                'chuc_vu': r.chuc_vu_id.ten_chuc_vu if r.chuc_vu_id else '',
                'don_vi': r.don_vi_id.ten_don_vi if r.don_vi_id else '',
                'loai_chuc_vu': r.loai_chuc_vu,
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn lịch sử công tác: %s", str(e))
            return []

    @api.model
    def _get_certificates(self, limit=20):
        try:
            ChungChi = self.env['chung_chi_bang_cap']
            records = ChungChi.search([], limit=limit, order='ten_chung_chi_bang_cap asc')
            return [{
                'ma_chung_chi': r.ma_chung_chi_bang_cap,
                'ten_chung_chi': r.ten_chung_chi_bang_cap,
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn chứng chỉ: %s", str(e))
            return []

    @api.model
    def _get_certificate_assignments(self, limit=20):
        try:
            Assign = self.env['danh_sach_chung_chi_bang_cap']
            records = Assign.search([], limit=limit, order='id desc')
            return [{
                'nhan_vien': r.nhan_vien_id.ho_va_ten if hasattr(r.nhan_vien_id, 'ho_va_ten') else '',
                'chung_chi': r.chung_chi_bang_cap_id.ten_chung_chi_bang_cap if r.chung_chi_bang_cap_id else '',
                'ghi_chu': r.ghi_chu,
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn chứng chỉ nhân viên: %s", str(e))
            return []

    @api.model
    def _get_contracts(self):
        """Lấy danh sách hợp đồng."""
        try:
            HopDong = self.env['hop_dong']
            contracts = HopDong.search([], limit=20)
            return [{
                'so_hop_dong': c.so_hop_dong,
                'ten_hop_dong': c.ten_hop_dong,
                'khach_hang': c.khach_hang_id.ten_khach_hang if c.khach_hang_id else '',
                'ngay_ky': str(c.ngay_ky) if c.ngay_ky else '',
                'ngay_bat_dau': str(getattr(c, 'ngay_bat_dau', '')),
                'ngay_ket_thuc': str(getattr(c, 'ngay_ket_thuc', '')),
                'tong_gia_tri': getattr(c, 'tong_gia_tri', None),
                'don_vi_tien': getattr(c, 'don_vi_tien', ''),
                'dai_dien_ky': getattr(c, 'dai_dien_ky', ''),
                'trang_thai': dict(c._fields['trang_thai'].selection).get(c.trang_thai, c.trang_thai) if 'trang_thai' in c._fields else '',
                'ghi_chu': getattr(c, 'ghi_chu', ''),
            } for c in contracts]
        except Exception as e:
            _logger.warning("Không thể truy vấn hợp đồng: %s", str(e))
            return []

    @api.model
    def _get_quotes(self):
        """Lấy danh sách báo giá."""
        try:
            BaoGia = self.env['bao_gia']
            quotes = BaoGia.search([], limit=20)
            return [{
                'so_bao_gia': q.so_bao_gia,
                'ten_bao_gia': q.ten_bao_gia,
                'khach_hang': q.khach_hang_id.ten_khach_hang if q.khach_hang_id else '',
                'ngay_bao_gia': str(q.ngay_bao_gia) if q.ngay_bao_gia else '',
                'nguoi_lien_he': getattr(q, 'nguoi_lien_he', ''),
                'tong_tien': getattr(q, 'tong_tien', None),
                'don_vi_tien': getattr(q, 'don_vi_tien', ''),
                'trang_thai': dict(q._fields['trang_thai'].selection).get(q.trang_thai, q.trang_thai) if 'trang_thai' in q._fields else '',
                'ghi_chu': getattr(q, 'ghi_chu', ''),
            } for q in quotes]
        except Exception as e:
            _logger.warning("Không thể truy vấn báo giá: %s", str(e))
            return []

    @api.model
    def _get_opportunities(self, limit=20):
        try:
            Opp = self.env['co_hoi_ban_hang']
            records = Opp.search([], limit=limit, order='ngay_tao desc')
            return [{
                'ma_co_hoi': r.ma_co_hoi,
                'ten_co_hoi': r.ten_co_hoi,
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'giai_doan': dict(r._fields['giai_doan'].selection).get(r.giai_doan, r.giai_doan),
                'gia_tri_du_kien': getattr(r, 'gia_tri_du_kien', None),
                'don_vi_tien': getattr(r, 'don_vi_tien', ''),
                'ty_le_thanh_cong': getattr(r, 'ty_le_thanh_cong', None),
                'ngay_du_kien_chot': str(getattr(r, 'ngay_du_kien_chot', '')),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn cơ hội: %s", str(e))
            return []

    @api.model
    def _get_orders(self, limit=20):
        try:
            Order = self.env['don_hang']
            records = Order.search([], limit=limit, order='ngay_dat desc')
            return [{
                'ma_don_hang': r.ma_don_hang,
                'ten_don_hang': r.ten_don_hang,
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'tong_gia_tri': getattr(r, 'tong_gia_tri', None),
                'don_vi_tien': getattr(r, 'don_vi_tien', ''),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai),
                'ngay_dat': str(r.ngay_dat) if r.ngay_dat else '',
                'ngay_hoan_thanh': str(getattr(r, 'ngay_hoan_thanh', '')),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn đơn hàng: %s", str(e))
            return []

    @api.model
    def _get_invoices(self, limit=20):
        try:
            Invoice = self.env['hoa_don']
            records = Invoice.search([], limit=limit, order='ngay_xuat desc')
            return [{
                'so_hoa_don': r.so_hoa_don,
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'don_hang': r.don_hang_id.ten_don_hang if r.don_hang_id else '',
                'tong_thanh_toan': getattr(r, 'tong_thanh_toan', None),
                'con_no': getattr(r, 'con_no', None),
                'han_thanh_toan': str(getattr(r, 'han_thanh_toan', '')),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn hóa đơn: %s", str(e))
            return []

    @api.model
    def _get_deliveries(self, limit=20):
        try:
            Delivery = self.env['giao_hang']
            order_field = 'ngay_giao desc' if 'ngay_giao' in Delivery._fields else 'id desc'
            records = Delivery.search([], limit=limit, order=order_field)
            return [{
                'ma_giao_hang': getattr(r, 'ma_giao_hang', ''),
                'don_hang': r.don_hang_id.ten_don_hang if r.don_hang_id else '',
                'khach_hang': r.don_hang_id.khach_hang_id.ten_khach_hang if r.don_hang_id and r.don_hang_id.khach_hang_id else '',
                'ngay_giao': str(getattr(r, 'ngay_giao', '')),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai) if 'trang_thai' in r._fields else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn giao hàng: %s", str(e))
            return []

    @api.model
    def _get_payments(self, limit=20):
        try:
            Payment = self.env['thanh_toan']
            order_field = 'ngay_thanh_toan desc' if 'ngay_thanh_toan' in Payment._fields else 'id desc'
            records = Payment.search([], limit=limit, order=order_field)
            return [{
                'ma_thanh_toan': getattr(r, 'ma_thanh_toan', ''),
                'hoa_don': r.hoa_don_id.so_hoa_don if r.hoa_don_id else '',
                'khach_hang': r.hoa_don_id.khach_hang_id.ten_khach_hang if r.hoa_don_id and r.hoa_don_id.khach_hang_id else '',
                'so_tien': getattr(r, 'so_tien', None),
                'phuong_thuc': getattr(r, 'phuong_thuc', ''),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai) if 'trang_thai' in r._fields else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn thanh toán: %s", str(e))
            return []

    @api.model
    def _get_loyalty_programs(self, limit=20):
        try:
            Loyalty = self.env['chuong_trinh_khach_hang_than_thiet']
            records = Loyalty.search([], limit=limit, order='id desc')
            return [{
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'tong_diem': getattr(r, 'tong_diem', None),
                'cap_do': getattr(r, 'cap_do', ''),
                'han_muc_tich_diem': getattr(r, 'han_muc_tich_diem', None),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn loyalty: %s", str(e))
            return []

    @api.model
    def _get_customer_interactions(self, limit=20):
        try:
            Interact = self.env['lich_su_tuong_tac']
            order_field = 'ngay_tuong_tac desc' if 'ngay_tuong_tac' in Interact._fields else 'id desc'
            records = Interact.search([], limit=limit, order=order_field)
            return [{
                'tieu_de': getattr(r, 'tieu_de', ''),
                'khach_hang': r.khach_hang_id.ten_khach_hang if hasattr(r, 'khach_hang_id') and r.khach_hang_id else '',
                'loai': getattr(r, 'loai_tuong_tac', ''),
                'ngay': str(getattr(r, 'ngay_tuong_tac', '')),
                'nguoi_phu_trach': (getattr(r.nhan_vien_id, 'ho_va_ten', '') or getattr(r.nhan_vien_id, 'ho_ten', '')) if hasattr(r, 'nhan_vien_id') and r.nhan_vien_id else '',
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn lịch sử tương tác: %s", str(e))
            return []

    @api.model
    def _get_complaints(self, limit=20):
        try:
            Complaint = self.env['khieu_nai_phan_hoi']
            records = Complaint.search([], limit=limit, order='create_date desc')
            return [{
                'tieu_de': getattr(r, 'tieu_de', ''),
                'khach_hang': r.khach_hang_id.ten_khach_hang if hasattr(r, 'khach_hang_id') and r.khach_hang_id else '',
                'loai': getattr(r, 'loai', ''),
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai) if 'trang_thai' in r._fields else '',
                'muc_do': getattr(r, 'muc_do', ''),
            } for r in records]
        except Exception as e:
            _logger.warning("Không thể truy vấn khiếu nại/phan hồi: %s", str(e))
            return []

    @api.model
    def _get_employees(self, limit=50):
        """Lấy danh sách nhân viên từ module nhan_su (field mapping đúng)."""
        try:
            NhanVien = self.env['nhan_vien']
            employees = NhanVien.search([], limit=limit, order='chuc_vu_cap_do asc, ten asc')
            return [{
                'ma_dinh_danh': e.ma_dinh_danh,
                'ho_va_ten': e.ho_va_ten,
                'ten': e.ten,
                'don_vi': e.don_vi_hien_tai.ten_don_vi if e.don_vi_hien_tai else '',
                'chuc_vu': e.chuc_vu_hien_tai.ten_chuc_vu if e.chuc_vu_hien_tai else '',
                'chuc_vu_cap_do': e.chuc_vu_cap_do,
                'tuoi': e.tuoi,
                'email': e.email,
                'so_dien_thoai': e.so_dien_thoai,
                'que_quan': e.que_quan,
                'luong_co_ban': e.luong_co_ban,
                'user': e.user_id.name if e.user_id else '',
                'so_chung_chi': len(e.danh_sach_chung_chi_bang_cap_ids),
                'so_nguoi_bang_tuoi': e.so_nguoi_bang_tuoi,
            } for e in employees]
        except Exception as e:
            _logger.warning("Không thể truy vấn nhân viên: %s", str(e))
            return []

    @api.model
    def _get_customer_requests(self):
        """Lấy danh sách yêu cầu khách hàng."""
        try:
            YeuCauKhachHang = self.env['yeu_cau_khach_hang']
            requests = YeuCauKhachHang.search([], limit=20)
            return [{
                'tieu_de': r.tieu_de,
                'noi_dung': r.noi_dung[:100] if r.noi_dung else '',
                'khach_hang': r.khach_hang_id.ten_khach_hang if r.khach_hang_id else '',
                'ngay_tao': str(r.create_date.date()) if r.create_date else '',
                'trang_thai': dict(r._fields['trang_thai'].selection).get(r.trang_thai, r.trang_thai),
            } for r in requests]
        except Exception as e:
            _logger.warning("Không thể truy vấn yêu cầu khách hàng: %s", str(e))
            return []

    @api.model
    def ask(self, question, model_key=None, session_id=None, user_id=None):
        """
        Xử lý câu hỏi từ người dùng:
        1. Truy vấn dữ liệu ERP
        2. Tạo prompt với context
        3. Gọi OpenAI API
        4. Trả về câu trả lời
        5. Lưu lịch sử chat
        """
        if not question or not question.strip():
            return {'success': False, 'error': 'Vui lòng nhập câu hỏi.'}
        
        # Tạo session_id nếu chưa có
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Lưu tin nhắn của user
        self._save_chat_message(session_id, question, is_bot=False, user_id=user_id)
        
        # Xác định model sẽ dùng
        selected_key = model_key or self.DEFAULT_MODEL_KEY
        model_config = self.SUPPORTED_MODELS.get(selected_key)
        if not model_config:
            _logger.warning("Model %s không được hỗ trợ, fallback default", selected_key)
            selected_key = self.DEFAULT_MODEL_KEY
            model_config = self.SUPPORTED_MODELS[self.DEFAULT_MODEL_KEY]

        provider = model_config['provider']

        # Lấy API key tương ứng provider
        api_key = self._get_api_key(provider)
        if not api_key:
            error_msg = (
                f'Chưa cấu hình API key cho {model_config["label"]}. '
                f'Vui lòng thêm biến môi trường {provider.upper()}_API_KEY '
                f'hoặc liên hệ quản trị viên để cấu hình.'
            )
            _logger.warning(error_msg)
            # Lưu lỗi vào lịch sử
            self._save_chat_message(session_id, error_msg, is_bot=True, message_type='system', user_id=user_id)
            return {
                'success': False,
                'error': error_msg,
            }
        
        try:
            # Truy vấn dữ liệu ERP
            erp_context = self.query_documents(question)
            
            # Tạo prompt
            system_prompt = self._build_system_prompt(erp_context)
            
            # Gọi model tương ứng
            if provider == 'openai':
                answer = self._call_openai(api_key, system_prompt, question, model_config['model_name'])
            elif provider == 'gemini':
                answer = self._call_gemini(
                    api_key,
                    system_prompt,
                    question,
                    model_config['model_name'],
                )
            else:
                raise ValueError(f"Provider không hỗ trợ: {provider}")
            
            # Lưu câu trả lời của bot
            self._save_chat_message(session_id, answer, is_bot=True, user_id=user_id)
            
            # Log cho audit (không log API key)
            _logger.info(
                "Chatbot query by user %s (model=%s): %s",
                self.env.user.login,
                selected_key,
                question[:100]
            )
            
            return {
                'success': True,
                'answer': answer,
                'session_id': session_id,
                'context_summary': {
                    'has_overdue': bool(erp_context.get('overdue_documents')),
                    'has_monthly': bool(erp_context.get('monthly_documents')),
                    'has_customer': bool(erp_context.get('customer_documents')),
                    'has_contracts': bool(erp_context.get('contracts')),
                    'has_quotes': bool(erp_context.get('quotes')),
                    'has_employees': bool(erp_context.get('employees')),
                    'has_customer_requests': bool(erp_context.get('customer_requests')),
                    'model_key': selected_key,
                }
            }
        except Exception as e:
            error_msg = f'Lỗi xử lý: {str(e)}'
            _logger.exception("Chatbot error: %s", str(e))
            # Lưu lỗi vào lịch sử
            self._save_chat_message(session_id, error_msg, is_bot=True, message_type='system', user_id=user_id)
            return {'success': False, 'error': error_msg}

    @api.model
    def process_uploaded_file(self, file_data, file_name, model_key=None, question=None, session_id=None, user_id=None):
        """
        Xử lý file upload từ chatbot:
        1. Trích xuất text từ file (PDF, DOCX, etc.)
        2. Tóm tắt nội dung hoặc trả lời câu hỏi về file
        3. Trả về kết quả
        4. Lưu lịch sử chat
        """
        if not file_data or not file_name:
            return {'success': False, 'error': 'Thiếu dữ liệu file hoặc tên file.'}

        # Tạo session_id nếu chưa có
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Lưu tin nhắn file upload
        file_message = f"Đã upload file: {file_name}"
        if question and question.strip():
            file_message += f" với câu hỏi: {question}"
        self._save_chat_message(
            session_id,
            file_message,
            is_bot=False,
            message_type='file',
            file_name=file_name,
            file_data=file_data,
            user_id=user_id,
        )

        # Xác định model sẽ dùng
        selected_key = model_key or self.DEFAULT_MODEL_KEY
        model_config = self.SUPPORTED_MODELS.get(selected_key)
        if not model_config:
            _logger.warning("Model %s không được hỗ trợ, fallback default", selected_key)
            selected_key = self.DEFAULT_MODEL_KEY
            model_config = self.SUPPORTED_MODELS[self.DEFAULT_MODEL_KEY]

        provider = model_config['provider']

        # Lấy API key tương ứng provider
        api_key = self._get_api_key(provider)
        if not api_key:
            error_msg = (
                f'Chưa cấu hình API key cho {model_config["label"]}. '
                f'Vui lòng thêm biến môi trường {provider.upper()}_API_KEY '
                f'hoặc liên hệ quản trị viên để cấu hình.'
            )
            _logger.warning(error_msg)
            # Lưu lỗi vào lịch sử
            self._save_chat_message(session_id, error_msg, is_bot=True, message_type='system', user_id=user_id)
            return {
                'success': False,
                'error': error_msg,
            }

        try:
            # Trích xuất text từ file
            extracted_text = self._extract_text_from_file(file_data, file_name)
            
            if not extracted_text:
                error_msg = f'Không thể trích xuất text từ file {file_name}. File có thể bị hỏng hoặc không được hỗ trợ.'
                self._save_chat_message(session_id, error_msg, is_bot=True, message_type='system', user_id=user_id)
                return {
                    'success': False,
                    'error': error_msg,
                }

            # Tạo prompt cho AI
            if question and question.strip():
                # Người dùng có câu hỏi cụ thể về file
                system_prompt = f"""Bạn là trợ lý AI thông minh. Người dùng đã upload file "{file_name}" và hỏi: "{question}"

Nội dung file:
{extracted_text[:4000]}  # Giới hạn 4000 ký tự để tránh vượt token limit

Hãy trả lời câu hỏi của người dùng dựa trên nội dung file này. Nếu câu hỏi không liên quan đến file, hãy nói rõ."""
                user_question = question
            else:
                # Không có câu hỏi cụ thể, tóm tắt file
                system_prompt = f"""Bạn là trợ lý AI thông minh. Người dùng đã upload file "{file_name}".

Nội dung file:
{extracted_text[:4000]}  # Giới hạn 4000 ký tự

Hãy tóm tắt nội dung chính của file này một cách ngắn gọn và có cấu trúc."""
                user_question = "Hãy tóm tắt nội dung file này"

            # Gọi model tương ứng
            if provider == 'openai':
                answer = self._call_openai(api_key, system_prompt, user_question, model_config['model_name'])
            elif provider == 'gemini':
                answer = self._call_gemini(
                    api_key,
                    system_prompt,
                    user_question,
                    model_config['model_name'],
                )
            else:
                raise ValueError(f"Provider không hỗ trợ: {provider}")

            # Lưu câu trả lời của bot
            self._save_chat_message(session_id, answer, is_bot=True, user_id=user_id)

            # Log cho audit
            _logger.info(
                "File processing by user %s (model=%s): %s",
                self.env.user.login,
                selected_key,
                file_name
            )

            return {
                'success': True,
                'answer': answer,
                'session_id': session_id,
                'extracted_text': extracted_text[:1000],  # Trả về phần đầu để preview
                'summary': answer,
                'file_name': file_name,
                'file_size': len(file_data) if file_data else 0,
            }

        except Exception as e:
            _logger.exception("File processing error: %s", str(e))
            return {
                'success': False,
                'error': f'Lỗi xử lý file: {str(e)}',
            }

    @api.model
    def _extract_text_from_file(self, file_data, file_name):
        """
        Trích xuất text từ file base64.
        Hỗ trợ: PDF, DOCX, TXT, etc.
        """
        try:
            import base64
            import io
            
            # Decode base64
            file_bytes = base64.b64decode(file_data)
            
            # Xác định loại file từ extension
            file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            
            if file_ext == 'pdf':
                # Trích xuất từ PDF
                try:
                    # Thử import pypdf (thay thế PyPDF2)
                    try:
                        from pypdf import PdfReader
                    except ImportError:
                        from PyPDF2 import PdfReader
                    
                    pdf_file = io.BytesIO(file_bytes)
                    pdf_reader = PdfReader(pdf_file)
                    
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    return text.strip()
                except ImportError:
                    return "Không thể xử lý PDF: thiếu thư viện pypdf hoặc PyPDF2. Vui lòng cài đặt: pip install pypdf"
                except Exception as e:
                    return f"Lỗi xử lý PDF: {str(e)}"
            
            elif file_ext in ['docx', 'doc']:
                # Trích xuất từ DOCX
                try:
                    from docx import Document
                    docx_file = io.BytesIO(file_bytes)
                    doc = Document(docx_file)
                    
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    
                    return text.strip()
                except ImportError:
                    return "Không thể xử lý DOCX: thiếu thư viện python-docx. Vui lòng cài đặt: pip install python-docx"
                except Exception as e:
                    return f"Lỗi xử lý DOCX: {str(e)}"
            
            elif file_ext == 'txt':
                # File text thuần
                try:
                    return file_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return file_bytes.decode('latin-1')
                    except:
                        return "Không thể đọc file text"
            
            else:
                # File không hỗ trợ
                return f"Loại file không được hỗ trợ: {file_ext}. Chỉ hỗ trợ PDF, DOCX, TXT."
                
        except Exception as e:
            _logger.error("Text extraction error: %s", str(e))
            return f"Lỗi trích xuất text: {str(e)}"

    @api.model
    def _build_system_prompt(self, erp_context):
        """Xây dựng system prompt với dữ liệu ERP."""
        prompt = f"""Bạn là trợ lý AI nội bộ của hệ thống quản lý văn bản. 
Hãy trả lời ngắn gọn, chính xác dựa trên dữ liệu ERP được cung cấp.
Nếu không có dữ liệu liên quan, hãy thông báo rõ ràng.
Ngày hôm nay: {erp_context.get('today', '')}
Tháng hiện tại: {erp_context.get('month', '')}
Người dùng: {erp_context.get('user_name', '')}

=== THỐNG KÊ TỔNG QUAN ===
{json.dumps(erp_context.get('statistics', {}), ensure_ascii=False, indent=2)}
"""
        
        if erp_context.get('overdue_documents'):
            prompt += f"""
=== VĂN BẢN QUÁ HẠN ({len(erp_context['overdue_documents'])} văn bản) ===
{json.dumps(erp_context['overdue_documents'], ensure_ascii=False, indent=2)}
"""
        
        if erp_context.get('monthly_documents'):
            monthly = erp_context['monthly_documents']
            prompt += f"""
=== VĂN BẢN THÁNG NÀY ===
Văn bản đến: {monthly.get('total_den', 0)} văn bản
Văn bản đi: {monthly.get('total_di', 0)} văn bản
Chi tiết văn bản đến:
{json.dumps(monthly.get('van_ban_den', [])[:10], ensure_ascii=False, indent=2)}
"""
        
        if erp_context.get('customer_documents'):
            cust = erp_context['customer_documents']
            if cust.get('found'):
                prompt += f"""
=== VĂN BẢN CỦA KHÁCH HÀNG ===
Khách hàng tìm thấy: {[c['name'] for c in cust.get('customers', [])]}
Tổng số văn bản: {cust.get('total', 0)}
Chi tiết:
{json.dumps(cust.get('documents', [])[:10], ensure_ascii=False, indent=2)}
"""
            else:
                prompt += f"""
=== VĂN BẢN CỦA KHÁCH HÀNG ===
Không tìm thấy khách hàng tên "{cust.get('customer_name', '')}" trong hệ thống.
"""

        if erp_context.get('contracts'):
            prompt += f"""
=== HỢP ĐỒNG ({len(erp_context['contracts'])} hợp đồng) ===
{json.dumps(erp_context['contracts'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('quotes'):
            prompt += f"""
=== BÁO GIÁ ({len(erp_context['quotes'])} báo giá) ===
{json.dumps(erp_context['quotes'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('employees'):
            prompt += f"""
=== NHÂN VIÊN ({len(erp_context['employees'])} nhân viên) ===
{json.dumps(erp_context['employees'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('customer_requests'):
            prompt += f"""
=== YÊU CẦU KHÁCH HÀNG ({len(erp_context['customer_requests'])} yêu cầu) ===
{json.dumps(erp_context['customer_requests'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('opportunities'):
            prompt += f"""
=== CƠ HỘI BÁN HÀNG ({len(erp_context['opportunities'])} cơ hội) ===
{json.dumps(erp_context['opportunities'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('orders'):
            prompt += f"""
=== ĐƠN HÀNG ({len(erp_context['orders'])} đơn) ===
{json.dumps(erp_context['orders'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('invoices'):
            prompt += f"""
=== HÓA ĐƠN ({len(erp_context['invoices'])} hóa đơn) ===
{json.dumps(erp_context['invoices'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('deliveries'):
            prompt += f"""
=== GIAO HÀNG ({len(erp_context['deliveries'])} lần) ===
{json.dumps(erp_context['deliveries'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('payments'):
            prompt += f"""
=== THANH TOÁN ({len(erp_context['payments'])} giao dịch) ===
{json.dumps(erp_context['payments'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('loyalty_programs'):
            prompt += f"""
=== KHÁCH HÀNG THÂN THIẾT ({len(erp_context['loyalty_programs'])} bản ghi) ===
{json.dumps(erp_context['loyalty_programs'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('interactions'):
            prompt += f"""
=== LỊCH SỬ TƯƠNG TÁC ({len(erp_context['interactions'])} bản ghi) ===
{json.dumps(erp_context['interactions'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('complaints'):
            prompt += f"""
=== KHIẾU NẠI / PHẢN HỒI ({len(erp_context['complaints'])} bản ghi) ===
{json.dumps(erp_context['complaints'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('van_ban_den_list'):
            prompt += f"""
=== DANH SÁCH VĂN BẢN ĐẾN (top {len(erp_context['van_ban_den_list'])}) ===
{json.dumps(erp_context['van_ban_den_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('van_ban_di_list'):
            prompt += f"""
=== DANH SÁCH VĂN BẢN ĐI (top {len(erp_context['van_ban_di_list'])}) ===
{json.dumps(erp_context['van_ban_di_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('khach_hang_list'):
            prompt += f"""
=== DANH SÁCH KHÁCH HÀNG (top {len(erp_context['khach_hang_list'])}) ===
{json.dumps(erp_context['khach_hang_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('tai_lieu_list'):
            prompt += f"""
=== TÀI LIỆU SỐ HÓA (top {len(erp_context['tai_lieu_list'])}) ===
{json.dumps(erp_context['tai_lieu_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('don_vi_list'):
            prompt += f"""
=== ĐƠN VỊ (top {len(erp_context['don_vi_list'])}) ===
{json.dumps(erp_context['don_vi_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('chuc_vu_list'):
            prompt += f"""
=== CHỨC VỤ (top {len(erp_context['chuc_vu_list'])}) ===
{json.dumps(erp_context['chuc_vu_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('lich_su_cong_tac_list'):
            prompt += f"""
=== LỊCH SỬ CÔNG TÁC (top {len(erp_context['lich_su_cong_tac_list'])}) ===
{json.dumps(erp_context['lich_su_cong_tac_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('chung_chi_list'):
            prompt += f"""
=== CHỨNG CHỈ/BẰNG CẤP (top {len(erp_context['chung_chi_list'])}) ===
{json.dumps(erp_context['chung_chi_list'][:10], ensure_ascii=False, indent=2)}
"""

        if erp_context.get('chung_chi_nv_list'):
            prompt += f"""
=== CHỨNG CHỈ THEO NHÂN VIÊN (top {len(erp_context['chung_chi_nv_list'])}) ===
{json.dumps(erp_context['chung_chi_nv_list'][:10], ensure_ascii=False, indent=2)}
"""

        return prompt

    @api.model
    def _save_chat_message(self, session_id, message, is_bot=False, message_type='text', file_name=None, file_data=None, user_id=None):
        """Lưu tin nhắn vào lịch sử chat"""
        try:
            env = self.env
            if user_id:
                env = env.sudo(user_id)
            return env['chat.history'].create({
                'session_id': session_id,
                'message': message,
                'is_bot': is_bot,
                'message_type': message_type,
                'file_name': file_name,
                'file_data': file_data,
            })
        except Exception as e:
            _logger.error("Không thể lưu lịch sử chat: %s", str(e))
            return False

    @api.model
    def _call_openai(self, api_key, system_prompt, user_question, model_name):
        """Gọi OpenAI Chat Completion API."""
        import urllib.request
        import urllib.error
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            _logger.error("OpenAI API error: %s - %s", e.code, error_body)
            if e.code == 429:
                # Rate limit / quota exceeded
                raise Exception("OpenAI báo quá giới hạn hoặc hết quota. Vui lòng thử lại sau hoặc kiểm tra billing/quota.")
            if e.code == 401:
                raise Exception("API key OpenAI không hợp lệ hoặc bị từ chối (401). Kiểm tra lại khóa.")
            raise Exception(f"Lỗi API OpenAI: {e.code}")
        except urllib.error.URLError as e:
            _logger.error("OpenAI connection error: %s", str(e))
            raise Exception("Không thể kết nối đến OpenAI API")

    def _call_gemini(self, api_key, system_prompt, user_question, model_name):
        """Gọi Google Gemini API sử dụng SDK."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise Exception(
                "Thiếu thư viện google-generativeai. "
                "Cài đặt: pip install google-generativeai"
            )

        try:
            # Cấu hình API key
            genai.configure(api_key=api_key)

            # Khởi tạo model
            model = genai.GenerativeModel(model_name)

            # Tạo prompt đầy đủ
            full_prompt = f"{system_prompt}\n\nCâu hỏi: {user_question}"

            _logger.info("Calling Gemini model: %s", model_name)

            # Gọi API với cấu hình
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )

            # Lấy text từ response
            if not response or not response.text:
                raise Exception("Gemini không trả về nội dung văn bản.")

            return response.text

        except Exception as e:
            error_msg = str(e)
            _logger.error("Gemini SDK error: %s", error_msg)

            # Xử lý các lỗi phổ biến
            if "API_KEY_INVALID" in error_msg or "authentication" in error_msg.lower():
                raise Exception("API key Gemini không hợp lệ. Kiểm tra lại khóa.")
            elif "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
                raise Exception("Gemini báo quá giới hạn hoặc hết quota. Vui lòng thử lại sau.")
            elif "not found" in error_msg.lower() or "404" in error_msg:
                raise Exception(f"Model Gemini không tồn tại: {model_name}. Thử 'gemini-2.0-flash-001' hoặc 'gemini-2.5-flash'.")
            else:
                raise Exception(f"Lỗi Gemini: {error_msg}")
