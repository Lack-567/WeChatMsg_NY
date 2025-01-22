from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QByteArray, QBuffer
import os

class Icon:
    """图标资源管理类"""
    
    # 默认头像
    Default_avatar_path = ':/icons/default_avatar.svg'
    _default_avatar = None
    
    # 其他图标路径
    Logo_path = ':/icons/logo.svg'
    Logo = QIcon(Logo_path)
    
    @classmethod
    def get_default_avatar(cls):
        """获取默认头像"""
        if cls._default_avatar is None:
            cls._default_avatar = QPixmap(cls.Default_avatar_path)
        return cls._default_avatar
        
    @classmethod
    def get_default_avatar_bytes(cls):
        """获取默认头像的二进制数据"""
        if cls._default_avatar is None:
            cls._default_avatar = QPixmap(cls.Default_avatar_path)
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QBuffer.WriteOnly)
        cls._default_avatar.save(buffer, 'PNG')
        return ba.data() 