from pypinyin import lazy_pinyin, Style
import jieba
from typing import List, Dict, Set
import json
import os

class SearchHelper:
    def __init__(self):
        self.search_history: List[str] = []
        self.history_file = "search_history.json"
        self.load_history()
        
    def load_history(self):
        """加载搜索历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.search_history = json.load(f)
            except:
                self.search_history = []
                
    def save_history(self):
        """保存搜索历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history[-20:], f)  # 只保留最近20条记录
        except:
            pass
            
    def add_history(self, keyword: str):
        """添加搜索历史"""
        if keyword and keyword not in self.search_history:
            self.search_history.append(keyword)
            self.save_history()
            
    def clear_history(self):
        """清空搜索历史"""
        self.search_history = []
        self.save_history()
        
    def get_pinyin_initials(self, text: str) -> str:
        """获取拼音首字母"""
        return ''.join([i[0] for i in lazy_pinyin(text)])
        
    def get_full_pinyin(self, text: str) -> str:
        """获取全拼"""
        return ''.join(lazy_pinyin(text))
        
    def match_contact(self, keyword: str, contact_name: str) -> bool:
        """匹配联系人
        支持:
        1. 原文匹配（包括空格）
        2. 忽略空格匹配
        3. 拼音首字母匹配
        4. 全拼匹配
        5. 汉字模糊匹配
        """
        if not keyword:
            return True
            
        keyword = keyword.lower()
        contact_name = contact_name.lower()
        
        # 原文匹配
        if keyword in contact_name:
            return True
            
        # 忽略空格匹配
        if keyword.replace(' ', '') in contact_name.replace(' ', ''):
            return True
            
        # 拼音首字母匹配
        pinyin_initials = self.get_pinyin_initials(contact_name).lower()
        if keyword.replace(' ', '') in pinyin_initials:
            return True
            
        # 全拼匹配
        full_pinyin = self.get_full_pinyin(contact_name).lower()
        if keyword.replace(' ', '') in full_pinyin:
            return True
            
        # 分词后的模糊匹配
        name_words = set(jieba.cut(contact_name))
        search_words = set(jieba.cut(keyword))
        if search_words & name_words:  # 交集不为空则匹配成功
            return True
            
        return False 