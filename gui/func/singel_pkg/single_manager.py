from PySide6.QtCore import QObject, Signal
'''
创建一个能够全局调用的信号槽
'''
class SignalManager(QObject):
    # 左边树状结构展示 当创建了新的笔记 就将左边的树状结构用新的来代替
    left_tree_structure_rander_after_create_new_notebook_signal = Signal(str)


#创建实例来调用这个方法
sm = SignalManager()