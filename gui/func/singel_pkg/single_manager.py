from PySide6.QtCore import QObject, Signal
'''
创建一个能够全局调用的信号槽
'''
class SignalManager(QObject):
    # 左边树状结构展示 当创建了新的笔记 就将左边的树状结构用新的来代替
    left_tree_structure_rander_after_create_new_notebook_signal = Signal(str)
    # 发送当前的文件路径给main 让富文本框在显示的时候也会知道要保存到哪里去 第一个参数是传递文件路径的 第二个参数是判断属于那颗树状图结构
    send_current_file_path_2_main_richtext_signal = Signal(str, str)

#创建实例来调用这个方法
sm = SignalManager()