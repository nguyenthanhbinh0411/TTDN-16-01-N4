/** @odoo-module **/

const { Component } = owl;
const { useState, useRef, onMounted } = owl.hooks;

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class ChatbotDialog extends Component {
  setup() {
    this.rpc = useService("rpc");
    this.notification = useService("notification");
    this.actionService = useService("action");

    this.modelOptions = [
      { id: "openai_gpt4o_mini", label: "GPT-4o mini (OpenAI)" },
      { id: "gemini_pro", label: "Gemini 2.0 Flash (Google)" },
    ];

    this.state = useState({
      messages: [],
      inputValue: "",
      isLoading: false,
      isMinimized: false,
      selectedModel: this.modelOptions[0].id,
    });

    this.inputRef = useRef("chatInput");
    this.messagesRef = useRef("chatMessages");

    this.suggestions = [
      "Văn bản nào đang quá hạn xử lý?",
      "Có bao nhiêu văn bản trong tháng này?",
    ];

    onMounted(() => {
      if (this.inputRef.el) {
        this.inputRef.el.focus();
      }
    });
  }

  async sendMessage() {
    const question = this.state.inputValue.trim();
    if (!question || this.state.isLoading) return;

    this.state.messages.push({
      type: "user",
      content: question,
      time: this._formatTime(new Date()),
    });

    this.state.inputValue = "";
    this.state.isLoading = true;
    this._scrollToBottom();

    try {
      const result = await this.rpc("/qlvb/chatbot/ask", {
        question: question,
        model_key: this.state.selectedModel,
      });

      if (result.success) {
        this.state.messages.push({
          type: "bot",
          content: result.answer,
          time: this._formatTime(new Date()),
        });
      } else {
        this.state.messages.push({
          type: "error",
          content: result.error || "Có lỗi xảy ra, vui lòng thử lại.",
          time: this._formatTime(new Date()),
        });
      }
    } catch (error) {
      console.error("Chatbot error:", error);
      this.state.messages.push({
        type: "error",
        content: "Không thể kết nối đến server. Vui lòng thử lại.",
        time: this._formatTime(new Date()),
      });
    } finally {
      this.state.isLoading = false;
      this._scrollToBottom();
    }
  }

  onInputKeydown(event) {
    // Chỉ cho phép xuống dòng với Shift+Enter, không gửi khi nhấn Enter
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      // Không gọi sendMessage() nữa - chỉ gửi khi nhấn nút
    }
  }

  useSuggestion(suggestion) {
    this.state.inputValue = suggestion;
    this.sendMessage();
  }

  closeDialog() {
    this.actionService.doAction({
      type: "ir.actions.act_window_close",
    });
  }

  toggleMinimize() {
    this.state.isMinimized = !this.state.isMinimized;
  }

  clearHistory() {
    this.state.messages = [];
  }

  onModelChange(ev) {
    this.state.selectedModel = ev.target.value;
  }

  _formatTime(date) {
    return date.toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  _scrollToBottom() {
    setTimeout(() => {
      if (this.messagesRef.el) {
        this.messagesRef.el.scrollTop = this.messagesRef.el.scrollHeight;
      }
    }, 100);
  }
}

ChatbotDialog.template = "quan_ly_van_ban.ChatbotDialog";
ChatbotDialog.components = {};

// Đăng ký client action
registry.category("actions").add("open_chatbot_dialog", ChatbotDialog);
