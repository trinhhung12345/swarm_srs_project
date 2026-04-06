import pika, json, os
import fitz  # PyMuPDF

HOST = os.getenv("RABBITMQ_HOST", "127.0.0.1")
USER = os.getenv("RABBITMQ_USER", "admin")
PASS = os.getenv("RABBITMQ_PASS", "admin123")

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds))
    channel = connection.channel()
    
    # Khai báo hàng đợi đầu tiên cho Agent Phân tích
    channel.queue_declare(queue='queue_srs_raw')

    pdf_path = 'data/input/srs_document.pdf'
    doc = fitz.open(pdf_path)
    
    print(f"[*] Manager đang đọc tài liệu SRS ({len(doc)} trang)...")

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").strip()
        
        # Bỏ qua các trang trống
        if len(text) < 50: continue 
            
        task = {
            "page": page_num + 1,
            "raw_text": text
        }
        
        channel.basic_publish(exchange='', routing_key='queue_srs_raw', body=json.dumps(task))
        print(f"[x] Đã gửi nội dung Trang {page_num + 1} cho Agent Phân tích.")
        
    connection.close()

if __name__ == '__main__':
    main()