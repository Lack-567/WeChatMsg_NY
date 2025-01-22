"""
版本管理器，用于管理生成内容的版本
"""
import os
import json
import base64
from datetime import datetime
from typing import List, Dict

class VersionManager:
    def __init__(self):
        # 设置版本历史目录
        self.version_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version_history')
        
        # 确保目录存在
        if not os.path.exists(self.version_dir):
            os.makedirs(self.version_dir)
            
        # 初始化版本数据
        self.versions = {}
        
        # 加载所有版本数据
        self.load_versions()
        
    def load_versions(self):
        """加载所有版本数据"""
        if not os.path.exists(self.version_dir):
            return
            
        # 遍历版本文件
        for filename in os.listdir(self.version_dir):
            if filename.endswith('.json'):
                wxid = filename[:-5]  # 移除.json后缀
                file_path = os.path.join(self.version_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        encoded_versions = json.load(f)
                        # 解码版本数据
                        self.versions[wxid] = [
                            self.process_version_data(version, encode=False)
                            for version in encoded_versions
                        ]
                except Exception as e:
                    print(f"加载版本数据失败 - 联系人ID: {wxid}, 错误: {str(e)}")
                    
    def save_versions(self):
        """保存版本数据到文件"""
        # 确保目录存在
        os.makedirs(self.version_dir, exist_ok=True)
        
        # 遍历所有联系人的版本数据
        for contact_id, versions in self.versions.items():
            file_path = os.path.join(self.version_dir, f"{contact_id}.json")
            
            # 处理每个版本中的数据
            processed_versions = []
            for version in versions:
                # 处理二进制数据
                processed_version = self.process_version_data(version, encode=True)
                # 处理自定义风格内容
                if processed_version.get('style') == 'custom':
                    processed_version['custom_prompt'] = processed_version.get('style_content', '')
                processed_versions.append(processed_version)
            
            # 保存到文件
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_versions, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存版本数据失败 - 联系人ID: {contact_id}, 错误: {str(e)}")
                
    def get_version_file(self, wxid: str) -> str:
        """获取联系人的版本文件路径"""
        return os.path.join(self.version_dir, f"{wxid}.json")
        
    def add_version(self, version_info):
        """添加新版本"""
        contact_id = version_info['contact']['wxid']
        
        # 获取该联系人的所有版本
        if contact_id not in self.versions:
            self.versions[contact_id] = []
        contact_versions = self.versions[contact_id]
        
        # 添加版本号
        version_number = len(contact_versions) + 1
        version_info['version_number'] = version_number
        
        # 添加创建时间
        version_info['create_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 处理风格内容
        style = version_info.get('style', '')
        if style == 'custom':
            # 自定义风格使用 custom_prompt
            custom_prompt = version_info.get('custom_prompt', '')
            version_info['style_content'] = custom_prompt
        else:
            # 预设风格使用 style_prompt
            style_prompt = version_info.get('style_prompt', '')
            version_info['style_content'] = style_prompt
            # 移除自定义提示词
            version_info.pop('custom_prompt', None)
        
        # 添加新版本
        contact_versions.append(version_info)
        
        # 保存到文件
        self.save_versions()
        
        return version_info
        
    def process_version_data(self, version_info: Dict, encode: bool = True) -> Dict:
        """处理版本数据中的二进制内容"""
        processed = version_info.copy()  # 创建副本以避免修改原始数据
        
        # 处理联系人数据
        if 'contact' in processed:
            processed['contact'] = self.process_contact_data(processed['contact'], encode)
            
        # 确保自定义风格内容被正确处理
        if processed.get('style') == 'custom':
            custom_prompt = processed.get('custom_prompt', '')
            processed['custom_prompt'] = custom_prompt
            processed['style_content'] = custom_prompt
            
        return processed
        
    def process_contact_data(self, contact_info: Dict, encode: bool = True) -> Dict:
        """处理联系人数据中的二进制内容"""
        processed = contact_info.copy()
        if 'avatar' in processed:
            if encode:
                processed['avatar'] = self.encode_binary(processed['avatar'])
            else:
                processed['avatar'] = self.decode_binary(processed['avatar'])
        return processed
        
    def encode_binary(self, data):
        """编码二进制数据为base64字符串"""
        if isinstance(data, bytes):
            return base64.b64encode(data).decode('utf-8')
        return data
        
    def decode_binary(self, data):
        """解码base64字符串为二进制数据"""
        if isinstance(data, str):
            try:
                return base64.b64decode(data)
            except:
                return data
        return data
        
    def get_contact_versions(self, contact_id):
        """获取指定联系人的所有版本"""
        return self.versions.get(contact_id, [])
        
    def get_all_versions(self):
        """获取所有版本"""
        return self.versions 

    def update_version(self, version_info):
        """更新版本信息"""
        contact_id = version_info['contact']['wxid']
        
        # 处理风格内容
        style = version_info.get('style', '')
        if style == 'custom':
            # 自定义风格使用 custom_prompt
            custom_prompt = version_info.get('custom_prompt', '')
            version_info['style_content'] = custom_prompt
        else:
            # 预设风格使用 style_prompt
            style_prompt = version_info.get('style_prompt', '')
            version_info['style_content'] = style_prompt
            # 移除自定义提示词
            version_info.pop('custom_prompt', None)
            
        # 获取该联系人的所有版本
        contact_versions = self.versions.get(contact_id, [])
        
        # 查找并更新版本
        for i, version in enumerate(contact_versions):
            if version.get('version_number') == version_info.get('version_number'):
                contact_versions[i] = version_info
                break
                
        # 保存更新后的版本
        self.versions[contact_id] = contact_versions
        self.save_versions() 