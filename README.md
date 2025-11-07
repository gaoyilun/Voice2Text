# 语音文件转文字工具

这是一个基于腾讯云API开发的语音文件转文字工具，支持多种音频格式，并通过RESTful API调用腾讯云语音识别服务。

## 功能特点

- 支持多种音频格式（wav、mp3、aac、m4a、flac、ogg）
- 通过RESTful API调用腾讯云语音识别服务
- 自动验证和处理音频文件
- 支持大文件分割处理
- 命令行界面，易于使用和集成

## 环境要求

- Python 3.6+
- 腾讯云账号和API密钥
- **注意**：不再需要腾讯云对象存储(COS)服务，现在支持直接上传音频文件

## 安装步骤

1. 克隆或下载本项目

2. 安装依赖包
   ```bash
   pip install -r requirements.txt
   ```

3. 配置腾讯云API密钥
   - 方法一：复制 `.env.example` 文件并重命名为 `.env`
   - 方法二：直接编辑现有的 `.env` 文件（如果已存在）
   - 编辑 `.env` 文件，填写您的腾讯云API密钥信息
   ```
   TENCENTCLOUD_TENANT_ID=您的租户ID（可选）
   TENCENTCLOUD_SECRET_ID=您的SecretId
   TENCENTCLOUD_SECRET_KEY=您的SecretKey
   TENCENTCLOUD_APP_ID=您的AppId
   # COS配置现在是可选的，可以保留为空
   TENCENTCLOUD_COS_BUCKET=
   TENCENTCLOUD_COS_REGION=
   ```
   
   **重要安全提示：**
   - `.env` 文件包含敏感的API密钥，不应提交到代码仓库
   - 本项目已在 `.gitignore` 中配置了忽略 `.env` 文件
   - 仅 `.env.example` 作为示例提交到仓库，其中不包含实际密钥

## 使用方法

### 方法一：图形界面（推荐）

```bash
python gui.py
```

图形界面功能：
- 点击"浏览"按钮选择输入音频文件和输出文本文件
- 从下拉菜单选择识别引擎模型（如中文普通话、英语等）
- 点击"开始转换"按钮开始处理
- 实时查看处理进度和状态
- 处理完成后直接在界面查看识别结果
- 点击"复制结果"按钮将识别结果复制到剪贴板

### 方法二：命令行

#### 基本使用

```bash
python main.py 音频文件路径
```

#### 示例

```bash
# 使用默认设置处理音频文件
python main.py example.mp3

# 指定输出文件
python main.py example.mp3 --output transcript.txt

# 指定引擎模型
python main.py example.mp3 --model 16k_zh
```

## 配置说明

### 腾讯云账号准备

1. 注册并登录腾讯云账号
2. 完成实名认证
3. 在[腾讯云控制台](https://console.cloud.tencent.com/)开通以下服务：
   - 语音识别服务
   - **注意**：不再需要开通对象存储(COS)服务
4. 获取API密钥：
   - 进入[API密钥管理](https://console.cloud.tencent.com/cam/capi)页面
   - 创建或使用已有的SecretId和SecretKey

### 音频文件要求

- 支持格式：wav、mp3、aac、m4a、flac、ogg
- 采样率：建议16kHz（腾讯云ASR最优支持）
- 声道：建议单声道
- 文件大小：大文件会自动分割处理

## 注意事项

1. **关于直接上传**：当前版本支持直接上传音频文件进行识别，无需使用对象存储服务。

2. **API调用限制**：请参考腾讯云语音识别服务的[计费说明](https://cloud.tencent.com/document/product/1093/37940)和[使用限制](https://cloud.tencent.com/document/product/1093/37941)。

3. **错误处理**：如果遇到API调用失败，请检查您的API密钥配置和网络连接。

## 扩展开发

### 添加界面

您可以使用PyQt、Tkinter或其他GUI库为工具添加图形界面，提升用户体验。

### 优化音频处理

- 实现更完善的音频格式转换
- 添加音频降噪、音量归一化等预处理功能

### 多平台支持

该项目使用Python开发，理论上支持Windows、macOS和Linux。如需进一步优化跨平台体验，可以考虑：
- 使用PyInstaller等工具打包为可执行文件
- 添加平台特定的优化

## 许可证

本项目采用MIT许可证。