# Hướng Dẫn Chạy Dự Án YOLOv8 Web App

Dự án này bao gồm 2 phần: **Backend** (Python/FastAPI) để xử lý nhận diện vật thể và **Frontend** (Nuxt.js) để hiển thị giao diện người dùng.

## 1. Yêu Cầu Hệ Thống (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:

*   **Python**: Phiên bản 3.10 trở lên.
*   **Node.js**: Phiên bản 18.0.0 trở lên (Yêu cầu của Nuxt 3).
*   **Git**: Để tải mã nguồn (nếu chưa có).

## 2. Cài Đặt & Chạy Backend

Backend chịu trách nhiệm chạy mô hình YOLOv8 và xử lý video stream.

1.  **Mở terminal** và di chuyển vào thư mục `backend`:
    ```bash
    cd backend
    ```

2.  **Tạo môi trường ảo (Virtual Environment)** (Khuyên dùng):
    ```bash
    python -m venv venv
    ```

3.  **Kích hoạt môi trường ảo**:
    *   **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS / Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Cài đặt các thư viện cần thiết**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Chạy server**:
    ```bash
    uvicorn main:app --reload
    ```
    *   Server sẽ chạy tại: `http://127.0.0.1:8000`
    *   API Docs (Swagger): `http://127.0.0.1:8000/docs`

## 3. Cài Đặt & Chạy Frontend

Frontend hiển thị camera và kết quả nhận diện.

1.  **Mở một terminal mới** (giữ terminal backend đang chạy) và di chuyển vào thư mục `frontend`:
    ```bash
    cd frontend
    ```

2.  **Cài đặt các thư viện**:
    ```bash
    npm install
    ```

3.  **Chạy ứng dụng**:
    ```bash
    npm run dev
    ```
    *   Ứng dụng sẽ chạy tại: `http://localhost:3000`

## 4. Sử Dụng

1.  Mở trình duyệt và truy cập `http://localhost:3000`.
2.  Cấp quyền truy cập **Camera** khi được hỏi.
3.  Đưa các vật thể vào trước camera để hệ thống nhận diện.
4.  Kết quả nhận diện sẽ được đọc bằng giọng nói tiếng Việt và hiển thị trên màn hình.

## 5. Cấu Trúc Dự Án

*   `backend/`: Mã nguồn Python, mô hình YOLO.
    *   `main.py`: File chính chạy server FastAPI.
    *   `yolov8n.pt`: File trọng số mô hình (sẽ tự tải nếu chưa có).
*   `frontend/`: Mã nguồn Nuxt.js.
    *   `app.vue`: Giao diện chính.
    *   `nuxt.config.ts`: Cấu hình dự án Frontend.
