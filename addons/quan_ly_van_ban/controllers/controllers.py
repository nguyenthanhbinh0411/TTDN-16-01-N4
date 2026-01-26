# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ChatbotController(http.Controller):
    """Controller cho AI trợ lý nội bộ."""

    @http.route('/qlvb/chatbot/models', type='json', auth='user', methods=['GET'], csrf=False)
    def get_available_models(self, **kwargs):
        """
        Endpoint trả về danh sách models AI có sẵn.
        
        Response:
            {"success": true, "models": [{"id": "...", "label": "...", "provider": "..."}]}
        """
        try:
            chatbot_service = request.env['chatbot.service'].sudo()
            models = []
            for key, config in chatbot_service.SUPPORTED_MODELS.items():
                models.append({
                    'id': key,
                    'label': config['label'],
                    'provider': config['provider'],
                })
            return {'success': True, 'models': models}
        except Exception as e:
            _logger.exception("Get models error: %s", str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qlvb/chatbot/ask', type='json', auth='user', methods=['POST'], csrf=True)
    def chatbot_ask(self, question=None, model_key=None, **kwargs):
        """
        Endpoint nhận câu hỏi từ chatbot và trả về câu trả lời.
        
        Request body:
            {"jsonrpc": "2.0", "method": "call", "params": {"question": "..."}}
        
        Response:
            {"success": true, "answer": "..."} hoặc
            {"success": false, "error": "..."}
        """
        if not question:
            return {'success': False, 'error': 'Vui lòng nhập câu hỏi.'}
        
        # Kiểm tra quyền người dùng (có thể mở rộng theo nhóm)
        user = request.env.user
        if not user or user._is_public():
            return {'success': False, 'error': 'Bạn cần đăng nhập để sử dụng chatbot.'}
        
        # Gọi service xử lý
        try:
            chatbot_service = request.env['chatbot.service'].sudo()
            result = chatbot_service.ask(question, model_key=model_key)
            return result
        except Exception as e:
            _logger.exception("Chatbot controller error: %s", str(e))
            return {'success': False, 'error': f'Lỗi hệ thống: {str(e)}'}
