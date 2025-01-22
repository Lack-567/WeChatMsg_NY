import json
from typing import Dict, List, Tuple
from volcenginesdkarkruntime import Ark
import os
from datetime import datetime

class VolcanoAPI:
    """火山引擎API调用工具类"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key
        )
        
    def test_connection(self) -> Tuple[bool, str]:
        """测试API连接是否正常
        
        Returns:
            Tuple[bool, str]: (是否连接成功, 错误信息)
        """
        try:
            # 构造一个简单的测试请求
            test_prompt = "你好，这是一个测试消息。"
            response = self.client.chat.completions.create(
                model="Doubao-vision-lite-32k",
                messages=[
                    {"role": "user", "content": test_prompt}
                ],
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            if response and response.choices:
                return True, "API连接成功"
            else:
                return False, "API响应异常：没有返回有效内容"
                
        except Exception as e:
            return False, f"API请求异常: {str(e)}"
        
    def generate_greeting(self, contact_info: Dict, chat_history: List[Dict], style_prompt: str) -> Dict:
        """生成新年祝福内容
        
        Args:
            contact_info: 联系人信息，包含姓名和wxid
            chat_history: 聊天记录列表
            style_prompt: 风格提示词
            
        Returns:
            Dict: 包含生成的祝福内容
        """
        try:
            # 分析聊天记录，提取关键信息
            chat_analysis = self._analyze_chat_history(chat_history)
            
            # 构建完整的提示词
            prompt = self._build_prompt(contact_info, chat_analysis, style_prompt)
            
            # 调用API生成内容
            response = self.client.chat.completions.create(
                model="ep-20250120142713-z5cs6",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                extra_headers={'x-is-encrypted': 'true'}
            )
            
            # 解析响应内容
            return self._parse_response(response)
            
        except Exception as e:
            raise Exception(f"生成祝福内容失败：{str(e)}")
        
    def _analyze_chat_history(self, chat_history: List[Dict]) -> Dict:
        """深度分析聊天记录，提取有价值的信息用于生成个性化祝福
        
        Args:
            chat_history: 聊天记录列表，每条记录包含：
                - message: 消息内容
                - is_sender: 是否为发送者
                - create_time: 消息时间
            
        Returns:
            Dict: 分析结果，包含：
                - chat_frequency: 聊天频率
                - relationship_level: 关系亲密度
                - common_topics: 共同话题
                - emotional_keywords: 情感关键词
                - interaction_style: 互动方式
                - chat_time_distribution: 聊天时间分布
                - key_life_events: 重要生活事件
        """
        from collections import Counter, defaultdict
        import jieba
        import jieba.analyse
        from datetime import datetime
        import re
        
        if not chat_history:
            return self._get_default_analysis()
            
        # 1. 基础统计
        total_messages = len(chat_history)
        sent_messages = sum(1 for msg in chat_history if msg['is_sender'])
        received_messages = total_messages - sent_messages
        
        # 2. 时间分析
        time_distribution = defaultdict(int)
        time_gaps = []
        last_time = None
        
        # 3. 文本处理准备
        all_text = []
        life_events = []
        emotional_words = []
        
        # 4. 关键词和话题识别的正则模式
        life_event_patterns = [
            r'考试|毕业|工作|加班|项目|旅行|旅游|生日|结婚|搬家|升职|考研',
            r'开心|难过|焦虑|压力|困难|成功|失败|努力|坚持|梦想|目标',
            r'家人|朋友|同事|领导|团队|公司|学校|家庭'
        ]
        
        emotional_patterns = [
            r'开心|快乐|高兴|激动|兴奋|满意|感动|温暖|感激|感谢',
            r'难过|伤心|焦虑|烦恼|痛苦|压力|疲惫|失望|生气|担心',
            r'加油|支持|鼓励|期待|希望|梦想|努力|坚持|相信|祝福'
        ]
        
        for msg in chat_history:
            text = msg['message']
            create_time = datetime.strptime(msg['create_time'], '%Y-%m-%d %H:%M:%S')
            
            # 更新时间分布
            hour = create_time.hour
            time_distribution[hour] += 1
            
            # 计算消息时间间隔
            if last_time:
                gap = (create_time - last_time).total_seconds() / 3600  # 转换为小时
                time_gaps.append(gap)
            last_time = create_time
            
            # 文本分析
            all_text.append(text)
            
            # 识别生活事件
            for pattern in life_event_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    life_events.extend(matches)
                    
            # 识别情感词
            for pattern in emotional_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    emotional_words.extend(matches)
        
        # 5. 分析聊天频率
        if time_gaps:
            avg_gap = sum(time_gaps) / len(time_gaps)
            if avg_gap < 24:
                chat_frequency = "频繁"
            elif avg_gap < 72:
                chat_frequency = "较多"
            else:
                chat_frequency = "一般"
        else:
            chat_frequency = "较少"
            
        # 6. 分析关系亲密度
        intimacy_score = 0
        intimacy_score += min(total_messages / 1000, 5)  # 消息数量得分，最高5分
        intimacy_score += len(set(emotional_words)) / 2  # 情感词丰富度得分
        intimacy_score += min(24 / (avg_gap if time_gaps else 168), 3)  # 时间间隔得分，最高3分
        
        if intimacy_score > 7:
            relationship_level = "密切"
        elif intimacy_score > 4:
            relationship_level = "友好"
        else:
            relationship_level = "一般"
            
        # 7. 提取关键话题
        combined_text = ' '.join(all_text)
        top_keywords = jieba.analyse.extract_tags(
            combined_text,
            topK=10,
            withWeight=True,
            allowPOS=('n', 'v', 'a')  # 名词、动词、形容词
        )
        
        # 8. 分析互动方式
        response_rate = received_messages / sent_messages if sent_messages > 0 else 0
        avg_msg_length = sum(len(msg['message']) for msg in chat_history) / total_messages
        
        if response_rate > 0.8 and avg_msg_length > 10:
            interaction_style = "深入交流"
        elif response_rate > 0.5:
            interaction_style = "积极互动"
        else:
            interaction_style = "一般交流"
            
        # 9. 整理分析结果
        return {
            "chat_frequency": chat_frequency,
            "relationship_level": relationship_level,
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "received_messages": received_messages,
            "common_topics": [word for word, weight in top_keywords[:5]],
            "emotional_keywords": list(set(emotional_words))[:5],
            "key_life_events": list(set(life_events))[:5],
            "interaction_style": interaction_style,
            "chat_time_distribution": dict(sorted(time_distribution.items())),
            "intimacy_score": round(intimacy_score, 2)
        }
        
    def _get_default_analysis(self) -> Dict:
        """返回默认的分析结果"""
        return {
            "chat_frequency": "较少",
            "relationship_level": "一般",
            "total_messages": 0,
            "sent_messages": 0,
            "received_messages": 0,
            "common_topics": ["工作", "生活"],
            "emotional_keywords": [],
            "key_life_events": [],
            "interaction_style": "一般交流",
            "chat_time_distribution": {},
            "intimacy_score": 0
        }
        
    def _build_prompt(self, contact_info: Dict, chat_analysis: Dict, style_prompt: str) -> str:
        """构建完整的提示词
        
        Args:
            contact_info: 联系人信息
            chat_analysis: 聊天记录分析结果
            style_prompt: 风格提示词
            
        Returns:
            str: 完整的提示词
        """
        # 将字典转换为更安全的字符串表示
        contact_str = f"姓名：{contact_info.get('name', '')}"
        
        # 构建详细的聊天分析信息
        common_topics = '、'.join(chat_analysis.get('common_topics', ['未知']))
        emotional_keywords = '、'.join(chat_analysis.get('emotional_keywords', []))
        key_life_events = '、'.join(chat_analysis.get('key_life_events', []))
        
        # 获取主要聊天时间段
        time_dist = chat_analysis.get('chat_time_distribution', {})
        active_hours = []
        if time_dist:
            # 找出消息数量最多的3个时间段
            sorted_hours = sorted(time_dist.items(), key=lambda x: x[1], reverse=True)[:3]
            active_hours = [f"{hour}点" for hour, _ in sorted_hours]
        
        analysis_str = (
            f"1) 基础关系：\n"
            f"   - 聊天频率：{chat_analysis.get('chat_frequency', '一般')}\n"
            f"   - 关系亲密度：{chat_analysis.get('relationship_level', '一般')}\n"
            f"   - 互动方式：{chat_analysis.get('interaction_style', '正式')}\n"
            f"   - 总消息数：{chat_analysis.get('total_messages', 0)}\n"
            f"   - 亲密度评分：{chat_analysis.get('intimacy_score', 0)}\n\n"
            f"2) 深度分析：\n"
            f"   - 共同话题：{common_topics}\n"
            f"   - 情感关键词：{emotional_keywords}\n"
            f"   - 重要生活事件：{key_life_events}\n"
            f"   - 主要互动时间：{', '.join(active_hours) if active_hours else '未知'}"
        )
        
        prompt = f"""请根据以下详细信息，生成一份2025年蛇年新年祝福：

【联系人信息】
{contact_str}

【聊天记录分析】
{analysis_str}

【风格要求】
{style_prompt}

请生成以下内容，并以JSON格式返回：
1. greeting: 新年祝福寄语（50字左右）
   - 包含2-3个具体互动数据（如消息数、默契值等） 
   - 描述3个日常相处场景，用动词短语呈现 
   - 用'从...到...'结构展现2组情感变化 
   - **给出富有特色的关系定位（如'职场损友'）** 
   - 以温暖期许作结 
   - 语气活泼自然，突出陪伴与成长 
   - 总字数控制在50字左右

2. idioms: 新年祝福诗（两句，用英文逗号分隔）
   - 每句7个汉字
   - 第一句描写一个美好愿景或意象
   - 第二句表达祝福或期许
   - 整体要押韵，符合"意、形、神"统一
   - 要融入分析出的情感关键词或生活事件

3. tags: 新年祝福成语（3个，用英文逗号分隔）
   - 要选用喜庆祥和的成语
   - 要与对方的生活状态和期望相呼应
   - 成语之间要形成递进关系

4. wishes: 新岁寄语(30字左右)
   - 要结合对方的生活事件和关注点
   - 表达真挚美好的期望
   - **以诗意笔触勾勒新年祝愿,融入对方生活际遇与心之所系,以婉约含蓄的文字传递真挚祝福,让文字如清泉般流淌,在对方心间激起涟漪**

要求：
1. 内容要体现高度个性化，充分利用聊天分析结果
2. 要严格遵循指定的风格要求
3. 整体风格要保持一致性
4. 要让对方感受到你对他/她的了解和关心
5. 要体现出诚意和温度

返回格式示例：
{{
    "greeting": "新年祝福寄语...",
    "idioms": "梦想飞扬似朝阳,岁岁安康伴春寒",
    "tags": "前程似锦,蒸蒸日上,前程万里",
    "wishes": "美好祝愿..."
}}"""

        # 保存prompt到本地文件
        try:
            # 确保目录存在
            os.makedirs('newYear/prompts', exist_ok=True)
            
            # 生成文件名（使用时间戳和联系人ID）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prompt_{timestamp}_{contact_info.get('wxid', 'unknown')}.txt"
            filepath = os.path.join('newYear/prompts', filename)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                f.write(prompt)
                
            print(f"\nPrompt已保存至: {filepath}")
            
        except Exception as e:
            print(f"\nPrompt保存失败: {str(e)}")
        
        return prompt
            
    def _parse_response(self, response) -> Dict:
        """解析API响应内容
        
        Args:
            response: API响应内容
            
        Returns:
            Dict: 解析后的祝福内容
        """
        try:
            print("\n解析响应...")
            content = response.choices[0].message.content
            print("\n生成的原始内容:", content)
            
            # 尝试解析JSON内容
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # 如果解析失败，尝试提取内容中的JSON部分
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise Exception("无法从响应中提取JSON内容")
            
            # 验证必要的字段
            required_fields = ['greeting', 'wishes', 'idioms', 'tags']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise KeyError(f"生成的内容缺少必要字段: {', '.join(missing_fields)}")
            
            
            return {
                'greeting': result['greeting'],
                'wishes': result['wishes'],
                'idioms': result['idioms'],
                'tags': result['tags']
            }
            
        except Exception as e:
            raise Exception(f"响应内容解析失败：{str(e)}")

    def test_generate_greeting(self) -> Tuple[bool, str, Dict]:
        """测试生成新年祝福内容
        
        Returns:
            Tuple[bool, str, Dict]: (是否成功, 错误信息, 生成的内容)
        """
        try:
            # 模拟联系人信息
            contact_info = {
                "wxid": "test_wxid_001",
                "name": "张三",
                "relationship": "好友"
            }
            
            # 模拟聊天记录
            chat_history = [
                {
                    "message": "今天工作怎么样？",
                    "is_sender": True,
                    "create_time": "2023-12-01 10:00:00"
                },
                {
                    "message": "还不错，项目进展顺利",
                    "is_sender": False,
                    "create_time": "2023-12-01 10:05:00"
                },
                {
                    "message": "周末要不要一起打球？",
                    "is_sender": True,
                    "create_time": "2023-12-01 10:10:00"
                }
            ]
            
            print("\n测试单个风格生成...")
            # 只测试一个风格，简化测试
            style_prompt = "温暖、亲切、感人的新年祝福，表达真挚的关心和美好祝愿"
            
            try:
                result = self.generate_greeting(
                    contact_info,
                    chat_history,
                    style_prompt
                )
                print("\n生成结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return True, "测试完成", {"warm": result}
            except Exception as e:
                return False, f"生成失败: {str(e)}", {}
            
        except Exception as e:
            return False, f"测试失败：{str(e)}", {}

if __name__ == "__main__":
    # 测试代码
    import os
    
    # 从环境变量获取API key
    api_key = os.getenv("VOLCANO_API_KEY", "")
    if not api_key:
        print("请先设置环境变量 VOLCANO_API_KEY")
        exit(1)
        
    # 创建API实例
    api = VolcanoAPI(api_key)
    
    # 测试API连接
    # print("\n=== 测试API连接 ===")
    # success, message = api.test_connection()
    # print(f"API测试结果: {'成功' if success else '失败'}")
    # print(f"详细信息: {message}")
    
    # if success:
    # 测试生成祝福内容
    print("\n=== 测试生成祝福内容 ===")
    success, message, results = api.test_generate_greeting()
    print(f"\n生成测试结果: {'成功' if success else '失败'}")
    print(f"详细信息: {message}")
    
    if success:
        print("\n=== 生成的内容示例 ===")
        # 选择一个风格的结果作为示例显示
        example = results.get("warm", {})
        if example:
            print("\n新年祝福语:")
            print(example.get("greeting", ""))
            print("\n美好祝愿:")
            print(example.get("wishes", ""))
            print("\n祝福成语:")
            print(example.get("idioms", "")) 