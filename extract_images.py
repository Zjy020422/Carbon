import fitz
import os
from pathlib import Path

pdf_path = r"F:\work\2025work\sure\yige\code\web\website\高年级组-能源与环境-航空业尾迹云与碳排放协同监测及气候影响评估研究-项目研究论文.pdf"
output_dir = r"F:\work\2025work\sure\yige\code\web\assert"

# 创建输出文件夹
Path(output_dir).mkdir(parents=True, exist_ok=True)

# 打开PDF文件
pdf_document = fitz.open(pdf_path)

image_count = 0

# 遍历每一页
for page_num in range(len(pdf_document)):
    page = pdf_document[page_num]
    image_list = page.get_images()

    # 提取每个图片
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = pdf_document.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]

        # 保存图片
        image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
        image_path = os.path.join(output_dir, image_filename)

        with open(image_path, "wb") as image_file:
            image_file.write(image_bytes)

        image_count += 1
        print(f"提取: {image_filename}")

pdf_document.close()
print(f"\n完成！共提取 {image_count} 张图片到 {output_dir}")
