<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
    PLATFORM ERP
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
Platform ERP được áp dụng vào học phần Thực tập doanh nghiệp dựa trên mã nguồn mở Odoo. 

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

## 🚀 3. Giới thiệu hệ thống ERP

**Platform ERP** là hệ thống quản trị doanh nghiệp được xây dựng trên nền tảng **Odoo (mã nguồn mở)**, phục vụ học phần *Thực tập doanh nghiệp* của Khoa Công nghệ Thông tin – Trường Đại học Đại Nam. Hệ thống được thiết kế theo mô hình ERP tích hợp, tập trung vào ba phân hệ nghiệp vụ chính: **Nhân sự – Khách hàng – Văn bản**, hướng tới mục tiêu số hóa quy trình và quản lý dữ liệu tập trung.

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

## 4. Nguồn tham khảo và kế thừa mã nguồn

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

    
