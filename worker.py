import pika, json, base64, os, time
import fitz  # PyMuPDF
import pdfplumber

HOST = os.getenv("RABBITMQ_HOST")
USER = os.getenv("RABBITMQ_USER")
PASS = os.getenv("RABBITMQ_PASS")
OUTPUT_DIR = "data/output"

def process_complex_pdf_page(page_num, pdf_bytes):
    # Lưu file tạm để các thư viện đọc
    temp_pdf = f"temp_page_{page_num}.pdf"
    with open(temp_pdf, "wb") as f:
        f.write(pdf_bytes)

    result = {"page": page_num, "text": "", "tables": [], "images_saved":[]}

    try:
        # 1. Trích xuất Text và Bảng (Dùng pdfplumber)
        with pdfplumber.open(temp_pdf) as pdf:
            page = pdf.pages[0]
            
            # Lấy text thông thường
            result["text"] = page.extract_text()
            
            # Lấy Bảng (Nó sẽ tự nhận diện các đường kẻ bảng như Hình 2 & 3)
            tables = page.extract_tables()
            for tbl in tables:
                # Xóa các dòng None (dòng rỗng) do ô gộp tạo ra
                clean_table = [[str(cell).replace('\n', ' ') if cell else "" for cell in row] for row in tbl]
                result["tables"].append(clean_table)

        # 2. Trích xuất Hình ảnh (Dùng PyMuPDF fitz)
        doc = fitz.open(temp_pdf)
        for img_index, img in enumerate(doc.get_page_images(0)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            img_filename = f"{OUTPUT_DIR}/page_{page_num}_img_{img_index}.{image_ext}"
            with open(img_filename, "wb") as img_file:
                img_file.write(image_bytes)
            result["images_saved"].append(img_filename)
            
    finally:
        os.remove(temp_pdf) # Dọn dẹp file tạm
        
    return result

def main():
    creds = pika.PlainCredentials(USER, PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, credentials=creds))
    channel = connection.channel()
    channel.queue_declare(queue='pdf_complex_tasks')
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        task = json.loads(body.decode())
        page_num = task['page_number']
        pdf_bytes = base64.b64decode(task['pdf_base64'])
        
        print(f"\n[*] Worker đang cày Trang {page_num}...")
        start_time = time.time()
        
        # Gọi hàm xử lý cốt lõi
        ext_data = process_complex_pdf_page(page_num, pdf_bytes)
        
        # In kết quả
        print(f"[v] Trang {page_num} xong trong {time.time()-start_time:.2f}s")
        print(f"    - Tìm thấy: {len(ext_data['tables'])} Bảng, {len(ext_data['images_saved'])} Ảnh.")
        
        # Lưu JSON data ra thư mục output
        with open(f"{OUTPUT_DIR}/page_{page_num}_data.json", "w", encoding="utf-8") as f:
            json.dump(ext_data, f, ensure_ascii=False, indent=4)
            
        ch.basic_ack(delivery_tag=method.delivery_tag)

    print(' [*] Đang đợi Task. Nhấn CTRL+C để thoát.')
    channel.basic_consume(queue='pdf_complex_tasks', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    main()
