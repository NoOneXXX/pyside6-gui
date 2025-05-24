import base64
import os
# PyMuPDF==1.26.0 这里要下载这个 也要注意
import fitz
# 这里引用的是 python-docx==1.1.2 注意了
from docx import Document
from ebooklib import epub
from bs4 import BeautifulSoup

def load_file(file_path, text_widget):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text_widget.setPlainText(f.read())

    elif ext == '.docx':
        doc = Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        text_widget.setPlainText(full_text)

    elif ext == '.pdf':
        doc = fitz.open(file_path)
        content = ""
        for page in doc:
            content += page.get_text() + "\n"
        text_widget.setPlainText(content)

    elif ext == '.epub':
        book = epub.read_epub(file_path)
        content = ''
        image_folder = os.path.join(os.path.dirname(file_path), 'images')

        # Create the images folder if it doesn't exist
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        # Track image names to avoid overwriting
        image_counter = 0

        # Iterate through the items in the EPUB file
        for item in book.get_items():
            if item.get_type() == 9:  # 9 corresponds to 'epub.ITEM_DOCUMENT'
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')

                # Handle images: Convert image paths to local paths
                for img_tag in soup.find_all('img'):
                    img_src = img_tag.get('src')
                    if img_src:
                        # Check if the image is base64-encoded
                        if img_src.startswith('data:image'):
                            # Extract the base64 data and save as an image
                            img_data = img_src.split(',')[1]  # Get the data part after 'data:image/png;base64,'
                            img_data = base64.b64decode(img_data)  # Decode the base64 data

                            # Ensure unique image filename
                            img_name = f"image_{image_counter + 1}.png"
                            img_path = os.path.join(image_folder, img_name)
                            with open(img_path, 'wb') as img_file:
                                img_file.write(img_data)

                            # Update the src to the local path
                            img_tag['src'] = f'file:///{img_path}'

                        else:
                            # If it's a regular image, download it from the EPUB
                            img_name = os.path.basename(img_src)
                            img_path = os.path.join(image_folder, img_name)

                            # Ensure unique image filename (in case of naming conflicts)
                            while os.path.exists(img_path):
                                image_counter += 1
                                img_name = f"{image_counter}_{os.path.basename(img_src)}"
                                img_path = os.path.join(image_folder, img_name)

                            img_tag['src'] = f'file:///{img_path}'

                            # Extract the image and save it
                            image_item = book.get_item_with_id(img_src)
                            if image_item:
                                with open(img_path, 'wb') as img_file:
                                    img_file.write(image_item.get_body())

                            print(f"Image saved: {img_path}")  # Debugging line to check image paths

                # Add the HTML content to the full content
                content += str(soup) + '\n'

        # Render HTML content with images in the rich text widget
        text_widget.setHtml(content)



    # else:
    #     text_widget.setPlainText("不支持的格式")
