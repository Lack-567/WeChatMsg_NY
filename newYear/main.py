import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from newYear.ui.main_window import NewYearGreetingWindow

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("新年祝福生成器")
    app.setOrganizationName("WeChatMsg")
    
    # 创建并显示主窗口
    window = NewYearGreetingWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 