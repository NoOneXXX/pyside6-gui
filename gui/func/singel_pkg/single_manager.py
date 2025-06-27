from PySide6.QtCore import QObject, Signal
'''
创建一个能够全局调用的信号槽
'''
class SignalManager(QObject):
    # 左边树状结构展示 当创建了新的笔记 就将左边的树状结构用新的来代替
    left_tree_structure_rander_after_create_new_notebook_signal = Signal(str)
    # 发送当前的文件路径给main 让富文本框在显示的时候也会知道要保存到哪里去 第一个参数是传递文件路径的 第二个参数是判断属于那颗树状图结构
    send_current_file_path_2_main_richtext_signal = Signal(str, str)
    # 发送pdf地址给main方法 动态的渲染这个pdf 通过浏览器的方式
    send_pdf_path_2_main_signal = Signal(str)
    # 当读取过pdf后的组件会被换成web引擎 然后其他文件读取的时候就要再换回来 否则就会因为找不渲染组件报错
    change_web_engine_2_richtext_signal = Signal()
    # 接收回传的富文本框对象 这里要传送的是RichTextEdit对象
    received_rich_text_signal = Signal(QObject)
    # 接收回传的富文本框对象 这里要传送的是RichTextEdit对象 左侧树的点击事件使用
    received_rich_text_2_left_click_signal = Signal(QObject)

#创建实例来调用这个方法
sm = SignalManager()