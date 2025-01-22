from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, QStackedWidget,
                             QScrollArea, QFrame, QTextEdit, QDialog, QFormLayout,
                             QListWidgetItem, QCheckBox, QGroupBox, QDateEdit, QMessageBox,
                             QProgressDialog, QApplication, QMenu, QCompleter, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QStringListModel, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCharFormat, QSyntaxHighlighter, QPixmap
from PyQt5.QtCore import QDate
import os
import sys
from datetime import datetime
import json

from newYear.utils.volcano_api import VolcanoAPI
from newYear.utils.data_processor import DataProcessor
from newYear.utils.search_helper import SearchHelper
from newYear.ui.result_display import ResultDisplay
from app.components.CAvatar import CAvatar
from newYear.utils.version_manager import VersionManager
from newYear.utils.card_util import generate_card

class SearchHighlighter(QSyntaxHighlighter):
    """搜索结果高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        
    def set_search_text(self, text):
        self.search_text = text
        self.rehighlight()
        
    def highlightBlock(self, text):
        if not self.search_text:
            return
            
        format = QTextCharFormat()
        format.setBackground(QColor(255, 255, 0, 100))  # 淡黄色背景
        
        index = text.lower().indexOf(self.search_text.lower())
        while index >= 0:
            self.setFormat(index, len(self.search_text), format)
            index = text.lower().indexOf(self.search_text.lower(), index + 1)

class GenerateWorker(QThread):
    """生成任务工作线程"""
    progress = pyqtSignal(int, str)  # 进度信号
    finished = pyqtSignal(bool, str)  # 完成信号
    result = pyqtSignal(dict)  # 结果信号
    
    def __init__(self, api, data_processor, contact_info, time_range, style_prompt):
        super().__init__()
        self.api = api
        self.data_processor = data_processor
        self.contact_info = contact_info
        self.time_range = time_range
        self.style_prompt = style_prompt
        
    def run(self):
        try:
            # 获取聊天记录 (20%)
            self.progress.emit(10, f"正在获取与{self.contact_info['name']}的聊天记录...")
            chat_history = self.data_processor.get_chat_history(
                self.contact_info['wxid'],
                self.time_range['start_date'],
                self.time_range['end_date']
            )
            
            # 分析聊天内容 (40%)
            self.progress.emit(20, "正在分析聊天记录...")
            chat_analysis = self.data_processor.analyze_chat_content(chat_history)
            
            # 生成祝福内容 (60%)
            self.progress.emit(30, "正在生成新年祝福...")
            result = self.api.generate_greeting(
                self.contact_info,
                chat_history,
                self.style_prompt
            )
            
            # 准备生成贺卡 (70%)
            self.progress.emit(50, "正在准备生成贺卡...")
            
            # 生成贺卡图片 (90%)
            self.progress.emit(70, "正在生成贺卡图片...")
            
            # 保存结果 (100%)
            self.progress.emit(90, "正在保存生成结果...")
            
            self.result.emit(result)
            self.progress.emit(100, "生成完成！")
            self.finished.emit(True, "")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class ContactItem(QWidget):
    """自定义联系人列表项"""
    def __init__(self, contact_name, contact_id, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 复选框
        self.checkbox = QCheckBox()
        layout.addWidget(self.checkbox)
        
        # 头像
        self.avatar = CAvatar(parent=self, shape=CAvatar.Circle, size=QSize(30, 30))
        layout.addWidget(self.avatar)
        
        # 联系人名称 - 使用原始备注名
        self.name_label = QLabel(contact_name)
        layout.addWidget(self.name_label)
        
        # 生成状态指示器
        self.status = QLabel()
        self.status.setFixedSize(16, 16)
        layout.addWidget(self.status)
        
        self.contact_id = contact_id
        layout.addStretch()
        
        # 高亮器
        self.highlighter = SearchHighlighter(self.name_label)
        
    def set_avatar(self, img_bytes):
        """设置头像
        Args:
            img_bytes: 头像的二进制数据
        """
        print(f"[ContactItem] 设置头像 - 联系人ID: {self.contact_id}")
        if not img_bytes:
            print(f"[ContactItem] 未提供头像数据，使用默认头像 - 联系人ID: {self.contact_id}")
            self.avatar.setBytes(QPixmap(Icon.Default_avatar_path))
            return
            
        try:
            self.avatar.setBytes(img_bytes)
            print(f"[ContactItem] 成功设置头像 - 联系人ID: {self.contact_id}")
        except Exception as e:
            print(f"[ContactItem] 设置头像失败: {str(e)}")
            self.avatar.setBytes(QPixmap(Icon.Default_avatar_path))
            
    def set_generated(self, generated=True):
        """设置生成状态"""
        if generated:
            self.status.setStyleSheet("background-color: #4CAF50; border-radius: 8px;")
            self.status.setToolTip("已生成")
        else:
            self.status.setStyleSheet("background-color: transparent;")
            self.status.setToolTip("")
            
    def highlight_text(self, text):
        """高亮显示搜索文本"""
        self.highlighter.set_search_text(text)

class APIConfigDialog(QDialog):
    """API配置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('配置')
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # API配置区域
        api_group = QGroupBox("火山引擎API配置")
        api_layout = QFormLayout()
        
        # API Key输入
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText('请输入您的火山引擎API Key')
        api_layout.addRow('API Key:', self.api_key_input)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 时间范围配置区域
        time_group = QGroupBox("消息记录时间范围")
        time_layout = QFormLayout()
        
        # 开始时间
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))  # 默认一年前
        time_layout.addRow('开始时间:', self.start_date)
        
        # 结束时间
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())  # 默认今天
        time_layout.addRow('结束时间:', self.end_date)
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        cancel_btn = QPushButton('取消')
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def get_config(self):
        """获取配置信息"""
        return {
            'api_key': self.api_key_input.text(),
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': self.end_date.date().toString('yyyy-MM-dd')
        }
        
    def set_config(self, config):
        """设置配置信息"""
        if config.get('api_key'):
            self.api_key_input.setText(config['api_key'])
        if config.get('start_date'):
            self.start_date.setDate(QDate.fromString(config['start_date'], 'yyyy-MM-dd'))
        if config.get('end_date'):
            self.end_date.setDate(QDate.fromString(config['end_date'], 'yyyy-MM-dd'))

class CustomPromptDialog(QDialog):
    """自定义提示词对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('自定义提示词')
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 说明文字
        desc = QLabel('请输入自定义提示词，系统将基于此生成新年祝福、美好祝愿和祝福成语')
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 提示词输入区
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText('例如：我们是多年的好朋友，经常一起打球...')
        layout.addWidget(self.prompt_input)
        
        # 按钮区
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('确定')
        cancel_btn = QPushButton('取消')
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

class StyleButton(QPushButton):
    """可切换选中状态的风格按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)  # 确保同组按钮只能选中一个

class NewYearGreetingWindow(QMainWindow):
    """新年祝福生成器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("新年祝福生成器")
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        # 居中显示
        self.move(int((screen.width() - self.width()) / 2),
                 int((screen.height() - self.height()) / 2))
        
        # 初始化数据处理器
        self.data_processor = DataProcessor()
        self.search_helper = SearchHelper()
        
        # 初始化配置
        self.config = {
            'api_key': '',
            'start_date': '',
            'end_date': ''
        }
        
        # 初始化版本管理器
        self.version_manager = VersionManager()
        
        # 初始化UI
        self.init_ui()
        
        # 加载联系人列表
        self.load_contacts()
        
        self.current_style = 'formal'  # 默认正式风格
        self.custom_prompt = ''  # 存储自定义提示词
        self.current_template = 1  # 默认使用模板1
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('2025新年祝福生成器')
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(16)  # 增加组件间距
        main_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        
        # 添加顶部区域
        self.init_header(main_layout)
        
        # 添加内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)  # 增加左右区域间距
        self.init_contact_list(content_layout)  # 左侧联系人列表
        self.init_content_area(content_layout)  # 右侧内容区域
        main_layout.addLayout(content_layout)
        
        # 添加底部操作区
        self.init_footer(main_layout)
        
        # 设置样式
        self.set_styles()
        
    def init_header(self, parent_layout):
        """初始化头部区域"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        # Logo和标题
        title_label = QLabel('2025新年祝福生成器')
        title_label.setObjectName('title')
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()  # 添加弹性空间
        
        # 配置按钮
        config_btn = QPushButton('配置')
        config_btn.clicked.connect(self.show_api_config)
        header_layout.addWidget(config_btn)

        # 导出按钮
        export_btn = QPushButton('导出')
        export_btn.clicked.connect(self.export_to_desktop)
        header_layout.addWidget(export_btn)
        
        parent_layout.addWidget(header)

    def init_contact_list(self, parent_layout):
        """初始化联系人列表区域"""
        contact_frame = QFrame()
        contact_frame.setObjectName('contact-frame')
        contact_frame.setMinimumWidth(280)  # 设置最小宽度
        contact_frame.setMaximumWidth(320)  # 设置最大宽度
        contact_layout = QVBoxLayout(contact_frame)
        contact_layout.setContentsMargins(12, 12, 12, 12)  # 增加内边距
        contact_layout.setSpacing(12)  # 增加组件间距
        
        # 列表标题和搜索区域
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        # 标题行
        title_layout = QHBoxLayout()
        title = QLabel('联系人列表')
        title.setObjectName('section-title')
        title_layout.addWidget(title)
        
        # 全选按钮
        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.toggle_select_all)
        title_layout.addWidget(self.select_all_btn)
        
        header_layout.addLayout(title_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('搜索联系人...')
        self.search_input.setObjectName('contact-search')
        self.search_input.textChanged.connect(self.filter_contacts)
        
        # 搜索历史自动完成
        completer = QCompleter()
        self.search_model = QStringListModel()
        completer.setModel(self.search_model)
        self.search_input.setCompleter(completer)
        
        # 搜索框右键菜单
        self.search_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self.search_input.customContextMenuRequested.connect(self.show_search_menu)
        
        search_layout.addWidget(self.search_input)
        
        # 清空按钮
        clear_btn = QPushButton('×')
        clear_btn.setFixedSize(20, 20)
        clear_btn.setObjectName('clear-search')
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        
        header_layout.addLayout(search_layout)
        contact_layout.addWidget(header_frame)
        
        # 联系人列表
        self.contact_list = QListWidget()
        self.contact_list.setObjectName('contact-list')
        contact_layout.addWidget(self.contact_list)
        
        parent_layout.addWidget(contact_frame)

    def add_test_contacts(self):
        """添加测试联系人数据"""
        test_contacts = [
            ("张三", "wxid_001"),
            ("李四", "wxid_002"),
            ("王五", "wxid_003"),
            ("赵六", "wxid_004"),
        ]
        
        for name, wxid in test_contacts:
            item = QListWidgetItem(self.contact_list)
            contact_widget = ContactItem(name, wxid)
            item.setSizeHint(contact_widget.sizeHint())
            self.contact_list.addItem(item)
            self.contact_list.setItemWidget(item, contact_widget)

    def filter_contacts(self, text):
        """过滤联系人列表"""
        # 更新搜索历史
        if text and text != self.search_input.placeholderText():
            self.search_helper.add_history(text)
            self.update_completer()
        
        # 过滤并高亮显示结果
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            contact_name = widget.name_label.text()
            
            if self.search_helper.match_contact(text, contact_name):
                item.setHidden(False)
                widget.highlight_text(text)
            else:
                item.setHidden(True)
                widget.highlight_text("")

    def toggle_select_all(self, checked):
        """切换全选状态"""
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            if not item.isHidden():
                widget.checkbox.setChecked(checked)

    def get_selected_contacts(self):
        """获取选中的联系人"""
        selected = []
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            if widget.checkbox.isChecked():
                selected.append(widget)
        return selected

    def show_api_config(self):
        """显示API配置对话框"""
        dialog = APIConfigDialog(self)
        dialog.set_config(self.config)  # 设置当前配置
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()  # 获取新的配置
            
    def get_message_time_range(self):
        """获取消息记录的时间范围"""
        return {
            'start_date': self.config.get('start_date', ''),
            'end_date': self.config.get('end_date', '')
        }

    def show_custom_prompt(self):
        """显示自定义提示词对话框"""
        dialog = CustomPromptDialog(self)
        # 如果已有自定义提示词，显示在对话框中
        if hasattr(self, 'custom_prompt') and self.custom_prompt:
            dialog.prompt_input.setPlainText(self.custom_prompt)
            
        if dialog.exec_() == QDialog.Accepted:
            prompt = dialog.prompt_input.toPlainText().strip()
            if prompt:
                self.custom_prompt = prompt
                # 更新当前风格为自定义
                self.current_style = 'custom'
                self.custom_btn.setChecked(True)
                # 更新结果显示区的自定义提示词
                if hasattr(self, 'result_display'):
                    current_version = self.result_display.current_version
                    if current_version:
                        current_version['style'] = 'custom'
                        current_version['custom_prompt'] = prompt
                        self.result_display.update_content(current_version)
            else:
                # 如果用户清空了提示词，恢复到默认风格
                self.custom_prompt = ''
                self.current_style = 'formal'
                self.formal_btn.setChecked(True)
                QMessageBox.warning(self, '提示', '自定义提示词不能为空，已恢复为正式风格')
            
    def get_style_prompt(self):
        """根据当前风格获取提示词"""
        print(f"\n=== 获取风格提示词 ===")
        print(f"当前风格: {self.current_style}")
        
        if self.current_style == 'custom':
            if not self.custom_prompt:
                print("自定义风格但无提示词，使用默认风格")
                return self.get_style_prompt_by_style('formal')
            print(f"使用自定义提示词: {self.custom_prompt}")
            return self.custom_prompt
            
        # 使用预设风格
        prompt = self.get_style_prompt_by_style(self.current_style)
        print(f"使用预设风格提示词: {prompt}")
        return prompt
        
    def update_style(self, style):
        """更新当前风格"""
        print(f"\n=== 更新风格 ===")
        print(f"新风格: {style}")
        self.current_style = style
        # 清除之前的自定义提示词
        if style != 'custom':
            self.custom_prompt = ''
        print(f"当前风格: {self.current_style}")
        print(f"自定义提示词: {self.custom_prompt}")
        print("=== 风格更新完成 ===\n")
        
    def init_content_area(self, parent_layout):
        """初始化主要内容区域"""
        # 创建结果展示组件
        self.result_display = ResultDisplay(version_manager=self.version_manager)
        
        # 连接信号
        self.result_display.regenerate_requested.connect(self.generate_greetings)
        self.result_display.version_selected.connect(self.load_version)
        self.result_display.export_requested.connect(self.export_content)
        
        parent_layout.addWidget(self.result_display)
        
    def init_footer(self, parent_layout):
        """初始化底部操作区"""
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(16)  # 增加按钮间距
        
        # 左侧的风格设置
        style_group = QFrame()
        style_layout = QHBoxLayout(style_group)
        
        # 添加模板选择
        template_layout = QHBoxLayout()
        template_label = QLabel('选择模板：')
        self.template_combo = QComboBox()
        self.template_combo.addItems(['模板1', '模板2'])
        self.template_combo.currentIndexChanged.connect(self.update_template)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        style_layout.addLayout(template_layout)
        
        style_layout.addWidget(QLabel('选择生成风格：'))
        
        # 风格选项
        self.formal_btn = StyleButton('正式')
        self.warm_btn = StyleButton('温馨')
        self.humor_btn = StyleButton('幽默')
        self.literary_btn = StyleButton('文艺')
        self.custom_btn = StyleButton('自定义')
        
        # 连接风格按钮的点击事件
        self.formal_btn.clicked.connect(lambda: self.update_style('formal'))
        self.warm_btn.clicked.connect(lambda: self.update_style('warm'))
        self.humor_btn.clicked.connect(lambda: self.update_style('humor'))
        self.literary_btn.clicked.connect(lambda: self.update_style('literary'))
        self.custom_btn.clicked.connect(self.show_custom_prompt)
        
        # 设置默认选中的风格
        self.formal_btn.setChecked(True)
        
        style_layout.addWidget(self.formal_btn)
        style_layout.addWidget(self.warm_btn)
        style_layout.addWidget(self.humor_btn)
        style_layout.addWidget(self.literary_btn)
        style_layout.addWidget(self.custom_btn)
        
        footer_layout.addWidget(style_group)
        footer_layout.addStretch()
        
        # 添加签名输入框
        signature_layout = QHBoxLayout()
        signature_label = QLabel('签名：')
        self.signature_input = QLineEdit()
        self.signature_input.setPlaceholderText('请输入您的签名')
        self.signature_input.setMaximumWidth(150)  # 限制最大宽度
        signature_layout.addWidget(signature_label)
        signature_layout.addWidget(self.signature_input)
        footer_layout.addLayout(signature_layout)
        
        # 右侧的操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)  # 设置按钮间距
        
        self.generate_btn = QPushButton('生成')
        self.generate_btn.setObjectName('primary-button')
        self.generate_btn.clicked.connect(self.generate_greetings)
        button_layout.addWidget(self.generate_btn)
        
        # 添加发送至微信按钮
        self.send_wechat_btn = QPushButton('发送至微信')
        self.send_wechat_btn.setObjectName('primary-button')
        self.send_wechat_btn.clicked.connect(self.send_to_wechat)
        button_layout.addWidget(self.send_wechat_btn)
        
        footer_layout.addLayout(button_layout)
        
        parent_layout.addLayout(footer_layout)
        
    def set_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9F4E6;
            }
            #title {
                font-family: '思源黑体';
                font-size: 24px;
                font-weight: bold;
                color: #D4341F;
            }
            #section-title {
                font-family: '思源黑体';
                font-size: 18px;
                font-weight: bold;
                color: #333333;
                margin: 16px 0 8px 0;
            }
            #contact-frame {
                background-color: white;
                border-radius: 8px;
                margin-right: 16px;
            }
            #contact-list {
                border: none;
                background-color: transparent;
            }
            #contact-list::item {
                padding: 4px;
            }
            #contact-list::item:hover {
                background-color: #F5F5F5;
            }
            QPushButton {
                background-color: #E8C06F;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D4B05F;
            }
            QPushButton:checked {
                background-color: #D4341F;
                color: white;
            }
            #primary-button {
                background-color: #D4341F;
                color: white;
                font-weight: bold;
                padding: 10px 24px;
            }
            #primary-button:hover {
                background-color: #A61F14;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #E8C06F;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QTextEdit {
                min-height: 100px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #E8C06F;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #D4341F;
                border-color: #D4341F;
            }
            #contact-search {
                padding: 4px 8px;
                border: 1px solid #E8C06F;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            #clear-search {
                background: transparent;
                color: #666666;
                border: none;
                padding: 0;
                font-size: 14px;
            }
            #clear-search:hover {
                color: #D4341F;
            }
        """) 
        
    def validate_config(self):
        """验证配置是否完整"""
        if not self.config.get('api_key'):
            QMessageBox.warning(self, '提示', '请先配置火山引擎API Key')
            return False
        if not self.config.get('start_date') or not self.config.get('end_date'):
            QMessageBox.warning(self, '提示', '请先配置消息记录时间范围')
            return False
            
        # 检查自定义风格
        if self.current_style == 'custom' and not self.custom_prompt:
            QMessageBox.warning(self, '提示', '您选择了自定义风格，请先填写自定义提示词')
            self.show_custom_prompt()  # 直接打开自定义提示词对话框
            return False
            
        return True
        
    def get_selected_contacts_info(self):
        """获取选中联系人的详细信息"""
        selected = []
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            if widget.checkbox.isChecked():
                # 获取联系人头像
                avatar_data = None
                try:
                    avatar_data = self.data_processor.get_contact_avatar(widget.contact_id)
                except Exception as e:
                    print(f"获取头像失败：{str(e)}")
                    
                selected.append({
                    'wxid': widget.contact_id,
                    'name': widget.name_label.text(),
                    'avatar': avatar_data  # 保留头像数据用于展示
                })
        return selected
        
    def load_contacts(self):
        """加载联系人列表"""
        try:
            print("[MainWindow] 开始加载联系人列表")
            contacts = self.data_processor.get_all_contacts()
            print(f"[MainWindow] 成功获取联系人列表，共 {len(contacts)} 个联系人")
            self.contact_list.clear()
            
            for contact in contacts:
                print(f"\n[MainWindow] 处理联系人 - 名称: {contact['name']}, ID: {contact['wxid']}")
                item = QListWidgetItem(self.contact_list)
                contact_widget = ContactItem(contact['original_name'] if 'original_name' in contact else contact['name'], contact['wxid'])
                
                # 获取联系人头像
                try:
                    print(f"[MainWindow] 尝试获取头像 - 联系人ID: {contact['wxid']}")
                    avatar_data = self.data_processor.get_contact_avatar(contact['wxid'])
                    if avatar_data:
                        print(f"[MainWindow] 成功获取头像数据 - 联系人ID: {contact['wxid']}, 数据大小: {len(avatar_data)} 字节")
                        contact_widget.set_avatar(avatar_data)
                    else:
                        print(f"[MainWindow] 未获取到头像数据 - 联系人ID: {contact['wxid']}")
                except Exception as e:
                    print(f"[MainWindow] 获取头像失败 - 联系人ID: {contact['wxid']}, 错误: {str(e)}")
                
                item.setSizeHint(contact_widget.sizeHint())
                self.contact_list.addItem(item)
                self.contact_list.setItemWidget(item, contact_widget)
                
            print("[MainWindow] 联系人列表加载完成")
        except Exception as e:
            print(f"[MainWindow] 加载联系人列表失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载联系人列表失败: {str(e)}")
            
    def generate_greetings(self, regenerate_info=None):
        """生成祝福"""
        print("\n=== 开始生成祝福 ===")
        # 验证配置
        if not self.validate_config():
            return
            
        # 获取要生成的联系人信息
        if regenerate_info:
            print("重新生成模式")
            selected_contacts = [regenerate_info['contact']]
            # 使用传入的风格
            style = regenerate_info.get('style', self.current_style)  # 默认使用当前选中的风格
            print(f"使用传入的风格: {style}")
            
            if style == 'custom':
                style_prompt = regenerate_info.get('custom_prompt', self.custom_prompt)  # 默认使用当前的自定义提示词
                if not style_prompt:
                    print("错误：未提供自定义提示词")
                    QMessageBox.warning(self, '提示', '请先填写自定义风格内容')
                    return
                print(f"使用传入的自定义提示词: {style_prompt}")
            else:
                style_prompt = self.get_style_prompt_by_style(style)
                print(f"使用预设风格提示词: {style_prompt}")
        else:
            print("新生成模式")
            selected_contacts = self.get_selected_contacts_info()
            if not selected_contacts:
                QMessageBox.warning(self, '提示', '请至少选择一个联系人')
                return
            # 使用当前选择的风格
            style = self.current_style
            style_prompt = self.get_style_prompt()
            print(f"使用当前风格: {style}")
            print(f"使用当前风格提示词: {style_prompt}")
            
        # 获取时间范围
        time_range = self.get_message_time_range()
        
        try:
            # 创建API实例
            api = VolcanoAPI(self.config['api_key'])
            
            # 禁用生成按钮
            self.generate_btn.setEnabled(False)
            
            # 创建进度对话框
            progress = QProgressDialog("准备生成...", "取消", 0, 100, self)
            progress.setWindowTitle("生成进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setAutoReset(True)
            progress.show()
            QApplication.processEvents()
            
            # 为每个选中的联系人创建生成任务
            for contact in selected_contacts:
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(f"正在为 {contact['name']} 生成祝福...")
                QApplication.processEvents()
                
                # 创建工作线程
                worker = GenerateWorker(
                    api,
                    self.data_processor,
                    contact,
                    time_range,
                    style_prompt
                )
                
                # 连接信号
                worker.progress.connect(progress.setValue)
                worker.result.connect(lambda r, c=contact: self.handle_generation_result(r, c, style, style_prompt))  # 传递风格信息
                worker.finished.connect(lambda s, e, c=contact: self.handle_generation_finished(c['wxid'], s, e))
                
                # 启动工作线程
                worker.start()
                
                # 等待完成
                while not worker.isFinished():
                    QApplication.processEvents()
                    QThread.msleep(100)
                    
        except Exception as e:
            QMessageBox.critical(self, '错误', f'生成失败：{str(e)}')
        finally:
            # 恢复生成按钮
            self.generate_btn.setEnabled(True)
            
    def handle_generation_result(self, result, contact_info, style, style_prompt):
        """处理生成结果"""
        print("\n=== 处理生成结果 ===")
        print(f"当前风格: {style}")
        print(f"当前模板: {self.current_template}")
        print(f"联系人信息: {contact_info['name']} ({contact_info['wxid']})")
        
        # 创建版本信息，包含头像数据用于展示
        version_info = {
            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'style': style,
            'contact': {
                'wxid': contact_info['wxid'],
                'name': contact_info['name'],
                'avatar': contact_info.get('avatar', None)  # 保留头像数据用于展示
            },
            'greeting': result.get('greeting', ''),  # 新年祝福寄语
            'poem': result.get('idioms', ''),       # 新年祝福诗
            'idioms': result.get('tags', ''),       # 新年祝福成语
            'wishes': result.get('wishes', ''),     # 新年祝福愿望
            'template_number': self.current_template
        }
        print(f"\n1. 版本信息已创建")
        
        try:
            # 准备注入到模板的数据
            template_data = {
                'greeting_text': result.get('greeting', ''),  # 新年祝福寄语
                'poem_text': result.get('idioms', ''),     # 新年祝福诗（原来是成语的内容）
                'idioms_text': result.get('tags', ''),     # 新年祝福成语
                'wishes_text': result.get('wishes', ''),      # 新年祝福愿望
                'signature': self.signature_input.text() or contact_info['name'],  # 优先使用用户输入的签名，如果没有则使用联系人名称
                'year': '2025',                              # 年份
            }
            print(f"\n2. 模板数据已准备")
            
            # 确保generate_img目录存在
            if not os.path.exists('newYear/generate_img'):
                os.makedirs('newYear/generate_img')
                print(f"\n3. 创建generate_img目录")
            else:
                print(f"\n3. generate_img目录已存在")
            
            # 生成图片文件名
            img_filename = f"{contact_info['wxid']}.png"
            img_path = os.path.join('newYear/generate_img', img_filename)
            print(f"\n4. 图片将保存至: {img_path}")
            
            # 使用generate_card生成图片
            print(f"\n5. 开始生成贺卡图片...")
            print(f"   - 使用模板: {self.current_template}")
            print(f"   - 用户ID: {contact_info['wxid']}")
            img_path = generate_card(
                template_number=self.current_template,
                data=template_data,
                user_id=contact_info['wxid']
            )
            print(f"\n6. 贺卡图片生成完成: {img_path}")
            
            # 将图片路径添加到版本信息中
            version_info['image_path'] = img_path
            
            # 更新JSON文件
            json_path = os.path.join('newYear/version_history', f"{contact_info['wxid']}.json")
            print(f"\n7. 准备更新JSON文件: {json_path}")
            
            # 读取现有的JSON文件（如果存在）
            existing_data = []
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 确保data是列表类型
                        if isinstance(data, list):
                            existing_data = data
                        elif isinstance(data, dict):
                            # 如果是旧格式（字典），将其转换为列表
                            if 'latest_version' in data:
                                existing_data = [data['latest_version']]
                        print(f"8. 成功读取现有JSON文件")
                except json.JSONDecodeError:
                    print(f"Warning: 无法解析现有的JSON文件: {json_path}")
                except Exception as e:
                    print(f"Warning: 读取JSON文件时出错: {str(e)}")
            
            # 创建用于保存的数据副本，移除二进制数据
            save_version_info = {
                'create_time': version_info['create_time'],
                'style': version_info['style'],
                'contact': {
                    'wxid': contact_info['wxid'],
                    'name': contact_info['name']
                },
                'greeting': version_info['greeting'],  # 新年祝福寄语
                'poem': version_info['poem'],         # 新年祝福诗
                'idioms': version_info['idioms'],     # 新年祝福成语
                'wishes': version_info['wishes'],     # 新年祝福愿望
                'template_number': version_info['template_number'],
                'image_path': version_info['image_path']
            }
            
            # 保存风格相关内容
            if style == 'custom':
                save_version_info['custom_prompt'] = style_prompt
                save_version_info['style_content'] = style_prompt
            else:
                save_version_info['style_prompt'] = style_prompt
                save_version_info['style_content'] = style_prompt
            
            # 添加新版本到数组
            existing_data.append(save_version_info)
            
            # 确保version_history目录存在
            version_history_dir = os.path.dirname(json_path)
            if not os.path.exists(version_history_dir):
                os.makedirs(version_history_dir)
                
            # 保存更新后的JSON文件
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)
                print(f"\n10. JSON文件已保存")
            except Exception as e:
                print(f"Error: 保存JSON文件失败: {str(e)}")
                raise
            
        except Exception as e:
            error_msg = f"生成贺卡图片失败: {str(e)}"
            print(f"\nError: {error_msg}")
            QMessageBox.warning(self, '警告', error_msg)
            version_info['image_path'] = None
            return
        
        # 保存风格内容
        if style == 'custom':
            print(f"\n11. 保存自定义提示词: {style_prompt}")
            version_info['custom_prompt'] = style_prompt
            version_info['style_content'] = style_prompt
        else:
            print(f"\n11. 保存预设风格提示词: {style_prompt}")
            version_info['style_prompt'] = style_prompt
            version_info['style_content'] = style_prompt
        
        # 添加到版本管理器
        print(f"\n12. 添加到版本管理器")
        self.version_manager.add_version(version_info)
        
        # 更新结果显示
        print(f"\n13. 更新结果显示")
        self.result_display.update_content(version_info)
        
        # 刷新版本历史
        print(f"\n14. 刷新版本历史")
        self.result_display.load_version_history()
        
        # 更新联系人状态
        print(f"\n15. 更新联系人状态")
        self.update_contact_status(contact_info['wxid'], True)
        print("=== 生成结果处理完成 ===\n")
        
    def handle_generation_finished(self, contact_id, success, error_msg):
        """处理生成完成事件"""
        if success:
            self.update_contact_status(contact_id, True)
        else:
            QMessageBox.warning(self, '提示', f'生成失败：{error_msg}')
            self.update_contact_status(contact_id, False)
            
    def update_contact_status(self, contact_id, generated):
        """更新联系人的生成状态"""
        for i in range(self.contact_list.count()):
            item = self.contact_list.item(i)
            widget = self.contact_list.itemWidget(item)
            if widget.contact_id == contact_id:
                widget.set_generated(generated)
                break 

    def show_search_menu(self, pos):
        """显示搜索框右键菜单"""
        menu = QMenu(self)
        
        # 添加搜索历史
        if self.search_helper.search_history:
            history_menu = menu.addMenu('搜索历史')
            for keyword in reversed(self.search_helper.search_history):
                action = history_menu.addAction(keyword)
                action.triggered.connect(lambda x, k=keyword: self.use_history(k))
            
            menu.addSeparator()
            clear_action = menu.addAction('清空搜索历史')
            clear_action.triggered.connect(self.clear_history)
        
        menu.exec_(self.search_input.mapToGlobal(pos))
        
    def use_history(self, keyword):
        """使用历史搜索关键词"""
        self.search_input.setText(keyword)
        
    def clear_history(self):
        """清空搜索历史"""
        self.search_helper.clear_history()
        self.update_completer()
        
    def clear_search(self):
        """清空搜索框"""
        self.search_input.clear()
        
    def update_completer(self):
        """更新自动完成器"""
        self.search_model.setStringList(self.search_helper.search_history)
        
    def load_version(self, version_info):
        """加载指定版本"""
        self.result_display.update_content(version_info)
        
    def export_content(self, content):
        """导出内容"""
        self.result_display.export_content(content)
        
    def compare_versions(self):
        """显示版本比较对话框"""
        # 获取所有版本数据
        versions = self.version_manager.get_all_versions()
        if not versions:
            QMessageBox.information(self, "提示", "暂无可比较的版本")
            return
            
        dialog = VersionCompareDialog(versions, self)
        dialog.exec_()
        
    def get_style_prompt_by_style(self, style):
        """根据风格获取提示词"""
        style_prompts = {
            'formal': '正式、庄重、专业的新年祝福，使用恰当的敬语和礼貌用语',
            'warm': '温暖、亲切、感人的新年祝福，表达真挚的关心和美好祝愿',
            'humor': '幽默、轻松、有趣的新年祝福，让人会心一笑',
            'literary': '文艺、优美、富有诗意的新年祝福，使用优美的文学语言',
            'custom': self.custom_prompt
        }
        return style_prompts.get(style, style_prompts['formal'])

    def update_template(self, index):
        """更新当前选择的模板"""
        self.current_template = index + 1
        print(f"当前选择的模板: {self.current_template}")
        
    def send_to_wechat(self):
        """发送贺卡到微信"""
        # 获取选中的联系人
        selected_contacts = self.get_selected_contacts()
        if not selected_contacts:
            QMessageBox.warning(self, '提示', '请至少选择一个联系人')
            return
            
        # 导入发送消息的方法
        try:
            from newYear.utils.wx_util import send_message_and_image
        except ImportError as e:
            QMessageBox.critical(self, '错误', f'导入发送消息模块失败：{str(e)}')
            return
            
        # 记录发送失败的联系人
        failed_contacts = []
        
        # 显示进度对话框
        progress = QProgressDialog("正在发送消息...", "取消", 0, len(selected_contacts), self)
        progress.setWindowTitle("发送进度")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        for i, contact in enumerate(selected_contacts):
            if progress.wasCanceled():
                break
                
            progress.setValue(i)
            progress.setLabelText(f"正在发送给联系人 {contact.contact_id}...")
            QApplication.processEvents()
            
            try:
                # 读取联系人的JSON数据
                json_path = os.path.join('newYear/version_history', f"{contact.contact_id}.json")
                if not os.path.exists(json_path):
                    failed_contacts.append(f"{contact.contact_id} (无生成记录)")
                    continue
                    
                with open(json_path, 'r', encoding='utf-8') as f:
                    versions = json.load(f)
                    
                if not versions:
                    failed_contacts.append(f"{contact.contact_id} (无版本记录)")
                    continue
                    
                # 获取最新版本（数组中的最后一个元素）
                latest_version = versions[-1]
                    
                # 获取图片路径
                image_path = latest_version.get('image_path')
                name = latest_version.get('contact').get('name')
                if not image_path or not os.path.exists(image_path):
                    failed_contacts.append(f"{contact.contact_id} (图片不存在)")
                    continue
                    
                # 发送消息和图片
                success = send_message_and_image(name, image_path)
                if not success:
                    failed_contacts.append(f"{contact.contact_id} (发送失败)")
                    
            except Exception as e:
                print(f"发送失败 - 联系人: {name}, 错误: {str(e)}")
                failed_contacts.append(f"{contact.contact_id}-{name} (错误: {str(e)})")
                
        progress.setValue(len(selected_contacts))
        
        # 显示发送结果
        if failed_contacts:
            failed_msg = "\n".join(failed_contacts)
            QMessageBox.warning(
                self,
                '发送结果',
                f'以下联系人发送失败：\n\n{failed_msg}'
            )
        else:
            QMessageBox.information(
                self,
                '发送结果',
                '所有消息发送成功！'
            )

    def export_to_desktop(self):
        """导出选中联系人的数据到桌面"""
        # 获取选中的联系人
        selected_contacts = self.get_selected_contacts()
        if not selected_contacts:
            QMessageBox.warning(self, '提示', '请先选择要导出的联系人')
            return
            
        try:
            # 获取桌面路径
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            export_folder = os.path.join(desktop_path, '2025新年祝福整理')
            
            # 创建导出文件夹
            os.makedirs(export_folder, exist_ok=True)
            
            # 显示进度对话框
            progress = QProgressDialog("正在导出数据...", "取消", 0, len(selected_contacts), self)
            progress.setWindowTitle("导出进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # 获取版本管理器
            version_manager = VersionManager()
            failed_contacts = []  # 记录导出失败的联系人
            
            # 遍历选中的联系人
            for i, contact in enumerate(selected_contacts):
                if progress.wasCanceled():
                    break
                    
                contact_id = contact.contact_id
                contact_name = contact.name_label.text()
                
                # 处理文件名中的非法字符
                safe_name = "".join(c for c in contact_name if c.isalnum() or c in (' ', '_', '-', '(', ')'))
                if not safe_name:
                    safe_name = contact_id
                
                progress.setValue(i)
                progress.setLabelText(f"正在导出 {contact_name} 的数据...")
                QApplication.processEvents()
                
                try:
                    # 创建联系人文件夹
                    contact_folder = os.path.join(export_folder, safe_name)
                    os.makedirs(contact_folder, exist_ok=True)
                    
                    # 获取联系人的所有版本
                    versions = version_manager.get_contact_versions(contact_id)
                    if versions:
                        # 处理版本数据，移除二进制内容
                        export_versions = []
                        for version in versions:
                            export_version = version.copy()
                            if 'contact' in export_version:
                                contact_data = export_version['contact'].copy()
                                contact_data.pop('avatar', None)  # 移除头像数据
                                export_version['contact'] = contact_data
                            export_versions.append(export_version)
                        
                        # 导出json文件
                        json_path = os.path.join(contact_folder, f"{safe_name}.json")
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(export_versions, f, ensure_ascii=False, indent=2)
                        
                        # 导出最新版本的图片
                        latest_version = versions[-1]
                        if 'image_path' in latest_version:
                            original_image = latest_version['image_path']
                            if os.path.exists(original_image):
                                image_name = os.path.basename(original_image)
                                new_image_path = os.path.join(contact_folder, image_name)
                                import shutil
                                shutil.copy2(original_image, new_image_path)
                    else:
                        failed_contacts.append(f"{contact_name} (无生成记录)")
                        
                except Exception as e:
                    print(f"导出失败 - 联系人: {contact_name}, 错误: {str(e)}")
                    failed_contacts.append(f"{contact_name} (错误: {str(e)})")
            
            progress.setValue(len(selected_contacts))
            
            # 显示导出结果
            if failed_contacts:
                failed_msg = "\n".join(failed_contacts)
                QMessageBox.warning(
                    self,
                    '导出结果',
                    f'部分联系人导出失败：\n\n{failed_msg}\n\n其他联系人已成功导出到桌面的"2025新年祝福整理"文件夹'
                )
            else:
                QMessageBox.information(self, '导出成功', f'数据已成功导出到桌面的"2025新年祝福整理"文件夹')
            
            # 打开导出文件夹
            os.startfile(export_folder)
            
        except Exception as e:
            QMessageBox.critical(self, '导出失败', f'导出过程中发生错误：{str(e)}') 