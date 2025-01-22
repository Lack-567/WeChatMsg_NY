from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTextEdit, QFrame, QScrollArea,
                           QGridLayout, QSpacerItem, QSizePolicy, QMenu,
                           QFileDialog, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon
import json
import os
from datetime import datetime

from .Icon import Icon
from newYear.utils.search_helper import SearchHelper  # 添加 SearchHelper 导入

class ResultDisplay(QWidget):
    """结果展示组件"""
    
    # 信号定义
    regenerate_requested = pyqtSignal(dict)  # 请求重新生成
    version_selected = pyqtSignal(dict)  # 版本被选中
    export_requested = pyqtSignal(dict)  # 请求导出
    
    def __init__(self, version_manager=None, parent=None):
        super().__init__(parent)
        self.current_version = None
        self.versions = []  # 存储所有版本
        self.version_manager = version_manager  # 保存版本管理器引用
        self.search_helper = SearchHelper()  # 初始化搜索助手
        self.parent_window = parent  # 保存父窗口引用
        self.init_ui()
        self.set_styles()  # 应用样式
        
        # 加载已有版本
        if self.version_manager:
            self.load_version_history()
            
    def init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 内容展示区（中间）
        content_area = QFrame()
        content_area.setObjectName("content-area")
        content_layout = QVBoxLayout(content_area)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 上部分（个人信息和风格）- 30%
        upper_frame = QFrame()
        upper_layout = QVBoxLayout(upper_frame)
        upper_layout.setSpacing(12)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        
        # 基础信息区
        self.init_basic_info(upper_layout)
        
        # 设置上部分的固定高度（整体高度的30%）
        upper_frame.setFixedHeight(int(self.height() * 0.3))
        content_layout.addWidget(upper_frame)
        
        # 下部分（生成内容）- 70%
        content_layout.addWidget(self.init_content_display(content_layout), stretch=7)
        
        # 操作按钮区
        self.init_action_buttons(content_layout)
        
        main_layout.addWidget(content_area, stretch=7)
        
        # 版本和工具栏（右侧）
        tools_area = QFrame()
        tools_area.setObjectName("tools-area")
        tools_area.setMinimumWidth(260)
        tools_area.setMaximumWidth(300)
        tools_layout = QVBoxLayout(tools_area)
        tools_layout.setSpacing(12)
        tools_layout.setContentsMargins(16, 16, 16, 16)
        
        # 版本列表
        self.init_version_history(tools_layout)
        
        # 工具按钮
        self.init_tools(tools_layout)
        
        main_layout.addWidget(tools_area, stretch=3)
        
    def init_basic_info(self, parent_layout):
        """初始化基础信息区"""
        info_frame = QFrame()
        info_frame.setObjectName("info-frame")
        info_frame.setFixedHeight(100)  # 固定高度
        info_layout = QHBoxLayout(info_frame)
        info_layout.setSpacing(8)  # 减小左右区域间距
        info_layout.setContentsMargins(20, 12, 20, 12)
        
        # 左侧：头像和基本信息
        left_frame = QFrame()
        left_frame.setFixedWidth(260)  # 减小左侧宽度
        left_layout = QHBoxLayout(left_frame)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 头像
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(60, 60)
        self.avatar_label.setObjectName("avatar")
        self.avatar_label.setScaledContents(True)
        self.avatar_label.setPixmap(Icon.get_default_avatar())
        left_layout.addWidget(self.avatar_label)
        
        # 联系人信息
        info_container = QVBoxLayout()
        info_container.setSpacing(4)
        info_container.setContentsMargins(0, 8, 0, 8)
        
        # 联系人名称
        self.name_label = QLabel()
        self.name_label.setObjectName("contact-name")
        info_container.addWidget(self.name_label)
        
        # 版本号
        version_container = QHBoxLayout()
        version_container.setSpacing(4)
        version_container.setContentsMargins(0, 0, 0, 0)  # 移除版本号容器的内边距
        
        version_icon = QLabel("📝")
        version_icon.setObjectName("meta-icon")
        version_container.addWidget(version_icon)
        
        self.version_label = QLabel()
        self.version_label.setObjectName("version-label")
        version_container.addWidget(self.version_label)
        version_container.addStretch()
        
        info_container.addLayout(version_container)
        left_layout.addLayout(info_container)
        
        # 右侧：生成风格
        style_container = QFrame()
        style_container.setObjectName("style-container")
        style_layout = QVBoxLayout(style_container)
        style_layout.setSpacing(2)  # 减小标题和内容的间距
        style_layout.setContentsMargins(12, 4, 12, 4)  # 减小内边距
        
        # 风格标题
        style_title = QHBoxLayout()
        style_title.setSpacing(4)
        style_title.setContentsMargins(0, 0, 0, 0)  # 移除标题的内边距
        
        style_icon = QLabel("✨")
        style_icon.setObjectName("meta-icon")
        style_title.addWidget(style_icon)
        
        title_label = QLabel("生成风格")
        title_label.setObjectName("style-title")
        style_title.addWidget(title_label)
        style_title.addStretch()
        
        style_layout.addLayout(style_title)
        
        # 创建滚动区域
        style_scroll = QScrollArea()
        style_scroll.setWidgetResizable(True)
        style_scroll.setObjectName("style-scroll")
        style_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        style_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)    # 需要时显示垂直滚动条
        style_scroll.setFrameShape(QFrame.NoFrame)  # 移除边框
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 风格内容
        self.custom_prompt_label = QLabel()
        self.custom_prompt_label.setObjectName("custom-prompt")
        self.custom_prompt_label.setWordWrap(True)
        self.custom_prompt_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(self.custom_prompt_label)
        content_layout.addStretch()
        
        style_scroll.setWidget(content_widget)
        style_layout.addWidget(style_scroll, 1)  # 添加拉伸因子
        
        # 将左右两部分添加到主布局
        info_layout.addWidget(left_frame)
        info_layout.addWidget(style_container, 1)  # 右侧占用剩余空间
        
        parent_layout.addWidget(info_frame)
        
    def init_content_display(self, parent_layout):
        """初始化内容展示区"""
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setObjectName("content-scroll")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 新年祝福寄语
        greeting_group = self.create_content_group("新年祝福寄语", "greeting")
        content_layout.addWidget(greeting_group)
        
        # 新年祝福诗
        poem_group = self.create_content_group("新年祝福诗", "poem")
        content_layout.addWidget(poem_group)
        
        # 新年祝福成语
        idioms_group = self.create_content_group("新年祝福成语", "idioms")
        content_layout.addWidget(idioms_group)
        
        # 新年祝福愿望
        wishes_group = self.create_content_group("新年祝福愿望", "wishes")
        content_layout.addWidget(wishes_group)
        
        content_scroll.setWidget(content_widget)
        parent_layout.addWidget(content_scroll)
        
    def create_content_group(self, title, content_type):
        """创建内容组"""
        group = QFrame()
        group.setObjectName(f"{content_type}-group")
        layout = QVBoxLayout(group)
        
        # 标题栏
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("content-title")
        header.addWidget(title_label)
        
        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.setObjectName("tool-button")
        copy_btn.clicked.connect(lambda: self.copy_content(content_type))
        header.addWidget(copy_btn)
        
        layout.addLayout(header)
        
        # 内容区
        content = QTextEdit()
        content.setObjectName(f"{content_type}-content")
        content.setReadOnly(True)
        setattr(self, f"{content_type}_text", content)
        layout.addWidget(content)
        
        return group
        
    def init_action_buttons(self, parent_layout):
        """初始化操作按钮区"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)  # 减小按钮间距
        
        # 重新生成按钮
        regenerate_btn = QPushButton("重新生成")
        regenerate_btn.setObjectName("primary-button")
        regenerate_btn.setFixedWidth(100)  # 固定按钮宽度
        regenerate_btn.clicked.connect(self.on_regenerate_clicked)
        button_layout.addWidget(regenerate_btn)
        
        # 导出按钮
        # export_btn = QPushButton("导出")
        # export_btn.setObjectName("secondary-button")
        # export_btn.setFixedWidth(80)  # 固定按钮宽度
        # export_btn.clicked.connect(self.on_export_clicked)
        # button_layout.addWidget(export_btn)
        
        button_layout.addStretch()  # 添加弹性空间，使按钮靠左对齐
        parent_layout.addLayout(button_layout)
        
    def init_version_history(self, parent_layout):
        """初始化版本历史区"""
        version_frame = QFrame()
        version_frame.setObjectName("version-frame")
        version_layout = QVBoxLayout(version_frame)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(8)
        
        # 版本列表标题和搜索区域
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        # 标题
        title = QLabel("版本历史")
        title.setObjectName("section-title")
        header_layout.addWidget(title)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setSpacing(4)
        self.version_search = QLineEdit()
        self.version_search.setPlaceholderText("搜索联系人...")
        self.version_search.setObjectName("version-search")
        self.version_search.textChanged.connect(self.filter_versions)
        search_layout.addWidget(self.version_search)
        
        # 清空搜索按钮
        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(16, 16)
        clear_btn.setObjectName("clear-search")
        clear_btn.clicked.connect(lambda: self.version_search.clear())
        search_layout.addWidget(clear_btn)
        
        header_layout.addLayout(search_layout)
        version_layout.addWidget(header_frame)
        
        # 版本列表
        version_scroll = QScrollArea()
        version_scroll.setWidgetResizable(True)
        version_scroll.setObjectName("version-scroll")
        version_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        version_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)    # 需要时显示垂直滚动条
        
        self.version_list = QWidget()
        version_list_layout = QVBoxLayout(self.version_list)
        version_list_layout.setContentsMargins(0, 0, 0, 0)
        version_list_layout.setSpacing(1)  # 设置项目间的间距
        version_list_layout.setAlignment(Qt.AlignTop)
        
        version_scroll.setWidget(self.version_list)
        version_layout.addWidget(version_scroll)
        
        # 版本比较按钮
        compare_btn = QPushButton("版本比较")
        compare_btn.setObjectName("tool-button")
        compare_btn.clicked.connect(self.on_compare_clicked)
        version_layout.addWidget(compare_btn)
        
        parent_layout.addWidget(version_frame)
        
    def filter_versions(self, text):
        """过滤版本列表"""
        text = text.lower()
        for i in range(self.version_list.layout().count()):
            widget = self.version_list.layout().itemAt(i).widget()
            if widget:
                name_label = widget.findChild(QLabel, "version-name")
                if name_label:
                    contact_name = name_label.text()
                    # 使用 SearchHelper 进行匹配
                    if self.search_helper.match_contact(text, contact_name):
                        widget.setVisible(True)
                    else:
                        widget.setVisible(False)
                    
    def init_tools(self, parent_layout):
        """初始化工具按钮"""
        # 移除此方法，因为版本比较按钮已经移到版本列表区域
        pass
        
    def set_contact_info(self, contact_info):
        """设置联系人信息"""
        if contact_info.get('avatar'):
            avatar_data = contact_info['avatar']
            pixmap = QPixmap()
            try:
                # 如果是字符串（base64编码），先解码
                if isinstance(avatar_data, str):
                    import base64
                    avatar_data = base64.b64decode(avatar_data)
                    
                # 根据图片格式加载数据
                if avatar_data[:4] == b'\x89PNG':
                    pixmap.loadFromData(avatar_data, format='PNG')
                else:
                    pixmap.loadFromData(avatar_data, format='JPEG')
                # 设置头像
                self.avatar_label.setPixmap(pixmap)
            except Exception as e:
                print(f"设置头像失败: {str(e)}")
                self.avatar_label.setPixmap(Icon.get_default_avatar())
        else:
            # 设置默认头像
            self.avatar_label.setPixmap(Icon.get_default_avatar())
        
        self.name_label.setText(contact_info.get('name', ''))
        
    def load_version_history(self):
        """加载版本历史"""
        # 获取所有版本数据
        all_versions = self.version_manager.get_all_versions()
        
        # 清空当前版本列表
        self.versions = []
        
        # 清空版本列表UI
        while self.version_list.layout().count():
            item = self.version_list.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # 添加所有版本，每个联系人只保留最新版本
        for wxid, versions in all_versions.items():
            if versions:  # 确保有版本
                # 按版本号排序，获取最新版本
                latest_version = max(versions, key=lambda x: x.get('version_number', 0))
                self.add_version(latest_version)
                
        # 如果有版本，显示最新的一个
        if self.versions:
            self.select_version(self.versions[-1])
            
    def update_content(self, version_info):
        """更新内容显示"""
        if not version_info:
            self.clear_content()
            return
            
        self.current_version = version_info
        
        # 更新联系人信息
        contact = version_info.get('contact', {})
        self.name_label.setText(contact.get('name', '未知联系人'))
        
        # 更新头像
        avatar_data = contact.get('avatar')
        if avatar_data:
            pixmap = QPixmap()
            pixmap.loadFromData(avatar_data)
            self.avatar_label.setPixmap(pixmap)
        else:
            self.avatar_label.setPixmap(Icon.get_default_avatar())
            
        # 更新版本信息
        create_time = version_info.get('create_time', '')
        if create_time:
            self.version_label.setText(f"版本 {create_time}")
            
        # 更新风格信息
        style = version_info.get('style', 'formal')
        if style == 'custom':
            self.custom_prompt_label.setText(version_info.get('custom_prompt', ''))
        else:
            self.custom_prompt_label.setText(self.get_style_display_text(style))
            
        # 更新各部分内容
        self.greeting_text.setText(version_info.get('greeting', ''))  # 新年祝福寄语
        self.poem_text.setText(version_info.get('poem', ''))         # 新年祝福诗
        self.idioms_text.setText(version_info.get('idioms', ''))     # 新年祝福成语
        self.wishes_text.setText(version_info.get('wishes', ''))     # 新年祝福愿望
        
        # 更新版本列表选中状态
        self.update_version_selection(version_info)
        
    def update_version_selection(self, version_info):
        """更新版本选中状态"""
        contact_id = version_info['contact']['wxid']
        for i in range(self.version_list.layout().count()):
            widget = self.version_list.layout().itemAt(i).widget()
            if widget:
                is_selected = (widget.property('contact_id') == contact_id)
                widget.setProperty('selected', is_selected)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                
    def select_version(self, version_info):
        """选择版本"""
        print("\n=== 开始选择版本 ===")
        print(f"选择版本: 联系人={version_info['contact'].get('name', '')}, 版本号=V{version_info.get('version_number', '')}")
        
        # 更新显示内容
        self.update_content(version_info)
        
        # 更新选中状态
        self.update_version_selection(version_info)
        print("=== 版本选择完成 ===\n")
        
    def copy_content(self, content_type):
        """复制内容到剪贴板"""
        text_edit = getattr(self, f"{content_type}_text", None)
        if text_edit:
            text_edit.selectAll()
            text_edit.copy()
            text_edit.clearSelection()
            QMessageBox.information(self, "提示", "内容已复制到剪贴板")
            
    def get_current_content(self):
        """获取当前内容"""
        if not self.current_version:
            return {}
            
        return {
            'greeting': self.greeting_text.toPlainText(),
            'poem': self.poem_text.toPlainText(),
            'idioms': self.idioms_text.toPlainText(),
            'wishes': self.wishes_text.toPlainText(),
            'contact': self.current_version.get('contact', {}),
            'style': self.current_version.get('style', ''),
            'create_time': self.current_version.get('create_time', ''),
            'custom_prompt': self.current_version.get('custom_prompt', '')
        }
        
    def on_regenerate_clicked(self):
        """重新生成按钮点击处理"""
        print("\n=== 开始重新生成流程 ===")
        
        if not self.current_version:
            print("错误：当前没有展示的内容")
            QMessageBox.information(self, "提示", "当前没有可重新生成的内容")
            return
            
        print(f"当前选中联系人: {self.current_version['contact'].get('name', '')}")
        print(f"当前版本号: V{self.current_version.get('version_number', '')}")
        
        # 获取主窗口当前选中的风格
        parent_window = self.window()
        if hasattr(parent_window, 'current_style'):
            style = parent_window.current_style
            print(f"使用主窗口当前风格: {style}")
        else:
            style = self.current_version.get('style', 'formal')
            print(f"未找到主窗口风格，使用当前版本风格: {style}")
        
        regenerate_info = {
            'contact': self.current_version['contact'],
            'style': style
        }
        
        # 根据风格类型添加相应的提示词
        if style == 'custom':
            if hasattr(parent_window, 'custom_prompt'):
                regenerate_info['custom_prompt'] = parent_window.custom_prompt
            else:
                regenerate_info['custom_prompt'] = self.current_version.get('custom_prompt', '')
        else:
            # 使用主窗口的预设风格提示词
            if hasattr(parent_window, 'get_style_prompt_by_style'):
                regenerate_info['style_prompt'] = parent_window.get_style_prompt_by_style(style)
            else:
                regenerate_info['style_prompt'] = self.current_version.get('style_content', '')
        
        print("发送重新生成信号，信息：", regenerate_info)
        self.regenerate_requested.emit(regenerate_info)
        print("=== 重新生成流程结束 ===\n")
        
    def get_style_display_text(self, style):
        """获取风格的显示文本"""
        style_texts = {
            'formal': '正式、庄重、专业的新年祝福，使用恰当的敬语和礼貌用语',
            'warm': '温暖、亲切、感人的新年祝福，表达真挚的关心和美好祝愿',
            'humor': '幽默、轻松、有趣的新年祝福，让人会心一笑',
            'literary': '文艺、优美、富有诗意的新年祝福，使用优美的文学语言'
        }
        return style_texts.get(style, '')
        
    def on_compare_clicked(self):
        """比较按钮点击处理"""
        if not self.current_version:
            QMessageBox.information(self, "提示", "请先在右侧版本历史中选择要比较的版本")
            return
            
        contact_id = self.current_version['contact']['wxid']
        # 获取该联系人的所有版本
        contact_versions = self.version_manager.get_contact_versions(contact_id)
        
        if len(contact_versions) < 2:
            QMessageBox.information(self, "提示", "需要至少有两个版本才能进行比较")
            return
            
        # 创建并显示版本比较对话框
        from .version_compare import VersionCompareDialog
        dialog = VersionCompareDialog(contact_versions, self)
        dialog.exec_()
        
    def on_export_clicked(self):
        """导出按钮点击处理"""
        if self.current_version:
            content = self.get_current_content()
            if content:
                content['contact'] = self.current_version['contact']
                self.export_requested.emit(content)
        
    def delete_version(self):
        """删除当前版本"""
        # 移除此方法
        
    def clear_content(self):
        """清空内容显示"""
        self.custom_prompt_label.clear()
        self.greeting_text.clear()  # 新年祝福寄语
        self.poem_text.clear()      # 新年祝福诗
        self.idioms_text.clear()    # 新年祝福成语
        self.wishes_text.clear()    # 新年祝福愿望
        
    def set_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            #content-area {
                background-color: white;
                border-radius: 12px;
                margin-right: 16px;
                border: 1px solid #E8E8E8;
            }
            #tools-area {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E8E8E8;
            }
            #info-frame {
                background-color: white;
                border: 1px solid #E8E8E8;
                border-radius: 8px;
                margin-bottom: 16px;
            }
            #avatar {
                border-radius: 24px;
                border: 2px solid #E8C06F;
                background-color: white;
            }
            #contact-name {
                font-family: '思源黑体';
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
            #version-label {
                font-size: 12px;
                color: #666666;
                background-color: #F5F5F5;
                padding: 2px 8px;
                border-radius: 4px;
                margin-top: 2px;
            }
            #meta-icon {
                font-size: 13px;
                color: #999999;
                margin-right: 4px;
            }
            #style-container {
                background-color: #F9F9F9;
                border-radius: 6px;
                min-width: 180px;
            }
            #custom-prompt {
                font-size: 13px;
                color: #666666;
                line-height: 1.4;
                padding: 4px 0;
            }
            #avatar-container {
                background: transparent;
                border-radius: 18px;
            }
            #version-avatar {
                border-radius: 18px;
                border: 1px solid #E8E8E8;
                background-color: white;
            }
            #version-item {
                background-color: white;
                border: 1px solid transparent;
                border-radius: 8px;
                margin: 4px 0;
                min-height: 80px;
                max-height: 80px;
            }
            #version-item:hover {
                background-color: #F9F4E6;
                border-color: #E8C06F;
            }
            #version-item[selected=true] {
                background-color: #F9F4E6;
                border-color: #E8C06F;
            }
            #primary-button {
                background-color: #D4341F;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            #primary-button:hover {
                background-color: #B32D1A;
            }
            #secondary-button {
                background-color: #E8C06F;
                color: #333333;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            #secondary-button:hover {
                background-color: #D4B05F;
            }
            #content-title {
                font-family: '思源黑体';
                font-size: 16px;
                font-weight: bold;
                color: #333333;
                margin: 16px 0 8px 0;
            }
            QTextEdit {
                border: 1px solid #E8C06F;
                border-radius: 8px;
                background-color: white;
                padding: 12px;
                font-family: '思源黑体';
                font-size: 14px;
                line-height: 1.5;
            }
            #tool-button {
                background-color: #F5F5F5;
                color: #333333;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            #tool-button:hover {
                background-color: #E8E8E8;
            }
            #version-button {
                background-color: white;
                color: #333333;
                border: 1px solid #E8E8E8;
                padding: 12px;
                border-radius: 8px;
                text-align: left;
                min-height: 50px;
            }
            #version-button:hover {
                background-color: #F9F4E6;
                border-color: #E8C06F;
            }
            #version-button[selected=true] {
                background-color: #F9F4E6;
                border-color: #E8C06F;
            }
            #version-name {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
            }
            #version-number {
                font-size: 12px;
                color: #666666;
                background-color: #F5F5F5;
                padding: 2px 8px;
                border-radius: 4px;
            }
            #version-time {
                color: #666666;
                font-size: 12px;
            }
            #version-list {
                background-color: transparent;
                border: none;
            }
            #version-scroll {
                border: none;
                background: transparent;
            }
            #version-search {
                padding: 6px 10px;
                border: 1px solid #E8E8E8;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
                color: #333333;
            }
            #version-search:focus {
                border-color: #E8C06F;
            }
            #clear-search {
                background: transparent;
                color: #999999;
                border: none;
                padding: 0;
                font-size: 12px;
                min-width: 16px;
                min-height: 16px;
            }
            #clear-search:hover {
                color: #D4341F;
            }
            #section-title {
                font-family: '思源黑体';
                font-size: 15px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 8px;
            }
        """) 

    def add_version(self, version_info):
        """添加新版本"""
        contact_id = version_info['contact']['wxid']
        
        # 检查是否已存在该联系人的版本项
        existing_version = None
        for i in range(self.version_list.layout().count()):
            widget = self.version_list.layout().itemAt(i).widget()
            if widget and widget.property('contact_id') == contact_id:
                existing_version = widget
                break
        
        if existing_version:
            # 更新现有版本项的显示
            version_number_label = existing_version.findChild(QLabel, "version-number")
            version_number_label.setText(f"V{version_info['version_number']}")
            time_label = existing_version.findChild(QLabel, "version-time")
            time_label.setText(version_info.get('create_time', '').split()[1])
            existing_version.mousePressEvent = lambda e, v=version_info: self.select_version(v)
            self.versions.append(version_info)
        else:
            # 创建新的版本项
            version_item = QFrame()
            version_item.setObjectName("version-item")
            version_item.setFixedHeight(56)  # 减小固定高度
            item_layout = QHBoxLayout(version_item)
            item_layout.setContentsMargins(8, 4, 8, 4)  # 减小内边距
            item_layout.setSpacing(8)  # 减小间距
            
            # 头像容器
            avatar_container = QFrame()
            avatar_container.setObjectName("avatar-container")
            avatar_container.setFixedSize(32, 32)  # 减小头像容器大小
            avatar_layout = QVBoxLayout(avatar_container)
            avatar_layout.setContentsMargins(0, 0, 0, 0)
            avatar_layout.setAlignment(Qt.AlignCenter)
            
            # 头像
            avatar_label = QLabel()
            avatar_label.setFixedSize(32, 32)  # 减小头像大小
            avatar_label.setObjectName("version-avatar")
            avatar_label.setScaledContents(True)
            
            if version_info.get('contact', {}).get('avatar'):
                avatar_data = version_info['contact']['avatar']
                pixmap = QPixmap()
                try:
                    if isinstance(avatar_data, str):
                        import base64
                        avatar_data = base64.b64decode(avatar_data)
                    
                    if avatar_data[:4] == b'\x89PNG':
                        pixmap.loadFromData(avatar_data, format='PNG')
                    else:
                        pixmap.loadFromData(avatar_data, format='JPEG')
                    avatar_label.setPixmap(pixmap)
                except Exception as e:
                    print(f"设置版本头像失败: {str(e)}")
                    avatar_label.setPixmap(Icon.get_default_avatar())
            else:
                avatar_label.setPixmap(Icon.get_default_avatar())
            
            avatar_layout.addWidget(avatar_label)
            item_layout.addWidget(avatar_container)
            
            # 信息区域
            info_frame = QFrame()
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(2)  # 减小信息区域的间距
            info_layout.setAlignment(Qt.AlignVCenter)  # 垂直居中对齐
            
            # 第一行：联系人名称和版本号
            top_row = QHBoxLayout()
            top_row.setSpacing(4)
            name_label = QLabel(version_info.get('contact', {}).get('name', ''))
            name_label.setObjectName("version-name")
            name_label.setFixedHeight(20)  # 减小名称高度
            top_row.addWidget(name_label)
            
            version_number = QLabel(f"V{version_info['version_number']}")
            version_number.setObjectName("version-number")
            version_number.setFixedHeight(20)  # 减小版本号高度
            top_row.addWidget(version_number)
            top_row.addStretch()
            
            info_layout.addLayout(top_row)
            
            # 第二行：生成时间
            time_label = QLabel(version_info.get('create_time', '').split()[1])
            time_label.setObjectName("version-time")
            time_label.setFixedHeight(16)  # 减小时间高度
            info_layout.addWidget(time_label)
            
            item_layout.addWidget(info_frame)
            
            # 设置点击事件
            version_item.mousePressEvent = lambda e, v=version_info: self.select_version(v)
            version_item.setProperty('contact_id', contact_id)
            version_item.setCursor(Qt.PointingHandCursor)
            
            # 添加到版本列表
            self.version_list.layout().addWidget(version_item)
            self.versions.append(version_info) 