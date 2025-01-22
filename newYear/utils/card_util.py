from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import shutil
from datetime import datetime

def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def inject_data_to_template(template_path, data):
    """将数据注入到模板中
    Args:
        template_path: 模板文件路径
        data: 包含以下字段的字典：
            - year: 年份
            - greeting_text: 新年祝福寄语（主标题）
            - poem_text: 新年祝福诗
            - idioms_text: 新年祝福成语
            - wishes_text: 新年祝福愿望
            - signature: 署名
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 处理祝福诗（分割成两句）
    poem_lines = data.get('poem_text', '梦想飞扬似朝阳,岁岁安康伴春寒').split(',')
    if len(poem_lines) < 2:
        poem_lines = [poem_lines[0], poem_lines[0]]  # 如果只有一句，重复使用
    
    # 处理祝福成语（分割成三个）
    idioms = data.get('idioms_text', '福满人间,万事胜意,喜乐安康').split(',')
    while len(idioms) < 3:  # 确保有3个成语
        idioms.append(idioms[-1])
    
    # 准备所有替换数据
    replace_data = {
        'year': data.get('year', '2025'),
        'greeting_text': data.get('greeting_text', '新年快乐'),
        'idioms_text_1': poem_lines[0],
        'idioms_text_2': poem_lines[1],
        'wishes_text': data.get('wishes_text', '愿你在新的一年里\\n事事顺遂 万事胜意'),
        'signature': data.get('signature', '署名'),
        'tag_1': idioms[0],
        'tag_2': idioms[1],
        'tag_3': idioms[2]
    }
    
    # 替换所有占位符
    for key, value in replace_data.items():
        placeholder = '{' + key + '}'
        template_content = template_content.replace(placeholder, str(value))
    
    # 创建临时文件来存储注入数据后的HTML
    temp_html_path = 'temp_generated.html'
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return temp_html_path

def capture_local_html(html_path, output_path, wait_time=2):
    """截取HTML页面为图片"""
    print(f"\n=== 开始截取HTML页面 ===")
    print(f"HTML文件路径: {html_path}")
    print(f"输出路径: {output_path}")
    
    if not os.path.exists(html_path):
        error_msg = f'HTML文件不存在: {html_path}'
        print(f"错误: {error_msg}")
        raise FileNotFoundError(error_msg)
    
    abs_path = os.path.abspath(html_path)
    file_url = f'file:///{abs_path}'
    print(f"文件URL: {file_url}")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 设置足够大的初始窗口，确保能完整显示内容
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        print("\n1. 初始化Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("\n2. 加载HTML页面...")
        driver.get(file_url)
        
        print("\n3. 等待页面元素加载...")
        wait = WebDriverWait(driver, 10)
        card_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'card-container')))
        
        print(f"\n4. 等待页面渲染 ({wait_time}秒)...")
        import time
        time.sleep(wait_time)
        
        print("\n5. 获取卡片位置和尺寸...")
        # 获取卡片容器的精确位置和尺寸
        card_rect = driver.execute_script("""
            const container = document.querySelector('.card-container');
            const rect = container.getBoundingClientRect();
            return {
                left: rect.left,
                top: rect.top,
                width: rect.width,
                height: rect.height,
                devicePixelRatio: window.devicePixelRatio
            };
        """)
        
        print(f"卡片信息: {card_rect}")
        
        print("\n6. 截取完整页面...")
        driver.save_screenshot('temp_full.png')
        
        print("\n7. 裁剪卡片区域...")
        from PIL import Image
        img = Image.open('temp_full.png')
        
        # 计算裁剪坐标（考虑设备像素比）
        dpr = card_rect['devicePixelRatio']
        left = int(card_rect['left'] * dpr)
        top = int(card_rect['top'] * dpr)
        right = int((card_rect['left'] + card_rect['width']) * dpr)
        bottom = int((card_rect['top'] + card_rect['height']) * dpr)
        
        print(f"裁剪坐标: left={left}, top={top}, right={right}, bottom={bottom}")
        
        # 确保裁剪区域不超出图片范围
        img_width, img_height = img.size
        left = max(0, left)
        top = max(0, top)
        right = min(img_width, right)
        bottom = min(img_height, bottom)
        
        # 裁剪并保存
        card_img = img.crop((left, top, right, bottom))
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            ensure_directory(output_dir)
            
        print("\n8. 保存卡片图片...")
        card_img.save(output_path, quality=100)  # 使用最高质量
        print(f'卡片截图已保存至: {output_path}')
        
        print("\n9. 清理临时文件...")
        os.remove('temp_full.png')
        print("=== 截图完成 ===\n")
        
    except Exception as e:
        error_msg = f'截图过程发生错误: {str(e)}'
        print(f"\nError: {error_msg}")
        raise Exception(error_msg)
        
    finally:
        if driver:
            print("\n10. 关闭WebDriver...")
            driver.quit()


def generate_card(template_number, data, user_id):
    """生成贺卡并保存相关信息"""
    print(f"\n=== 开始生成贺卡 ===")
    print(f"模板编号: {template_number}")
    print(f"用户ID: {user_id}")
    
    try:
        # 确保目录存在
        print("\n1. 检查并创建必要的目录...")
        ensure_directory('newYear/generate_img')
        ensure_directory('newYear/version_history')
        
        # 构建文件路径
        template_path = f'newYear/template/template_{template_number}.html'
        img_filename = f'{user_id}.png'
        img_path = os.path.join('newYear/generate_img', img_filename)
        json_path = os.path.join('newYear/version_history', f'{user_id}.json')
        
        print(f"\n2. 检查模板文件: {template_path}")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f'模板文件不存在: {template_path}')
        
        print("\n3. 注入数据到模板...")
        temp_html_path = inject_data_to_template(template_path, data)
        print(f"临时HTML文件已创建: {temp_html_path}")
        
        print("\n4. 生成贺卡图片...")
        capture_local_html(temp_html_path, img_path, wait_time=2)
        
        print("\n5. 更新JSON文件...")
        # 只保存必要的文本数据和路径信息
        json_data = {
            'template_number': template_number,
            'image_path': img_path,
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'template_data': {
                'year': data.get('year', '2025'),
                'greeting_text': data.get('greeting_text', ''),
                'poem_text': data.get('poem_text', ''),
                'idioms_text': data.get('idioms_text', ''),
                'wishes_text': data.get('wishes_text', ''),
                'signature': data.get('signature', '')
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"JSON文件已保存: {json_path}")
        
        print("=== 贺卡生成完成 ===\n")
        return img_path
        
    except Exception as e:
        error_msg = f'生成贺卡失败: {str(e)}'
        print(f"\nError: {error_msg}")
        raise Exception(error_msg)

# 使用示例
if __name__ == '__main__':
    # 示例数据
    test_data = {
        'blessing_text': '新年快乐！',
        'memory_text': '愿你在新的一年里事事顺心',
        'signature': '小明'
    }
    
    # 生成卡片
    img_path = generate_card(
        template_number=1,  # 使用模板1
        data=test_data,
        user_id='test_user'
    )