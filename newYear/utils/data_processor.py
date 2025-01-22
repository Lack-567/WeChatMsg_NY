"""
数据处理工具类，用于处理聊天记录和联系人信息
"""
import os
import sqlite3
from typing import List, Dict, Tuple
from datetime import datetime
import re

class DataProcessor:
    def __init__(self):
        """初始化数据处理器"""
        # 获取当前文件所在目录的上两级目录作为项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 使用os.path.join构建跨平台的路径
        db_dir = os.path.join(project_root, "app", "Database", "Msg")
        self.micro_msg_db_path = os.path.join(db_dir, "MicroMsg.db")
        self.msg_db_path = os.path.join(db_dir, "MSG.db")
        self.misc_db_path = os.path.join(db_dir, "MISC.db")
        
        print(f"[DataProcessor] 数据库路径配置:")
        print(f"MicroMsg数据库: {self.micro_msg_db_path}")
        print(f"MSG数据库: {self.msg_db_path}")
        print(f"MISC数据库: {self.misc_db_path}")
        
        self.micro_msg_conn = None
        self.msg_conn = None
        self.misc_conn = None
        self.init_database()
        
    def check_misc_tables(self):
        """检查MISC数据库的表结构"""
        if not self.misc_conn:
            raise Exception("MISC 数据库未连接")
            
        try:
            cursor = self.misc_conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print("\nMISC数据库中的表:")
            for table in tables:
                print(f"\n表名: {table[0]}")
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  列名: {col[1]}, 类型: {col[2]}")
                    
        except sqlite3.Error as e:
            print(f"检查表结构失败：{str(e)}")
            
        finally:
            if cursor:
                cursor.close()
                
    def init_database(self):
        """初始化数据库连接"""
        if not os.path.exists(os.path.dirname(self.micro_msg_db_path)):
            print(f"[DataProcessor] 数据库目录不存在，尝试创建: {os.path.dirname(self.micro_msg_db_path)}")
            try:
                os.makedirs(os.path.dirname(self.micro_msg_db_path), exist_ok=True)
            except Exception as e:
                print(f"[DataProcessor] 创建数据库目录失败: {str(e)}")
                
        if os.path.exists(self.micro_msg_db_path):
            try:
                self.micro_msg_conn = sqlite3.connect(self.micro_msg_db_path, check_same_thread=False)
                print(f"[DataProcessor] 成功连接到 MicroMsg 数据库: {self.micro_msg_db_path}")
            except sqlite3.Error as e:
                print(f"[DataProcessor] 连接 MicroMsg 数据库失败: {str(e)}")
                self.micro_msg_conn = None
        else:
            print(f"[DataProcessor] MicroMsg 数据库文件不存在: {self.micro_msg_db_path}")
            
        if os.path.exists(self.msg_db_path):
            try:
                self.msg_conn = sqlite3.connect(self.msg_db_path, check_same_thread=False)
                print(f"[DataProcessor] 成功连接到 MSG 数据库: {self.msg_db_path}")
            except sqlite3.Error as e:
                print(f"[DataProcessor] 连接 MSG 数据库失败: {str(e)}")
                self.msg_conn = None
        else:
            print(f"[DataProcessor] MSG 数据库文件不存在: {self.msg_db_path}")
            
        if os.path.exists(self.misc_db_path):
            try:
                self.misc_conn = sqlite3.connect(self.misc_db_path, check_same_thread=False)
                print(f"[DataProcessor] 成功连接到 MISC 数据库: {self.misc_db_path}")
                # 检查MISC数据库的表结构
                self.check_misc_tables()
            except sqlite3.Error as e:
                print(f"[DataProcessor] 连接 MISC 数据库失败: {str(e)}")
                self.misc_conn = None
        else:
            print(f"[DataProcessor] MISC 数据库文件不存在: {self.misc_db_path}")
            
        # 如果数据库未连接，尝试从其他位置查找
        if not all([self.micro_msg_conn, self.msg_conn, self.misc_conn]):
            print("[DataProcessor] 尝试从其他位置查找数据库...")
            alt_db_paths = [
                os.path.join(project_root, "app", "DataBase", "Msg"),  # 注意大小写
                os.path.join(project_root, "app", "database", "msg"),
                os.path.join(project_root, "app", "Database", "msg"),
                os.path.join(project_root, "app", "database", "Msg"),
            ]
            
            for db_dir in alt_db_paths:
                if os.path.exists(db_dir):
                    print(f"[DataProcessor] 找到数据库目录: {db_dir}")
                    self.micro_msg_db_path = os.path.join(db_dir, "MicroMsg.db")
                    self.msg_db_path = os.path.join(db_dir, "MSG.db")
                    self.misc_db_path = os.path.join(db_dir, "MISC.db")
                    
                    # 重新尝试连接
                    if not self.micro_msg_conn and os.path.exists(self.micro_msg_db_path):
                        try:
                            self.micro_msg_conn = sqlite3.connect(self.micro_msg_db_path, check_same_thread=False)
                            print(f"[DataProcessor] 成功连接到 MicroMsg 数据库: {self.micro_msg_db_path}")
                        except sqlite3.Error as e:
                            print(f"[DataProcessor] 连接 MicroMsg 数据库失败: {str(e)}")
                            
                    if not self.msg_conn and os.path.exists(self.msg_db_path):
                        try:
                            self.msg_conn = sqlite3.connect(self.msg_db_path, check_same_thread=False)
                            print(f"[DataProcessor] 成功连接到 MSG 数据库: {self.msg_db_path}")
                        except sqlite3.Error as e:
                            print(f"[DataProcessor] 连接 MSG 数据库失败: {str(e)}")
                            
                    if not self.misc_conn and os.path.exists(self.misc_db_path):
                        try:
                            self.misc_conn = sqlite3.connect(self.misc_db_path, check_same_thread=False)
                            print(f"[DataProcessor] 成功连接到 MISC 数据库: {self.misc_db_path}")
                            self.check_misc_tables()
                        except sqlite3.Error as e:
                            print(f"[DataProcessor] 连接 MISC 数据库失败: {str(e)}")
                            
                    if all([self.micro_msg_conn, self.msg_conn, self.misc_conn]):
                        print("[DataProcessor] 所有数据库连接成功")
                        break
        
    def check_contact_table(self):
        """检查Contact表的结构"""
        if not self.micro_msg_conn:
            raise Exception("MicroMsg 数据库未连接")
            
        try:
            cursor = self.micro_msg_conn.cursor()
            
            # 获取表结构
            cursor.execute("PRAGMA table_info(Contact)")
            columns = cursor.fetchall()
            
            print("\nContact表结构:")
            for col in columns:
                print(f"列名: {col[1]}, 类型: {col[2]}")
                
            # 获取一条示例数据
            cursor.execute("SELECT * FROM Contact LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                print("\n示例数据:")
                for i, col in enumerate(columns):
                    print(f"{col[1]}: {result[i]}")
                    
        except sqlite3.Error as e:
            print(f"检查表结构失败：{str(e)}")
            
        finally:
            if cursor:
                cursor.close()
                
    def get_all_contacts(self) -> List[Dict]:
        """获取所有联系人列表
        
        Returns:
            List[Dict]: 联系人列表
        """
        if not self.micro_msg_conn:
            raise Exception("MicroMsg 数据库未连接")
            
        try:
            cursor = self.micro_msg_conn.cursor()
            
            # 查询所有联系人
            query = """
            SELECT Contact.UserName, Contact.Alias, Contact.Type, Contact.Remark, Contact.NickName, 
                   Contact.PYInitial, Contact.RemarkPYInitial, 
                   ContactHeadImgUrl.smallHeadImgUrl, ContactHeadImgUrl.bigHeadImgUrl,
                   Contact.ExTraBuf,
                   COALESCE(ContactLabel.LabelName, 'None') AS labelName
            FROM Contact
            INNER JOIN ContactHeadImgUrl ON Contact.UserName = ContactHeadImgUrl.usrName
            LEFT JOIN ContactLabel ON Contact.LabelIDList = ContactLabel.LabelId
            WHERE (Type!=4 AND VerifyFlag=0)
                AND NickName != ''
            ORDER BY 
                CASE
                    WHEN RemarkPYInitial = '' THEN PYInitial
                    ELSE RemarkPYInitial
                END ASC
            """
            
            try:
                cursor.execute(query)
                results = cursor.fetchall()
            except sqlite3.OperationalError:
                # 处理ContactLabel表不存在的情况
                query = """
                SELECT Contact.UserName, Contact.Alias, Contact.Type, Contact.Remark, Contact.NickName, 
                       Contact.PYInitial, Contact.RemarkPYInitial, 
                       ContactHeadImgUrl.smallHeadImgUrl, ContactHeadImgUrl.bigHeadImgUrl,
                       Contact.ExTraBuf,
                       'None' as labelName
                FROM Contact
                INNER JOIN ContactHeadImgUrl ON Contact.UserName = ContactHeadImgUrl.usrName
                WHERE (Type!=4 AND VerifyFlag=0)
                    AND NickName != ''
                ORDER BY 
                    CASE
                        WHEN RemarkPYInitial = '' THEN PYInitial
                        ELSE RemarkPYInitial
                    END ASC
                """
                cursor.execute(query)
                results = cursor.fetchall()
            
            print(f"\n找到 {len(results)} 个联系人")
            
            contacts = []
            for result in results:
                original_name = result[3] if result[3] else result[4]  # 优先使用备注名
                display_name = re.sub(r'[\\/:*?"<>|\s\.]', '_', original_name)  # 用于文件名等需要处理特殊字符的场景
                
                if original_name:  # 确保名称不为空
                    contacts.append({
                        'wxid': result[0],
                        'alias': result[1],
                        'type': result[2],
                        'name': display_name,
                        'original_name': original_name,
                        'nickname': result[4],
                        'py_initial': result[5],
                        'remark_py_initial': result[6],
                        'small_avatar_url': result[7],
                        'big_avatar_url': result[8],
                        'extra_buf': result[9],
                        'label_name': result[10]
                    })
                
            return contacts
            
        except sqlite3.Error as e:
            raise Exception(f"数据库查询失败：{str(e)}")
            
        finally:
            if cursor:
                cursor.close()

    def get_chat_history(self, contact_id: str, start_date: str, end_date: str) -> List[Dict]:
        """获取指定时间范围内的聊天记录
        
        Args:
            contact_id: 联系人ID
            start_date: 开始日期（格式：YYYY-MM-DD）
            end_date: 结束日期（格式：YYYY-MM-DD）
            
        Returns:
            List[Dict]: 聊天记录列表
        """
        try:
            cursor = self.msg_conn.cursor()
            
            # 查询聊天记录
            query = """
            SELECT localId, TalkerId, Type, SubType, IsSender, CreateTime, Status, 
                   StrContent, strftime('%Y-%m-%d %H:%M:%S', CreateTime, 'unixepoch', 'localtime') as create_time
            FROM MSG
            WHERE StrTalker = ? 
            AND CreateTime BETWEEN strftime('%s', ?) AND strftime('%s', ?)
            AND Type = 1  -- 只获取文本消息
            ORDER BY CreateTime ASC
            """
            
            cursor.execute(query, (contact_id, start_date, end_date))
            results = cursor.fetchall()
            
            # 转换为字典列表
            chat_history = []
            for msg in results:
                chat_history.append({
                    'local_id': msg[0],
                    'talker_id': msg[1],
                    'type': msg[2],
                    'sub_type': msg[3],
                    'is_sender': msg[4],
                    'timestamp': msg[5],
                    'status': msg[6],
                    'message': msg[7],
                    'create_time': msg[8]
                })
                
            return chat_history
            
        except sqlite3.Error as e:
            raise Exception(f"数据库查询失败：{str(e)}")
            
        finally:
            if cursor:
                cursor.close()
                
    def analyze_chat_content(self, chat_history: List[Dict]) -> Dict:
        """分析聊天内容，提取关键信息
        
        Args:
            chat_history: 聊天记录列表
            
        Returns:
            Dict: 分析结果，包含关键词、聊天频率等信息
        """
        # 实现聊天内容分析逻辑
        pass
        
    def get_contact_avatar(self, wxid: str) -> bytes:
        """获取联系人头像数据
        
        Args:
            wxid: 联系人的微信ID
            
        Returns:
            bytes: 头像的二进制数据
        """
        try:
            print(f"[DataProcessor] 开始获取头像 - 联系人ID: {wxid}")
            cursor = self.misc_conn.cursor()
            
            # 从ContactHeadImg1表获取头像数据
            query = "SELECT smallHeadBuf FROM ContactHeadImg1 WHERE usrName=?"
            cursor.execute(query, (wxid,))
            result = cursor.fetchone()
            
            if result and result[0]:
                data = result[0]
                print(f"[DataProcessor] 成功获取头像数据 - 联系人ID: {wxid}, 数据大小: {len(data)} 字节")
                return data
            else:
                print(f"[DataProcessor] 未找到头像数据 - 联系人ID: {wxid}")
                return None
                
        except sqlite3.Error as e:
            print(f"[DataProcessor] 获取头像失败 - 联系人ID: {wxid}, 错误: {str(e)}")
            return None
            
        finally:
            if cursor:
                cursor.close()
        
    def close(self):
        """关闭数据库连接"""
        if self.micro_msg_conn:
            self.micro_msg_conn.close()
        if self.msg_conn:
            self.msg_conn.close()
        if self.misc_conn:
            self.misc_conn.close()
            
    def __del__(self):
        self.close() 