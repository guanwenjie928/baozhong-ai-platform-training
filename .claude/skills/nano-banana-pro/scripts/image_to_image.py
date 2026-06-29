#!/usr/bin/env python3
"""
Nano Banana Pro 图生图改图脚本
调用接口基于参考图片生成新图片
"""

import sys
import os
import json
import base64
import re
import urllib.request
import argparse
from pathlib import Path
from typing import Optional, List

# 默认 API 配置（可通过参数覆盖）
DEFAULT_API_URL = "http://120.26.213.113:80/v1/chat/completions"
DEFAULT_API_KEY = "sk-iFIJdk6SSJVctK8JPYDI7aMdZwTmRHPDiEybW5Q8ZNWGA8lt"
MODEL = "gemini-3-pro-image-preview"


def image_to_base64(image_path: str) -> str:
    """将本地图片转换为 base64 编码"""
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode('utf-8')


def get_mime_type(image_path: str) -> str:
    """根据文件扩展名获取 MIME 类型"""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }
    return mime_types.get(ext, 'image/jpeg')


def extract_base64_from_markdown(content: str) -> Optional[str]:
    """从 markdown 图片格式中提取 base64 数据"""
    pattern = r'!\[image\]\(data:image/[^;]+;base64,([^)]+)\)'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def save_base64_image(base64_data: str, output_path: str) -> str:
    """保存 base64 图片到文件"""
    image_bytes = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_bytes)
    return output_path


def transform_image(prompt: str, image_paths: List[str], output_dir: str, api_url: str, api_key: str) -> str:
    """
    基于参考图片生成新图片

    Args:
        prompt: 图片变换提示词
        image_paths: 参考图片路径列表
        output_dir: 图片保存目录
        api_url: API 接口地址
        api_key: API 认证密钥

    Returns:
        保存的图片路径
    """
    if not image_paths:
        raise ValueError("至少需要提供一张参考图片")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 构建 content 列表
    content = [{"type": "text", "text": prompt}]

    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图片不存在: {img_path}")

        base64_data = image_to_base64(img_path)
        mime_type = get_mime_type(img_path)

        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_data}"
            }
        })

    # 构建请求
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False,
        "temperature": 0.7
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )

    # 发送请求
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))

    # 提取图片内容
    result_content = data['choices'][0]['message']['content']
    base64_data = extract_base64_from_markdown(result_content)

    if not base64_data:
        raise ValueError("无法从响应中提取图片数据")

    # 生成文件名
    timestamp = os.popen('date +%Y%m%d_%H%M%S').read().strip()
    safe_prompt = re.sub(r'[^\w\u4e00-\u9fff]+', '_', prompt[:30]).strip('_')
    filename = f"{safe_prompt}_{timestamp}.jpg"
    output_path = os.path.join(output_dir, filename)

    # 保存图片
    save_base64_image(base64_data, output_path)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Nano Banana Pro 图生图工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python image_to_image.py "帮我把这只猫变成卡通风格" /path/to/image.jpg
  python image_to_image.py "全家福" cat1.jpg cat2.jpg cat3.jpg
  python image_to_image.py "修改风格" image.jpg -o /custom/output/path
  python image_to_image.py "修改风格" image.jpg --api-url "http://your-api.com" --api-key "your-key"
        '''
    )

    parser.add_argument('prompt', help='图片变换提示词')
    parser.add_argument('images', nargs='+', help='参考图片路径（可多个）')
    parser.add_argument('-o', '--output', default='assets/imgs',
                        help='图片输出目录 (默认: 项目根目录下的 assets/imgs)')
    parser.add_argument('--api-url', default=DEFAULT_API_URL,
                        help=f'API 接口地址 (默认: {DEFAULT_API_URL})')
    parser.add_argument('--api-key', default=DEFAULT_API_KEY,
                        help='API 认证密钥')

    args = parser.parse_args()

    # 过滤出存在的图片文件（不存在的可能是误输入的目录参数，但这里我们要求显式使用 -o）
    image_paths = [img for img in args.images if os.path.isfile(img)]

    if not image_paths:
        print("Error: 至少需要提供一张有效的参考图片", file=sys.stderr)
        sys.exit(1)

    try:
        result_path = transform_image(args.prompt, image_paths, args.output, args.api_url, args.api_key)
        print(result_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
