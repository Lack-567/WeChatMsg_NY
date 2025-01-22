import ctypes
import sys
import time
import traceback
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from app.log.exception_handling import ExceptionHanding, send_error_msg
from app.ui.Icon import Icon
from app.DataBase import close_db
from app.log import logger
from app.ui import mainview
from app.ui.tool.pc_decrypt import pc_decrypt
from app.config import version, SEND_LOG_FLAG

widget = None


def excepthook(exc_type, exc_value, traceback_):
    # 将异常信息转为字符串

    # 在这里处理全局异常

    error_message = ExceptionHanding(exc_type, exc_value, traceback_)
    txt = '您可添加QQ群发送log文件以便解决该问题'
    msg = f"Exception Type: {exc_type.__name__}\nException Value: {exc_value}\ndetails: {error_message}\n\n{txt}"
    if SEND_LOG_FLAG:
        send_error_msg(msg)
    logger.error(f'程序发生了错误:\n\n{msg}')
    # 创建一个 QMessageBox 对象
    error_box = QMessageBox()

    # 设置对话框的标题
    error_box.setWindowTitle("未知错误")
    pixmap = QPixmap(Icon.logo_ico_path)
    icon = QIcon(pixmap)
    error_box.setWindowIcon(icon)
    # 设置对话框的文本消息
    error_box.setText(msg)
    # 设置对话框的图标，使用 QMessageBox.Critical 作为图标类型
    error_box.setIcon(QMessageBox.Critical)
    # 添加一个"确定"按钮
    error_box.addButton(QMessageBox.Ok)

    # 显示对话框
    error_box.exec_()

    # 调用原始的 excepthook，以便程序正常退出
    sys.__excepthook__(exc_type, exc_value, traceback_)


# 设置 excepthook
sys.excepthook = excepthook


ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WeChatReport")
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class ViewController(QWidget):
    def __init__(self):
        super().__init__()
        self.viewMainWindow = None
        self.viewDecrypt = None

    def loadPCDecryptView(self):
        """
        登录界面
        :return:
        """
        self.viewDecrypt = pc_decrypt.DecryptControl()
        self.viewDecrypt.DecryptSignal.connect(self.show_success)
        self.viewDecrypt.show()

    def loadMainWinView(self, username=None):
        """
        聊天界面
        :param username: 账号
        :return:
        """
        username = ''
        start = time.time()
        self.viewMainWindow = mainview.MainWinController(username=username)
        self.viewMainWindow.exitSignal.connect(self.close)
        try:
            self.viewMainWindow.setWindowTitle(f"留痕-{version}")
            
            # 添加新年祝福生成器菜单
            menu_new_year = QMenu("新年祝福", self.viewMainWindow.menubar)
            menu_new_year.setObjectName("menu_new_year")
            self.viewMainWindow.menubar.addMenu(menu_new_year)
            
            # 添加新年祝福生成器动作
            action_new_year = menu_new_year.addAction("生成祝福")
            action_new_year.setIcon(Icon.Help_Icon)  # 使用帮助图标或其他合适的图标
            action_new_year.triggered.connect(self.open_new_year_generator)
            
            self.viewMainWindow.show()
            end = time.time()
            self.viewMainWindow.init_ui()
            print('ok', '本次加载用了', end - start, 's')

        except Exception as e:
            print(f"Exception: {e}")
            logger.error(traceback.format_exc())

    def open_new_year_generator(self):
        """打开新年祝福生成器"""
        try:
            import subprocess
            import os
            
            # 获取newYear目录下main.py的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            new_year_main = os.path.join(current_dir, 'newYear', 'main.py')
            
            if os.path.exists(new_year_main):
                # 使用当前Python解释器启动新年祝福生成器
                python_exe = sys.executable
                subprocess.Popen([python_exe, new_year_main])
            else:
                QMessageBox.warning(self, '错误', '未找到新年祝福生成器程序')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'启动新年祝福生成器失败：{str(e)}')
            logger.error(traceback.format_exc())

    def show_success(self):
        QMessageBox.about(self, "解密成功", "数据库文件存储在\napp/DataBase/Msg\n文件夹下")

    def close(self) -> bool:
        close_db()
        super().close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont('微软雅黑', 12)  # 使用 Times New Roman 字体，字体大小为 14
    app.setFont(font)
    view = ViewController()
    widget = view.viewMainWindow
    try:
        # view.loadPCDecryptView()
        view.loadMainWinView()
        # view.show()
        # view.show_success()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Exception: {e}")
        logger.error(traceback.format_exc())
