#!/usr/bin/env python
"""
初始化项目必要的目录结构
"""
import os
import sys
from pathlib import Path

def init_project_directories():
    """创建项目所需的目录结构"""
    # 获取项目根目录
    BASE_DIR = Path(__file__).resolve().parent
    
    # 需要创建的目录列表
    directories = [
        os.path.join(BASE_DIR, 'logs'),
        os.path.join(BASE_DIR, 'media'),
        os.path.join(BASE_DIR, 'static'),
        os.path.join(BASE_DIR, 'static_collected'),
    ]
    
    # 创建目录
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")
    
    # 创建一个空的 .gitkeep 文件，确保空目录可以被Git跟踪
    for directory in directories:
        gitkeep_file = os.path.join(directory, '.gitkeep')
        if not os.path.exists(gitkeep_file):
            with open(gitkeep_file, 'w') as f:
                pass  # 创建空文件
            print(f"创建文件: {gitkeep_file}")

if __name__ == "__main__":
    print("正在初始化项目目录结构...")
    init_project_directories()
    print("项目初始化完成!")
