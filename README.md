<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
    ERP: HỆ THỐNG QUẢN LÝ KHÁCH HÀNG & VĂN BẢN
</h2>
<div align="center">
    <p align="center">
        <img src="docs/logo/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="docs/logo/fitdnu_logo.png" alt="AIoTLab Logo" width="180"/>
        <img src="docs/logo/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

## 📖 1. Giới thiệu
**ERP: HỆ THỐNG QUẢN LÝ KHÁCH HÀNG & VĂN BẢN** là hệ thống quản trị doanh nghiệp được xây dựng trên nền tảng **Odoo (mã nguồn mở)**, phục vụ học phần *Thực tập doanh nghiệp* của Khoa Công nghệ Thông tin – Trường Đại học Đại Nam. Hệ thống được thiết kế theo mô hình ERP tích hợp, tập trung vào ba phân hệ nghiệp vụ chính: **Nhân sự – Khách hàng – Văn bản**, hướng tới mục tiêu số hóa quy trình và quản lý dữ liệu tập trung.

### Các chức năng chính của hệ thống

* **Quản lý nhân sự (HRM)**
  Quản lý hồ sơ nhân viên, cơ cấu tổ chức, chức vụ, lịch sử công tác và chứng chỉ/bằng cấp; cung cấp dữ liệu nhân sự làm **master data** để gán người phụ trách, người xử lý và người phê duyệt trong toàn hệ thống.

* **Quản lý khách hàng và bán hàng (Customer/CRM)**
  Quản lý khách hàng cá nhân/doanh nghiệp; theo dõi vòng đời bán hàng từ cơ hội → báo giá → hợp đồng → đơn hàng → giao hàng → hóa đơn → thanh toán; quản lý công nợ, lịch sử tương tác, khiếu nại và chương trình khách hàng thân thiết.

* **Quản lý văn bản và tài liệu (Document Management)**
  Quản lý văn bản đến/đi, hợp đồng và tài liệu số hóa; hỗ trợ OCR trích xuất nội dung; workflow phê duyệt đa cấp; chữ ký điện tử; quản lý phiên bản tài liệu và dashboard theo dõi trạng thái xử lý.

* **Tích hợp liên module theo luồng nghiệp vụ End-to-End**
  Hệ thống tích hợp chặt chẽ giữa HRM – Customer – Document, cho phép tự động tạo và phê duyệt văn bản từ hợp đồng khách hàng, đảm bảo dữ liệu thống nhất và truy vết đầy đủ theo người chịu trách nhiệm.

* **Tự động hóa và hỗ trợ thông minh**
  Hỗ trợ trigger tự động (cron job, automated action), gửi email thông báo; định hướng tích hợp AI như OCR, chatbot trợ lý và tóm tắt văn bản nhằm giảm thao tác thủ công và tăng hiệu quả xử lý.

---

## 👥 Thành viên thực hiện

| STT | Mã sinh viên | Họ và tên           | Lớp        | Nhóm        |
| --- | ------------ | ------------------- | ---------- | ----------  |
| 1   | 1671020139   | Nguyễn Hữu Huy      | CNTT 16-01 | Nhóm 4      |
| 2   | 1671020041   | Nguyễn Thanh Bình   | CNTT 16-01 | Nhóm 4      |
| 3   | 1671020182   | Đào Thị Phương Long | CNTT 16-01 | Nhóm 4      |

---


## 🔧 2. Các công nghệ được sử dụng
<div align="center">

### Hệ điều hành
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](https://ubuntu.com/)
### Công nghệ chính
[![Odoo](https://img.shields.io/badge/Odoo-714B67?style=for-the-badge&logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![XML](https://img.shields.io/badge/XML-FF6600?style=for-the-badge&logo=codeforces&logoColor=white)](https://www.w3.org/XML/)
### Cơ sở dữ liệu
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
</div>

## 🏗️ 3. Kiến trúc hệ thống 
---

<img width="950" height="600" alt="image" src="https://github.com/user-attachments/assets/defa47a9-a18e-4a90-be35-b073fed400a7" />


Hệ thống ERP được xây dựng trên nền tảng **Odoo**, theo mô hình **Client – Server mở rộng**, cho phép tích hợp linh hoạt với các dịch vụ bên ngoài như OCR, chữ ký số và AI.

### Các thành phần chính

* **Client Layer**
  Người dùng truy cập hệ thống qua trình duyệt web (Odoo Web UI) hoặc thiết bị di động.

* **Odoo Server**
  Là trung tâm xử lý nghiệp vụ, triển khai các module ERP như:

  * HRM (Quản lý nhân sự)
  * Customer/CRM (Quản lý khách hàng, hợp đồng)
  * Document (Quản lý văn bản, phê duyệt, ký số)

* **PostgreSQL Database**
  Lưu trữ toàn bộ dữ liệu nghiệp vụ tập trung, đảm bảo đồng bộ giữa các module.

* **File Storage**
  Lưu trữ tệp đính kèm (hợp đồng, văn bản, chữ ký), có thể sử dụng filesystem hoặc object storage.

* **Integration Layer**
  Kết nối hệ thống với các dịch vụ bên ngoài thông qua REST API, Webhook hoặc RPC.

* **External Services & AI**

  * OCR: Trích xuất nội dung từ tài liệu scan
  * Digital Signature (PKI): Ký số và xác thực văn bản
  * Notification: Gửi email/thông báo sự kiện
  * Cloud Platform (tùy chọn): Lưu trữ và mở rộng dịch vụ

### Luồng xử lý tổng quát

**Client → Odoo Server → Database / File Storage → External Services**

Kiến trúc này giúp hệ thống **dễ mở rộng, dễ tích hợp và phù hợp cho cả học tập lẫn triển khai thực tế**.

---

---

## 🔄 End-to-End Flow: Số hóa hồ sơ khách hàng
<p align="center">
  <img src="docs/business flow/Nhom4_BusinessFlow_HeThongERPQuanLyKhachHang&VanBan.jpg" alt="End-to-End Business Flow - Digital Customer File" width="90%">
</p>

Luồng **Số hóa hồ sơ khách hàng** được lựa chọn làm luồng nghiệp vụ End-to-End vì thể hiện rõ nhất sự tích hợp giữa ba module cốt lõi của hệ thống ERP: **Nhân sự (HRM) – Quản lý khách hàng – Quản lý văn bản**.

Luồng bắt đầu từ tạo hồ sơ khách hàng và hợp đồng, chuyển sang xử lý văn bản pháp lý, phê duyệt – ký điện tử và kết thúc bằng việc lưu trữ, liên kết hồ sơ số hóa. Trong toàn bộ quy trình, **HRM đóng vai trò dữ liệu gốc** để gán người phụ trách, người duyệt và người ký; hệ thống hỗ trợ **tự động hóa workflow** và **tích hợp AI/API** (OCR, chữ ký số, thông báo).


---

## 🎨 Giao diện hệ thống

*(Một số giao diện tiêu biểu của hệ thống)*

Hệ thống được thiết kế với giao diện trực quan, thống nhất và thân thiện với người dùng, hỗ trợ đầy đủ các nghiệp vụ quản lý nhân sự, khách hàng và văn bản.

---

### 📊 1. Dashboard tổng quan

<p align="center">
  <img src="https://github.com/user-attachments/assets/4feafa52-32d1-481d-a300-e7ed13a1ec32" width="900"/>
</p>

**Hình 3.1 – Giao diện Dashboard**
Hiển thị tổng quan các chỉ số quan trọng của hệ thống như số lượng nhân viên, hợp đồng, đơn hàng và tình trạng hoạt động chung.

---

### 👥 2. Quản lý nhân sự

<p align="center">
  <img src="https://github.com/user-attachments/assets/64ebdfdd-92e6-4d34-a508-9ac472356676" width="900"/>
</p>

**Hình 3.2 – Giao diện quản lý nhân viên**
Cho phép quản lý thông tin nhân viên, phân quyền, theo dõi trạng thái làm việc và các nghiệp vụ liên quan.

---

### 🧑‍💼 3. Dashboard khách hàng

<p align="center">
  <img src="https://github.com/user-attachments/assets/e2962e2b-012a-41d3-b724-2def46e292cd" width="900"/>
</p>

**Hình 3.3 – Dashboard khách hàng**
Tổng hợp dữ liệu khách hàng, lịch sử giao dịch và các chỉ số hỗ trợ theo dõi mối quan hệ khách hàng (CRM).

---

### 📄 4. Quản lý hợp đồng

<p align="center">
  <img src="https://github.com/user-attachments/assets/aa526e11-ecc2-4599-b771-9007bc8dea54" width="900"/>
</p>

**Hình 3.4 – Giao diện danh sách hợp đồng**
Quản lý danh sách hợp đồng, trạng thái hiệu lực, thời hạn và thông tin chi tiết của từng hợp đồng.

---

### 💼 5. Quản lý cơ hội bán hàng

<p align="center">
  <img src="https://github.com/user-attachments/assets/20a2c4b6-7aa8-4c42-9c0f-651e937642f4" width="900"/>
</p>

**Hình 3.5 – Giao diện danh sách cơ hội bán hàng**
Theo dõi pipeline bán hàng, trạng thái từng cơ hội và hỗ trợ tối ưu hoạt động kinh doanh.

---

### 🛒 6. Quản lý đơn hàng

<p align="center">
  <img src="https://github.com/user-attachments/assets/8dae9b54-17cc-4abd-a6b4-5bdce1b1bd32" width="900"/>
</p>

**Hình 3.6 – Giao diện danh sách đơn hàng**
Quản lý thông tin đơn hàng, trạng thái xử lý, khách hàng và giá trị đơn hàng.

---

### 🗂️ 7. Quản lý văn bản

<p align="center">
  <img src="https://github.com/user-attachments/assets/ed3a6559-a815-4430-9d3b-a9fd0a642560" width="900"/>
</p>

**Hình 3.7 – Dashboard quản lý văn bản**
Tổng quan hệ thống văn bản đến – đi, hỗ trợ tìm kiếm và theo dõi trạng thái xử lý.

<p align="center">
  <img src="https://github.com/user-attachments/assets/d9d74dcc-3ed1-42a8-bbf8-02a5318446f7" width="900"/>
</p>

**Hình 3.8 – Danh sách văn bản đến**
Quản lý văn bản đến, phân loại, xử lý và theo dõi tiến độ.

<p align="center">
  <img src="https://github.com/user-attachments/assets/4c12ae94-9fef-402e-8fad-df5076a25b10" width="900"/>
</p>

**Hình 3.9 – Danh sách văn bản đi**
Quản lý văn bản đi, lưu trữ lịch sử và trạng thái gửi.

---

### 🤖 8. Chatbot hỗ trợ

<p align="center">
  <img src="https://github.com/user-attachments/assets/a39f4bed-adae-49b3-8f70-e74efb92d64b" width="900"/>
</p>

**Hình 3.10 – Chatbot hỗ trợ người dùng**
Chatbot tích hợp giúp hỗ trợ tra cứu thông tin, giải đáp nhanh các câu hỏi và hướng dẫn sử dụng hệ thống.



---
## ⚙️ 4. Cài đặt

### 4.1. Cài đặt công cụ, môi trường và các thư viện cần thiết

#### 4.1.1. Tải project.
```
git clone https://gitlab.com/anhlta/odoo-fitdnu.git
```
#### 4.1.2. Cài đặt các thư viện cần thiết
Người sử dụng thực thi các lệnh sau đề cài đặt các thư viện cần thiết

```
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev libssl-dev python3.10-distutils python3.10-dev build-essential libssl-dev libffi-dev zlib1g-dev python3.10-venv libpq-dev
```
#### 4.1.3. Khởi tạo môi trường ảo.
- Khởi tạo môi trường ảo
```
python3.10 -m venv ./venv
```
- Thay đổi trình thông dịch sang môi trường ảo
```
source venv/bin/activate
```
- Chạy requirements.txt để cài đặt tiếp các thư viện được yêu cầu
```
pip3 install -r requirements.txt
```
### 4.2. Setup database

Khởi tạo database trên docker bằng việc thực thi file dockercompose.yml.
```
sudo docker-compose up -d
```
### 4.3. Setup tham số chạy cho hệ thống
Tạo tệp **odoo.conf** có nội dung như sau:
```
[options]
addons_path = addons
db_host = localhost
db_password = odoo
db_user = odoo
db_port = 5431
xmlrpc_port = 8069
```
Có thể kế thừa từ file **odoo.conf.template**
### 4.4. Chạy hệ thống và cài đặt các ứng dụng cần thiết
Lệnh chạy
```
python3 odoo-bin.py -c odoo.conf -u all
```
Người sử dụng truy cập theo đường dẫn _http://localhost:8069/_ để đăng nhập vào hệ thống.

## 5. Nguồn tham khảo và kế thừa mã nguồn

Hệ thống được xây dựng dựa trên việc **kế thừa có chọn lọc và mở rộng** từ các mã nguồn và tài nguyên sau:

* **Repository quản lý khách hàng và CRM (tham khảo)**
  GitHub: [https://github.com/yukiharadev/TTDN-15-05-N2](https://github.com/yukiharadev/TTDN-15-05-N2)
  → Kế thừa nền tảng quản lý khách hàng/CRM và mở rộng thành vòng đời bán hàng đầy đủ theo mô hình ERP.

* **Repository quản lý văn bản (tham khảo)**
  GitHub: [https://github.com/ngocanhit201/TTDN-15-04-N2](https://github.com/ngocanhit201/TTDN-15-04-N2)
  → Kế thừa nghiệp vụ quản lý văn bản cơ bản và nâng cấp workflow duyệt, chữ ký điện tử, quản lý phiên bản.

* **Repository nền tảng học phần Thực tập doanh nghiệp – FIT DNU**
  GitHub: [https://github.com/FIT-DNU/Business-Internship](https://github.com/FIT-DNU/Business-Internship)
  → Là nền tảng triển khai chung cho các đề tài ERP, định hướng chuẩn hóa cấu trúc hệ thống và yêu cầu học phần.



## 📝 6. License

© 2024 AIoTLab, Faculty of Information Technology, DaiNam University. All rights reserved.

---

    
