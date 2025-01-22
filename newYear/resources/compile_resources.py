import os
import subprocess

def compile_resources():
    """编译 Qt 资源文件"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 资源文件路径
    qrc_file = os.path.join(current_dir, 'icons', 'resources.qrc')
    
    # 输出文件路径
    output_file = os.path.join(current_dir, 'resources_rc.py')
    
    try:
        # 使用 pyrcc5 编译资源文件
        subprocess.run(['pyrcc5', qrc_file, '-o', output_file], check=True)
        print(f"资源文件编译成功：{output_file}")
    except subprocess.CalledProcessError as e:
        print(f"编译失败：{str(e)}")
    except FileNotFoundError:
        print("错误：找不到 pyrcc5 工具。请确保已安装 PyQt5-tools")

if __name__ == '__main__':
    compile_resources() 