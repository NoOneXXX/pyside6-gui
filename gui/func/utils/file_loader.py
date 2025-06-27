
import os

from PySide6.QtCore import Slot, QObject
from .read_pdf_epud_txt_word_type.read_epud import read_epud_to_richtext
from gui.func.singel_pkg.single_manager import sm
from charset_normalizer import from_path

class file_loader():
    def __init__(self, path, rich_text_edit):
        self.file_path = path
        self.rich_text_edit = rich_text_edit
        sm.received_rich_text_signal.connect(self.get_rich_text)

    def load_file(self):
        ext = os.path.splitext(self.file_path)[1].lower()
    
        if ext == '.txt':
            sm.change_web_engine_2_richtext_signal.emit()
            result = from_path(self.file_path).best()
            if result is None:
                self.rich_text_edit.setPlainText('无法解析')
            else:
                # charset-normalizer 可能返回 utf_16，要转成 Python 支持的格式
                encoding = result.encoding.replace('_', '-')
                print(f"检测到编码: {encoding}")
                with open(self.file_path, 'r', encoding=encoding) as f:
                    self.rich_text_edit.setPlainText(f.read())


        elif ext == '.docx' or ext == '.doc':
            sm.send_pdf_path_2_main_signal.emit(self.file_path)
    
        elif ext == '.pdf':
            sm.send_pdf_path_2_main_signal.emit(self.file_path)
    
        elif ext == '.epub':
            sm.change_web_engine_2_richtext_signal.emit()
            # 直接的调用封装的类
            read_epud = read_epud_to_richtext(self.file_path, self.rich_text_edit)
            read_epud.read_epud_context()

    '''
    因为pdf读取后 后面再次点击富文本框的时候就会因为组件被替换了
    报错 这个就是将原本的富文本框给更新回来
    '''
    @Slot(QObject)
    def get_rich_text(self , rich_text_edit):
        self.rich_text_edit = rich_text_edit

