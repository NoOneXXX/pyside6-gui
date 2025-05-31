
'''
读取电子小说的文件
'''
import base64
import os
from urllib.parse import unquote
from ebooklib import epub
from bs4 import BeautifulSoup

class read_epud_to_richtext():
    def __init__(self, path, rich_text_edit):
        self.file_path = path
        self.rich_text_edit = rich_text_edit

    def read_epud_context(self):
        book = epub.read_epub(self.file_path)
        content = ''
        image_folder = os.path.join(os.path.dirname(self.file_path), 'images')

        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        for item in book.get_items():
            if item.get_type() == 9:  # epub.ITEM_DOCUMENT
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')

                for img_tag in soup.find_all('img'):
                    img_src = img_tag.get('src')
                    if not img_src:
                        continue

                    if img_src.startswith('data:image'):
                        # Base64 图像处理
                        img_data = img_src.split(',')[1]
                        img_data = base64.b64decode(img_data)
                        img_name = f"embedded_{abs(hash(img_data))}.png"
                        img_path = os.path.join(image_folder, img_name)

                        if not os.path.exists(img_path):
                            with open(img_path, 'wb') as img_file:
                                img_file.write(img_data)

                        img_tag['src'] = f'file:///{img_path}'

                    else:
                        # EPUB 内部图像资源处理
                        image_item = self.find_image_item(book, img_src)
                        if image_item:
                            raw_epub_path = image_item.get_name().replace('\\', '/')
                            img_name = raw_epub_path.replace('/', '_')
                            img_path = os.path.join(image_folder, img_name)

                            if not os.path.exists(img_path):
                                with open(img_path, 'wb') as img_file:
                                    img_file.write(image_item.get_content())

                            img_tag['src'] = f'file:///{img_path}'
                        else:
                            print(f"[WARN] 未找到图像资源: {img_src}")

                content += str(soup) + '\n'
        self.rich_text_edit.setHtml(f'''
                <div style="font-size:14pt; font-family:微软雅黑,SimSun,Arial,sans-serif; line-height:1.6;">
                {content}
                </div>
                ''')

    def find_image_item(self,book, src):
        src = unquote(src).replace('\\', '/').strip('../').strip('./')
        src_basename = os.path.basename(src).lower()

        for item in book.get_items():
            if item.get_type() == 1:  # epub.ITEM_IMAGE
                name = item.get_name().replace('\\', '/')
                item_basename = os.path.basename(name).lower()

                if item_basename == src_basename:
                    return item

        return None
