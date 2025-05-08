import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

# TreeView 样式常量
TVS_HASBUTTONS   = 0x0001
TVS_HASLINES     = 0x0002
TVS_LINESATROOT  = 0x0004
TVIF_TEXT = 0x0001
TVIF_IMAGE = 0x0002
TVIF_SELECTEDIMAGE = 0x0020
TVIF_CHILDREN = 0x0040
TVIF_PARAM = 0x0004
TV_FIRST = 0x1100
TVM_INSERTITEM = TV_FIRST + 0
TVM_EXPAND = TV_FIRST + 2
TVE_EXPAND = 0x0002
TVI_ROOT = ctypes.c_void_p(-0x10000)
TVI_FIRST = ctypes.c_void_p(-0x0FFFF)
TVI_LAST = ctypes.c_void_p(-0x0FFFE)
TVI_SORT = ctypes.c_void_p(-0x0FFFD)

# 定义 MSG 结构
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]

# TVITEM 和 TVINSERTSTRUCT 结构
class TVITEM(ctypes.Structure):
    _fields_ = [
        ("mask", wintypes.UINT),
        ("hItem", wintypes.HANDLE),
        ("state", wintypes.UINT),
        ("stateMask", wintypes.UINT),
        ("pszText", wintypes.LPWSTR),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("iSelectedImage", ctypes.c_int),
        ("cChildren", ctypes.c_int),
        ("lParam", wintypes.LPARAM),
    ]

class TVINSERTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hParent", wintypes.HANDLE),
        ("hInsertAfter", wintypes.HANDLE),
        ("item", TVITEM),
    ]

def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

# 注册窗口类
hInstance = win32api.GetModuleHandle()
className = "TreeApp"

wndClass = win32gui.WNDCLASS()
wndClass.lpfnWndProc = wnd_proc
wndClass.hInstance = hInstance
wndClass.lpszClassName = className
win32gui.RegisterClass(wndClass)

# 创建窗口
hwnd = win32gui.CreateWindowEx(
    0,
    className,
    "PyWin32 TreeView with Nodes",
    win32con.WS_OVERLAPPEDWINDOW,
    100, 100, 400, 500,
    0, 0, hInstance, None
)

# 创建 TreeView 控件
tree_hwnd = win32gui.CreateWindowEx(
    0,
    "SysTreeView32",
    None,
    win32con.WS_VISIBLE | win32con.WS_CHILD |
    TVS_HASLINES | TVS_LINESATROOT | TVS_HASBUTTONS,
    10, 10, 360, 440,
    hwnd,
    0,
    hInstance,
    None
)

# 插入树节点函数
def insert_item(parent, text, has_children=False):
    item = TVITEM()
    item.mask = TVIF_TEXT | TVIF_CHILDREN
    item.pszText = ctypes.c_wchar_p(text)
    item.cchTextMax = len(text)
    item.cChildren = 1 if has_children else 0

    insert_struct = TVINSERTSTRUCT()
    insert_struct.hParent = parent
    insert_struct.hInsertAfter = insert_struct.hInsertAfter = TVI_LAST
    insert_struct.item = item

    return win32gui.SendMessage(tree_hwnd, TVM_INSERTITEM, 0, ctypes.byref(insert_struct))

# 构建层级节点结构
root = insert_item(0, "My Software Notes", True)
insert_item(root, "mysql")
sub1 = insert_item(root, "Mysql|高级篇", True)
insert_item(sub1, "Mysql|高级篇")
insert_item(root, "Mysql|高级篇")
insert_item(root, "Mysql|高级篇")

# 展开根节点
win32gui.SendMessage(tree_hwnd, TVM_EXPAND, TVE_EXPAND, root)

# 显示窗口
win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
win32gui.UpdateWindow(hwnd)

# 消息循环
msg = MSG()
GetMessage = ctypes.windll.user32.GetMessageW
TranslateMessage = ctypes.windll.user32.TranslateMessage
DispatchMessage = ctypes.windll.user32.DispatchMessageW

while True:
    bRet = GetMessage(ctypes.byref(msg), 0, 0, 0)
    if bRet == 0:
        break
    elif bRet == -1:
        print("Error in GetMessage")
        break
    else:
        TranslateMessage(ctypes.byref(msg))
        DispatchMessage(ctypes.byref(msg))
