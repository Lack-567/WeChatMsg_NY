from wxauto import *
import time

def send_wx_msg(friend_name, message):
    try:
        # 获取当前微信客户端
        wx = WeChat()
        
        # 先切换到对应的聊天窗口
        if not wx.ChatWith(friend_name):
            print(f"切换到聊天窗口失败: {friend_name}")
            return False
        
        # 发送消息
        wx.SendMsg(message, who=friend_name)
        print(f"消息已成功发送给 {friend_name}")
        return True
        
    except Exception as e:
        print(f"发送失败：{str(e)}")
        return False

def send_message_and_image(name: str, image_path: str) -> bool:
    """发送消息和图片到指定微信联系人
    
    Args:
        name: 联系人的微信名称
        image_path: 图片文件的路径
        
    Returns:
        bool: 是否发送成功
    """
    try:
        # 获取微信实例
        wx = WeChat()
        
        # 先切换到对应的聊天窗口
        if not wx.ChatWith(name):
            print(f"切换到聊天窗口失败: {name}")
            return False
            
        # 发送图片
        if not wx.SendFiles(image_path):
            print(f"发送图片失败: {image_path}")
            return False
            
        return True
        
    except Exception as e:
        print(f"发送消息失败: {str(e)}")
        return False

# 使用示例
if __name__ == "__main__":
    # 要发送消息的好友名称
    friend_name = "''"  # 替换为实际好友名称
    
    # 要发送的消息内容
    message = "你好，这是一条测试消息！"
    
    # 发送消息
    send_wx_msg(friend_name, message)