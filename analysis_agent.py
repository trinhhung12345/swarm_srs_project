import pika, json, os
from openai import OpenAI

HOST = os.getenv("RABBITMQ_HOST", "100.95.51.25")
USER = os.getenv("RABBITMQ_USER", "admin")
PASS = os.getenv("RABBITMQ_PASS", "admin123")

client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
MODEL = "qwen3.5:4b"

def analyze_requirements(raw_text):
    prompt = f"""Bạn là một Chuyên gia Phân tích Hệ thống (Business Analyst).
Dưới đây là nội dung trích xuất từ tài liệu đặc tả SRS:
---
{raw_text}
---
Nhiệm vụ: Hãy phân tích đoạn trên và liệt kê ngắn gọn các API cần phải viết (ví dụ: API Đăng nhập, API Thêm Khóa học...). Chỉ liệt kê, không viết code."""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds, heartbeat=0))
    channel = connection.channel()
    
    # Hàng đợi nó LẮNG NGHE
    channel.queue_declare(queue='queue_srs_raw')
    # Hàng đợi nó SẼ GỬI ĐẾN (Cho Coder)
    channel.queue_declare(queue='queue_coding_tasks')
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        task = json.loads(body.decode())
        print(f"\n[Analyst Agent] Đang đọc Trang {task['page']} từ SRS...")
        
        # Bước 1: AI Suy nghĩ
        specs = analyze_requirements(task['raw_text'])
        print(f"[Analyst Agent] Đã phân tích xong. Chuyển giao cho Coder...")
        
        # Bước 2: Đóng gói và gửi cho Agent Lập trình
        coder_task = {
            "page": task['page'],
            "specs": specs
        }
        channel.basic_publish(exchange='', routing_key='queue_coding_tasks', body=json.dumps(coder_task))
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    print(' [*] Analyst Agent đã sẵn sàng. Nhấn CTRL+C để thoát.')
    channel.basic_consume(queue='queue_srs_raw', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    main()