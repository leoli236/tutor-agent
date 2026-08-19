# 📚 AI 家教工作台

> 面向独立家教/小机构教师的 AI 辅助系统：错题识别 → 归因分析 → 变式练习 → 苏格拉底辅导 → 学情周报

## 功能概览

| 模块 | 功能 | 技术点 |
|------|------|--------|
| 错题识别 | 上传照片 → OCR 提取题目和学生答案 | 多模态大模型（GLM-4V） |
| 归因分析 | 判断错误类型、定位薄弱知识点 | Prompt Engineering + 结构化输出 |
| 变式练习 | 围绕薄弱知识点生成 3 道梯度练习题 | Few-shot Prompting |
| 苏格拉底辅导 | 不直接给答案，通过提问引导学生 | 多轮对话 + 提示策略 |
| 学情周报 | 自动汇总数据生成家长可读报告 | 数据聚合 + NLG |

## 快速开始

### 1. 安装依赖

```bash
cd tutor_agent
pip install -r requirements.txt
```

### 2. 配置 API Key

打开 `config.py`，将 `ZHIPU_API_KEY` 替换为你的智谱 AI API Key：

```python
ZHIPU_API_KEY = "your_real_api_key_here"
```

🔑 获取 API Key：https://open.bigmodel.cn/ → 注册 → 创建 API Key

> 智谱提供免费额度（GLM-4-flash 免费额度较大，GLM-4v-flash 按量计费），测试阶段足够使用。

### 3. 启动应用

```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8501

## 项目结构

```
tutor_agent/
├── app.py                  # Streamlit 主应用（5 个 Tab）
├── config.py               # API Key、模型配置、学科/年级常量
├── db.py                   # SQLite 数据层（学生、错题、练习、对话）
├── requirements.txt
├── README.md
├── agent/                  # Agent 核心模块
│   ├── llm_client.py       # 统一 LLM 调用封装（支持 vision + text + JSON）
│   ├── ocr.py              # 错题图片识别
│   ├── analyzer.py         # 错误归因分析
│   ├── generator.py        # 变式练习生成
│   ├── tutor.py            # 苏格拉底式辅导对话引擎
│   └── reporter.py         # 学情周报生成
└── data/                   # 运行时数据（自动创建）
    ├── tutor.db            # SQLite 数据库
    └── uploads/            # 上传的错题照片
```

## 使用流程

1. **添加学生**：左侧边栏输入学生姓名、年级、辅导学科
2. **错题录入**：上传错题照片 → AI 识别 → AI 归因 → 保存并生成变式题
3. **变式练习**：学生完成变式题 → AI 批改 → 查看正确答案
4. **苏格拉底辅导**：选择一道错题 → AI 以对话方式引导学生理解
5. **学情周报**：一键生成面向家长的周报，可下载 Markdown 文件

## 技术亮点（简历素材）

- **Prompt Engineering**：每个模块独立设计 system prompt，强制 JSON 结构化输出
- **Function Calling 设计**：五步 Pipeline（OCR→归因→出题→辅导→周报），模块解耦
- **多模态融合**：视觉模型识别手写题 → 文本模型归因出题 → 多轮对话辅导
- **真实场景驱动**：基于一年独立家教实践的真实痛点设计，非 demo 级项目

## 自定义扩展

- 换用其他大模型：修改 `agent/llm_client.py` 中的 API 地址和调用格式
- 增加学科：在左侧「管理辅导学科」中直接添加；内置语文、数学、英语、物理、化学、生物、历史、地理、政治、科学、信息技术等常见学科
- 调整辅导风格：修改 `agent/tutor.py` 中的 `TUTOR_SYSTEM_PROMPT`
- 增加用户认证：Streamlit 支持 `st.session_state` 管理登录态
- 部署上线：`streamlit deploy` 或 Docker + Nginx
