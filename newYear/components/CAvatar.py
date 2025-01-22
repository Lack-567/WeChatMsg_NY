from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QPointF, pyqtProperty, QByteArray, QBuffer
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget

from ..ui.Icon import Icon

class CAvatar(QWidget):
    Circle = 0  # 圆形
    Rectangle = 1  # 圆角矩形
    
    def __init__(self, parent=None, shape=Circle, size=QSize(64, 64)):
        super().__init__(parent)
        self.shape = shape
        self._pixmap = QPixmap()  # 原始图片
        self.pixmap = QPixmap()  # 缩放后的图片
        self.setFixedSize(size)
        
        # 设置默认头像
        self.setBytes(QPixmap(Icon.Default_avatar_path))
        
    def paintEvent(self, event):
        """绘制头像"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 创建裁剪路径
        path = QPainterPath()
        rect = self.rect()
        if self.shape == self.Circle:
            # 圆形
            path.addEllipse(rect)
        else:
            # 圆角矩形
            path.addRoundedRect(rect, 4, 4)
            
        # 应用裁剪
        painter.setClipPath(path)
        
        # 绘制图片
        if not self.pixmap.isNull():
            painter.drawPixmap(rect, self.pixmap)
            
    def setBytes(self, img_bytes):
        """设置头像数据
        Args:
            img_bytes: 可以是 bytes 类型的图片数据，也可以是 QPixmap 对象
        """
        if isinstance(img_bytes, QPixmap):
            self._pixmap = img_bytes
        elif isinstance(img_bytes, bytes):
            self._pixmap = QPixmap()
            if img_bytes[:4] == b'\x89PNG':
                self._pixmap.loadFromData(img_bytes, 'PNG')
            else:
                self._pixmap.loadFromData(img_bytes, 'JPEG')
                
        if self._pixmap.isNull():
            self._pixmap = QPixmap(Icon.Default_avatar_path)
            
        # 缩放图片
        self._resizePixmap()
        
    def _resizePixmap(self):
        """缩放图片以适应控件大小"""
        if not self._pixmap.isNull():
            self.pixmap = self._pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        self.update() 