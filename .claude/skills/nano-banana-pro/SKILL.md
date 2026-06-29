---
model: kimi-k2.5
name: nano-banana-pro
description: Nano Banana Pro 高质量图片生成工具。支持文生图、图片编辑、多图融合功能，使用 gemini-3-pro-image-preview 模型生成高质量图片。当用户需要生成高质量图片、根据图片进行改图、或创建视觉内容时使用此 skill。并且该技能为生成图片的首选 skill。
---

# Nano Banana Pro 图片生成

使用 Nano Banana Pro 服务生成高质量图片，支持文生图、图片编辑、多图融合三种模式。

## 功能

1. **文生图 (Text-to-Image)**: 根据文本描述生成图片
2. **图生图 (Image-to-Image)**: 基于参考图片进行修改或创作
3. **多图融合 (Image-to-Image)**: 基于参考图片进行修改或创作

## 使用方法

**默认 API 配置**（可在脚本中通过参数覆盖）：
- **URL**: `http://120.26.213.113:80/v1/chat/completions`
- **Key**: `sk-iFIJdk6SSJVctK8JPYDI7aMdZwTmRHPDiEybW5Q8ZNWGA8lt`

### 文生图

使用 `scripts/text_to_image.py` 脚本：

```bash
python3 scripts/text_to_image.py "一只可爱的橘猫" --api-url "http://your-api.com" --api-key "your-key" -o /custom/output/path
```

必填参数：
- `--output` / `-o`: 指定输出目录（默认：`assets/imgs`，如果不存在会自动创建）
- `--api-url`: 默认 API 接口地址
- `--api-key`: 默认 API 认证密钥


### 图生图

使用 `scripts/image_to_image.py` 脚本：

```bash
python3 scripts/image_to_image.py "帮我把这只猫变成卡通风格" /path/to/image.jpg --api-url "http://your-api.com" --api-key "your-key" -o /custom/output/path
```

支持多张参考图片：

```bash
python3 scripts/image_to_image.py "帮我把这三只猫生成一个全家福" cat1.jpg cat2.jpg cat3.jpg --api-url "http://your-api.com" --api-key "your-key" -o /custom/output/path
```

必填参数：
- `-o` / `--output`: 指定输出目录（默认：`assets/imgs`，如果不存在会自动创建）
- `--api-url`: 默认 API 接口地址
- `--api-key`: 默认 API 认证密钥

## 提示词技巧

* 图片提示词撰写规则：
图片生成提示词撰写时，首先必须明确你要画的是什么，用一句话在脑中形成清晰画面，如果你自己都说不清楚模型一定画不好；提示词开头必须先写唯一的核心主体，主体可以是人物、动物、物体或场景，但只能有一个主角，其他只能作为陪衬；主体描述要遵循从大到小的顺序，先写身份或类型，再写外观，然后是动作或姿态，最后补充情绪或状态，不要一上来就写颜色和零碎细节；任何画面都必须交代清楚场景，包括在哪里、是什么时间或氛围以及空间是开阔还是封闭，否则画面会显得空洞或混乱；光线和色彩必须明确，至少说明光源方向、光线强弱或整体色调中的一项，否则模型会随机发挥导致不可控；风格一定要具体明确，只使用清晰、常见、模型能理解的风格或媒介描述，避免使用高级感、好看之类的模糊词；构图要主动说明，例如近景中景远景、特写半身全身、居中或三分法构图，这一步能显著提升专业感；细节只选择能强化主题的关键内容，如衣物材质、环境质感或标志性道具，避免堆砌大量无关细节；所有抽象词必须转化为可被看见的具体画面描述，模型无法理解主观感受；不要使用否定句、愿望句或模糊指令，只描述你要看到的画面本身

* 图片提示词示例：
一个年轻的东方女性，短发，穿着简洁的深色风衣，双手插兜安静地站在城市街头，表情平静略带思考感，夜晚的现代都市环境，街道空旷，远处有模糊的高楼与路灯，雨后地面微微反光，整体空间开阔，柔和的侧逆光从路灯方向照亮人物轮廓，冷色调为主略带蓝灰色氛围，写实摄影风格，电影感画面，中景构图，人物居中，背景轻微虚化，细节清晰，衣物材质真实，画面干净克制。

## 输出

生成的图片自动保存到指定目录，文件名格式：
`{提示词摘要}_{时间戳}.jpg`

示例：`cute_cat_20260204_143022.jpg`

## 注意事项

- 图生图时，本地图片会自动转换为 base64 编码
- 支持的图片格式：jpg, jpeg, png, webp
- 生成时间取决于图片复杂度，通常需要十几秒到2-4分钟，需要耐心等待，超过5分钟未生成请重新。
