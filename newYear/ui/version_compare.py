from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QPushButton, QTextEdit, QFrame,
                           QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor
import difflib

class VersionCompareDialog(QDialog):
    """版本比较对话框"""
    
    def __init__(self, versions, parent=None):
        super().__init__(parent)
        # 按联系人分组版本
        self.contact_versions = self.group_versions_by_contact(versions)
        self.init_ui()
        self.apply_style()
        
    def group_versions_by_contact(self, versions):
        """将版本按联系人分组
        Returns:
            Dict[str, List[Dict]]: 以联系人wxid为键，版本列表为值的字典
        """
        grouped = {}
        for version in versions:
            contact = version['contact']
            wxid = contact['wxid']
            if wxid not in grouped:
                grouped[wxid] = []
            grouped[wxid].append(version)
        return grouped
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("版本比较")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 联系人选择
        contact_layout = QHBoxLayout()
        contact_layout.addWidget(QLabel("选择联系人："))
        self.contact_combo = QComboBox()
        self.contact_combo.currentIndexChanged.connect(self.on_contact_changed)
        contact_layout.addWidget(self.contact_combo)
        layout.addLayout(contact_layout)
        
        # 版本选择区域
        select_layout = QHBoxLayout()
        
        # 版本A选择
        version_a_layout = QVBoxLayout()
        version_a_layout.addWidget(QLabel("版本A："))
        self.version_a_combo = QComboBox()
        self.version_a_combo.currentIndexChanged.connect(self.compare_versions)
        version_a_layout.addWidget(self.version_a_combo)
        select_layout.addLayout(version_a_layout)
        
        # 版本B选择
        version_b_layout = QVBoxLayout()
        version_b_layout.addWidget(QLabel("版本B："))
        self.version_b_combo = QComboBox()
        self.version_b_combo.currentIndexChanged.connect(self.compare_versions)
        version_b_layout.addWidget(self.version_b_combo)
        select_layout.addLayout(version_b_layout)
        
        layout.addLayout(select_layout)
        
        # 比较结果区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("compare-scroll")
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        # 各部分内容比较
        self.add_compare_section("新年祝福语", "greeting")
        self.add_compare_section("美好祝愿", "wishes")
        self.add_compare_section("祝福成语", "idioms")
        self.add_compare_section("新年图片提示词", "image_prompt")
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("close-btn")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # 初始化联系人列表
        self.init_contacts()
        
    def init_contacts(self):
        """初始化联系人列表"""
        self.contact_combo.clear()
        for wxid, versions in self.contact_versions.items():
            if versions:  # 确保有版本数据
                contact_name = versions[0]['contact']['name']  # 使用第一个版本中的联系人名称
                self.contact_combo.addItem(contact_name, wxid)  # 使用wxid作为用户数据
                
    def on_contact_changed(self, index):
        """联系人选择改变时的处理"""
        if index < 0:
            return
            
        # 获取选中联系人的wxid
        wxid = self.contact_combo.currentData()
        versions = self.contact_versions.get(wxid, [])
        
        # 更新版本选择框
        self.version_a_combo.clear()
        self.version_b_combo.clear()
        
        contact_name = versions[0]['contact']['name']
        for version in versions:
            version_text = f"{contact_name} - 版本{version['version_number']} ({version['create_time']})"
            self.version_a_combo.addItem(version_text, version)
            self.version_b_combo.addItem(version_text, version)
            
        # 默认选择最新的两个版本
        if len(versions) >= 2:
            self.version_a_combo.setCurrentIndex(len(versions) - 2)
            self.version_b_combo.setCurrentIndex(len(versions) - 1)
            
    def add_compare_section(self, title, content_key):
        """添加比较部分"""
        section = QWidget()
        layout = QVBoxLayout(section)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # 内容比较区域
        content_layout = QHBoxLayout()
        
        # 版本A内容
        text_a = QTextEdit()
        text_a.setReadOnly(True)
        setattr(self, f"{content_key}_a", text_a)
        content_layout.addWidget(text_a)
        
        # 版本B内容
        text_b = QTextEdit()
        text_b.setReadOnly(True)
        setattr(self, f"{content_key}_b", text_b)
        content_layout.addWidget(text_b)
        
        layout.addLayout(content_layout)
        self.content_layout.addWidget(section)
        
    def compare_versions(self):
        """比较选中的两个版本"""
        if self.version_a_combo.currentIndex() < 0 or self.version_b_combo.currentIndex() < 0:
            return
            
        version_a = self.version_a_combo.currentData()
        version_b = self.version_b_combo.currentData()
        
        if version_a and version_b:
            self.compare_content("greeting", version_a, version_b)
            self.compare_content("wishes", version_a, version_b)
            self.compare_content("idioms", version_a, version_b)
            self.compare_content("image_prompt", version_a, version_b)
        
    def compare_content(self, content_key, version_a, version_b):
        """比较特定内容"""
        text_a = version_a.get(content_key, '')
        text_b = version_b.get(content_key, '')
        
        # 获取文本框引用
        text_edit_a = getattr(self, f"{content_key}_a")
        text_edit_b = getattr(self, f"{content_key}_b")
        
        # 清空文本框
        text_edit_a.clear()
        text_edit_b.clear()
        
        # 计算差异
        differ = difflib.Differ()
        diff = list(differ.compare(text_a.splitlines(), text_b.splitlines()))
        
        # 设置差异高亮格式
        add_format = QTextCharFormat()
        add_format.setBackground(QColor(200, 255, 200))  # 浅绿色背景
        
        del_format = QTextCharFormat()
        del_format.setBackground(QColor(255, 200, 200))  # 浅红色背景
        
        # 显示差异
        cursor_a = text_edit_a.textCursor()
        cursor_b = text_edit_b.textCursor()
        
        for line in diff:
            if line.startswith('- '):
                cursor_a.insertText(line[2:] + '\n', del_format)
                cursor_b.insertText('\n')
            elif line.startswith('+ '):
                cursor_a.insertText('\n')
                cursor_b.insertText(line[2:] + '\n', add_format)
            else:
                cursor_a.insertText(line[2:] + '\n')
                cursor_b.insertText(line[2:] + '\n')
                
        # 滚动到顶部
        text_edit_a.verticalScrollBar().setValue(0)
        text_edit_b.verticalScrollBar().setValue(0)
        
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #F9F4E6;
                min-width: 800px;
                min-height: 600px;
            }
            QLabel {
                color: #333333;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #D4341F;
                padding: 10px;
            }
            QLabel#version-label {
                font-size: 16px;
                font-weight: bold;
                color: #D4341F;
                padding: 5px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #E8C06F;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #E8C06F;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #D4B05F;
            }
            QPushButton#close-btn {
                background-color: #D4341F;
                color: white;
            }
            QPushButton#close-btn:hover {
                background-color: #A61F14;
            }
        """) 