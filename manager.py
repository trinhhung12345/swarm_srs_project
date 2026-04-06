import pika, json, os

HOST = os.getenv("RABBITMQ_HOST", "127.0.0.1")
USER = os.getenv("RABBITMQ_USER", "admin")
PASS = os.getenv("RABBITMQ_PASS", "admin123")

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds))
    channel = connection.channel()
    channel.queue_declare(queue='ai_tasks')

    # Giả lập 4 đoạn text trích xuất từ file SRS
    tasks =[
        "Use case 1: Người dùng đăng nhập bằng Email và Password. Nếu sai 3 lần sẽ bị khóa tài khoản.",
        "Use case 2: Giảng viên có thể thêm, sửa, xóa khóa học. Khóa học phải có tên và mô tả.",
        "Use case 3: Học viên xem danh sách khóa học và có thể thanh toán qua VNPay.",
        "Use case 4: Quản trị viên xem báo cáo doanh thu hàng tháng và xuất file Excel."
    ]

    for i, text in enumerate(tasks):
        task_data = {"task_id": i + 1, "content": text}
        channel.basic_publish(exchange='', routing_key='ai_tasks', body=json.dumps(task_data))
        print(f"[x] Đã gửi Task {i + 1} lên hàng đợi cho AI.")

    connection.close()

if __name__ == '__main__':
    main()