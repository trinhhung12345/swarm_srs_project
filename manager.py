import pika, json, base64, os
import fitz  # PyMuPDF

HOST = os.getenv("RABBITMQ_HOST")
USER = os.getenv("RABBITMQ_USER")
PASS = os.getenv("RABBITMQ_PASS")

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds))
    channel = connection.channel()
    channel.queue_declare(queue='pdf_complex_tasks')

    pdf_path = 'data/input/srs_document.pdf' # Bạn copy file PDF vào đây
    doc = fitz.open(pdf_path)
    
    print(f"[*] Đang xử lý tài liệu {len(doc)} trang...")

    for page_num in range(len(doc)):
        # Tạo một file PDF mới chỉ chứa 1 trang này trong RAM
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        pdf_bytes = single_page_doc.write()
        
        # Mã hóa gửi đi
        task = {
            "page_number": page_num + 1,
            "pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')
        }
        
        channel.basic_publish(exchange='', routing_key='pdf_complex_tasks', body=json.dumps(task))
        print(f"[x] Đã gửi Trang {page_num + 1} cho Worker.")
        
    connection.close()

if __name__ == '__main__':
    main()
