import pika, json, os, time
from openai import OpenAI

# 1. Kết nối RabbitMQ (Mạng Tailscale)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "100.95.51.25")
USER = os.getenv("RABBITMQ_USER", "admin")
PASS = os.getenv("RABBITMQ_PASS", "admin123")

# 2. Kết nối Ollama (Local trên chính máy WSL này)
# Vì Ollama chạy trên cùng máy với worker.py, ta trỏ thẳng vào localhost
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama', # Ollama không cần key, nhưng cứ điền bừa cho đúng chuẩn
)
MODEL_NAME = "qwen3.5:4b" # Hoặc qwen2.5:7b tùy bạn đã tải cái nào

def ask_ai(text_content):
    prompt = f"Bạn là một chuyên gia phân tích hệ thống. Hãy đọc yêu cầu sau và trích xuất ra danh sách các tính năng cần lập trình một cách ngắn gọn:\n\n{text_content}"
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3 # Giảm độ sáng tạo để AI phân tích chính xác hơn
    )
    return response.choices[0].message.content

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=creds))
    channel = connection.channel()
    channel.queue_declare(queue='ai_tasks')
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        task = json.loads(body.decode())
        print(f"\n[*] AI đang suy nghĩ Task {task['task_id']}...")
        
        start_time = time.time()
        # Gọi mô hình AI trên GPU
        ai_response = ask_ai(task['content'])
        end_time = time.time()
        
        print(f"--- KẾT QUẢ TỪ AI (Mất {end_time - start_time:.1f}s) ---")
        print(ai_response)
        print("-------------------------------------------------")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    print(' [*] AI Worker đang chờ việc. Nhấn CTRL+C để thoát.')
    channel.basic_consume(queue='ai_tasks', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    main()