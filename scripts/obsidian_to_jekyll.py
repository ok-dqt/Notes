#!/usr/bin/env python3
import os
import re
import yaml
import shutil
from pathlib import Path
from datetime import datetime
import unicodedata

def slugify(text):
    """转换为 URL 友好的字符串"""
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def process_wikilinks(content):
    """处理 Obsidian 的 [[]] 链接"""
    def replace_link(match):
        link_text = match.group(1)
        if '|' in link_text:
            link, text = link_text.split('|', 1)
            return f"[{text.strip()}]({slugify(link.strip())}/)"
        else:
            return f"[{link_text}]({slugify(link_text)}/)"
    
    return re.sub(r'\[\[([^\]]+)\]\]', replace_link, content)

def process_images(content, source_dir, target_dir):
    """处理图片链接"""
    def replace_image(match):
        img_name = match.group(1)
        # 复制图片到 Jekyll 目录
        source_img = source_dir / 'assets' / 'images' / img_name
        target_img = target_dir / 'assets' / 'images' / img_name
        
        if source_img.exists():
            target_img.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_img, target_img)
            return f"![{img_name}](/assets/images/{img_name})"
        else:
            return match.group(0)  # 保持原样
    
    return re.sub(r'!\[\[([^\]]+)\]\]', replace_image, content)

def process_obsidian_file(file_path, obsidian_dir, jekyll_dir):
    """处理单个 Obsidian 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not content.startswith('---'):
        return False
    
    try:
        # 分离 frontmatter 和内容
        parts = content.split('---', 2)
        if len(parts) < 3:
            return False
        
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        
        # 检查是否需要发布
        if not frontmatter.get('publish', False):
            return False
        
        # 处理内容
        body = process_wikilinks(body)
        body = process_images(body, obsidian_dir, jekyll_dir)
        
        # 生成文件名
        date = frontmatter.get('date', datetime.now().strftime('%Y-%m-%d'))
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        
        title = frontmatter.get('title', file_path.stem)
        filename = f"{date}-{slugify(title)}.md"
        
        # 设置输出路径
        if frontmatter.get('type') == 'note':
            output_dir = jekyll_dir / '_notes'
        else:
            output_dir = jekyll_dir / '_posts'
        
        output_path = output_dir / filename
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入处理后的文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{body}")
        
        print(f"已处理: {file_path.name} -> {filename}")
        return True
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    project_root = Path.cwd()
    obsidian_dir = project_root / 'obsidian-vault'
    jekyll_dir = project_root / 'blog'
    
    if not obsidian_dir.exists():
        print("错误: 找不到 obsidian-vault 目录")
        return
    
    if not jekyll_dir.exists():
        print("错误: 找不到 blog 目录")
        return
    
    # 清理旧的发布文件（可选）
    # for old_file in (jekyll_dir / '_posts').glob('*.md'):
    #     old_file.unlink()
    
    # 处理所有标记为发布的文件
    processed_count = 0
    for md_file in obsidian_dir.rglob('*.md'):
        if process_obsidian_file(md_file, obsidian_dir, jekyll_dir):
            processed_count += 1
    
    print(f"总共处理了 {processed_count} 个文件")

if __name__ == '__main__':
    main()