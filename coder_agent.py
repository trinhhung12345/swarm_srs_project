import pika, json, os
from openai import OpenAI

HOST = os.getenv("RABBITMQ_HOST", "100.95.51.25")
USER = os.getenv("RABBITMQ_USER", "admin")
PASS = os.getenv("RABBITMQ_PASS", "admin123")

client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
MODEL = "qwen3.5:4b"

def generate_code(specs):
    prompt = f"""Bạn là một Lập trình viên Backend xuất sắc (Python/FastAPI).
Dựa trên bản thiết kế yêu cầu sau từ BA:
---
{specs}
---
Hãy viết code xử lý cho các tính năng trên. Trả về duy nhất code, không giải thích dài dòng."""
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds, heartbeat=0))
    channel = connection.channel()
    
    # Chỉ lắng nghe hàng đợi Coding
    channel.queue_declare(queue='queue_coding_tasks')
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        task = json.loads(body.decode())
        print(f"\n[Coder Agent] Nhận yêu cầu lập trình (Nguồn: Trang {task['page']}). Đang viết code...")
        
        # AI sinh Code
        code_result = generate_code(task['specs'])
        
        # In kết quả hoặc lưu ra file
        print(f"=== KẾT QUẢ CODE (Trang {task['page']}) ===")
        print(code_result)
        print("===========================================")
        
        # Lưu ra file Python thực tế
        os.makedirs("data/output", exist_ok=True)
        with open(f"data/output/generated_page_{task['page']}.py", "w", encoding="utf-8") as f:
            f.write(code_result)
            
        ch.basic_ack(delivery_tag=method.delivery_tag)

    print(' [*] Coder Agent đã sẵn sàng. Nhấn CTRL+C để thoát.')
    channel.basic_consume(queue='queue_coding_tasks', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    main()