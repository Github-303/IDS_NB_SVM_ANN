# Hệ Thống Phát Hiện Xâm Nhập Mạng (IDS) cho Doanh Nghiệp

## Tổng Quan

Hệ thống phát hiện xâm nhập mạng (IDS) này là một giải pháp nhằm dự đoán tính bảo mật, tận dụng sức mạnh của học máy để bảo vệ hạ tầng mạng doanh nghiệp. Hệ thống phân tích cho người dùng không chuyên khi sử dụng nhiều thuật toán học máy để phát hiện, phân loại các mối đe dọa tiềm ẩn một cách chính xác.

### Điểm Nổi Bật
- Phát hiện và phân loại 5 loại tấn công khác nhau
- Độ chính xác cao với khả năng chọn model ANN, SVM
- Xử lý nhanh dùng NB
- Giao diện web trực quan, dễ sử dụng

## Tính Năng Chính

### Phân Tích Lưu Lượng
- Phát hiện, phân loại các mối đe dọa tiềm ẩn một cách chính xác

### Phân Loại Tấn Công
- DoS (Denial of Service)
- Probe (Scanning and Probing)
- R2L (Remote to Local)
- U2R (User to Root)
- Nhận diện lưu lượng bình thường

### Hiệu Suất
- Độ chính xác tổng thể: 77.80%
- Tốc độ xử lý: 125,973 bản ghi/lô
- Thời gian phản hồi trung bình: <500ms

## Yêu Cầu Hệ Thống

### Phần Cứng
- CPU: Intel Core i5 hoặc tương đương trở lên
- RAM: 8GB trở lên
- Dung lượng ổ cứng: 50GB trở lên

### Phần Mềm
- Hệ điều hành: Windows 10/11, Ubuntu 20.04+, macOS 12+
- Python 3.7 hoặc cao hơn
- Git
- Web browser hiện đại (Chrome, Firefox, Safari)

## Hướng Dẫn Sử Dụng Tool Web

### Truy Cập Tool
1. Truy cập demo tại: [IDS Tool Demo](https://huggingface.co/spaces/KException/idstoolit3)
   ![1](IDS.png)
2. Giao diện sẽ hiển thị các tùy chọn cho việc tải lên dữ liệu và chọn mô hình

### Các Bước Sử Dụng

#### 1. Chuẩn Bị Dữ Liệu
- Dữ liệu phải ở định dạng CSV
- Kích thước file không được vượt quá 200MB
- Cấu trúc dữ liệu phải tuân theo định dạng NSL_KDD với 41 đặc trưng:
  ```
  duration,protocol_type,service,flag,src_bytes,dst_bytes,...
  0,tcp,http,SF,181,5450,...
  ```

#### 2. Chọn Mô Hình
- **Naive Bayes**: Phù hợp với dữ liệu nhỏ, tốc độ xử lý nhanh
- **SVM**: Chính xác cao nhưng tốc độ xử lý chậm hơn
- **ANN**: Phù hợp với dữ liệu lớn và phức tạp

#### 3. Tải Lên và Phân Tích
1. Chọn mô hình từ dropdown menu
2. Click nút "Upload File" và chọn file CSV của bạn
3. Đợi kết quả hiển thị (thường mất 1-2 phút tùy kích thước dữ liệu)

#### 4. Đọc Kết Quả
- Biểu đồ phân bố các loại tấn công
- Bảng chi tiết các bản ghi được phát hiện
- Thống kê độ chính xác của mô hình

### Lưu Ý Quan Trọng
- Kiểm tra định dạng dữ liệu trước khi tải lên
- Nén file nếu kích thước lớn hơn 200MB
- Đảm bảo kết nối internet ổn định trong quá trình phân tích
- Không đóng tab trình duyệt khi đang phân tích

## Cài Đặt

1. Clone repository:
```bash
git clone https://github.com/your-username/ids-enterprise.git
cd ids-enterprise
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# hoặc
.\venv\Scripts\activate  # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Cấu hình hệ thống:
```bash
cp config.example.yml config.yml
# Chỉnh sửa config.yml theo môi trường của bạn
```

5. Khởi chạy ứng dụng:
```bash
python app.py
```

## Chuẩn Bị và Xử Lý Dữ Liệu NSL_KDD

### Định Dạng Dữ Liệu Yêu Cầu
- File CSV với 41 cột đặc trưng + 1 cột nhãn
- Mỗi hàng là một bản ghi lưu lượng mạng
- Kích thước file tối đa 200MB
- Encoding: UTF-8
- Delimiter: dấu phẩy (,)

### Các Bước Tiền Xử Lý
1. **Làm sạch dữ liệu**
   ```python
   # Ví dụ code xử lý
   import pandas as pd
   
   def clean_data(df):
       # Loại bỏ dòng trống
       df = df.dropna()
       # Chuyển đổi kiểu dữ liệu
       df['duration'] = df['duration'].astype(float)
       return df
   ```

2. **Mã hóa đặc trưng**
   - Chuyển đổi các đặc trưng categorical sang numerical
   - Chuẩn hóa các đặc trưng số

3. **Định dạng đầu ra**
   - Đảm bảo thứ tự các cột đúng với NSL_KDD
   - Kiểm tra tên và kiểu dữ liệu của các cột

### Xử Lý File Lớn
1. Chia nhỏ file nếu kích thước > 200MB:
   ```python
   def split_file(filename, chunk_size=190):  # size in MB
       chunks = pd.read_csv(filename, chunksize=chunk_size*1024*1024)
       for i, chunk in enumerate(chunks):
           chunk.to_csv(f'chunk_{i}.csv', index=False)
   ```

2. Nén file trước khi tải lên:
   ```python
   import gzip
   import shutil
   
   def compress_file(file_path):
       with open(file_path, 'rb') as f_in:
           with gzip.open(f'{file_path}.gz', 'wb') as f_out:
               shutil.copyfileobj(f_in, f_out)
   ```

## Kiến Trúc Hệ Thống

### Mô Hình Học Máy
- **Naive Bayes**: Phân loại cơ bản với tốc độ xử lý nhanh
- **Support Vector Machine**: Phân loại chính xác cao cho dữ liệu phi tuyến
- **Artificial Neural Network**: Khả năng học sâu cho các mẫu tấn công phức tạp

### Quy Trình Xử Lý Dữ Liệu
1. Thu thập dữ liệu mạng
2. Tiền xử lý và trích xuất đặc trưng
3. Chuẩn hóa dữ liệu
4. Phân loại và dự đoán
5. Tổng hợp và báo cáo kết quả

## Nhóm Phát Triển

- **Khánh** - Lead
- Tiến - NB
- AN + Du - ANN
- **Khánh** - SVM

## Giấy Phép
Dự án được phát hành dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## Liên Hệ & Hỗ Trợ

- Email: Bit220084@st.cmcu.edu.vn

## Đóng Góp
Chúng tôi luôn chào đón mọi đóng góp!

---
© 2024 IDS Enterprise Team. All rights reserved.


