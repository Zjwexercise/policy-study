import os
import sys
import fitz
import scan_importer

sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'D:\Users\zjw\Study\MyProject\policy\pdf\2027-考研政治刷题计划.pdf'
if not os.path.exists(pdf_path):
    pdf_path = r'D:\Users\zjw\Study\MyProject\policy\pdf\2027-刷题计划--解析册.pdf.crdownload'

print(f"打开 PDF：{os.path.basename(pdf_path)}")
doc = fitz.open(pdf_path)

temp_img = "temp_page.png"

# 扫描第 12 页到第 32 页（导论与马原核心题库）
full_ocr_text = ""
start_p = 12
end_p = 32

print(f"正在识别并提取第 {start_p+1} ~ {end_p+1} 页真题与解析...")

for p in range(start_p, end_p + 1):
    txt = scan_importer.ocr_page_image(doc, p, temp_img)
    full_ocr_text += f"\n=== Page {p+1} ===\n" + txt

doc.close()
if os.path.exists(temp_img):
    os.remove(temp_img)

print(f"OCR 提取完成，字符数：{len(full_ocr_text)}")

# 解析所有题目
questions = scan_importer.parse_questions_from_ocr_text(full_ocr_text, default_category="马原")
print(f"成功识别并解析出 {len(questions)} 道题目！")

# 存入数据库
scan_importer.import_to_database(
    workbook_name="2027考研政治刷题计划（精选真题集）",
    questions=questions,
    description=f"精选自2027考研政治刷题计划，含马原单选与多选，包含完整考点解析与答题技巧",
    overwrite=True
)
