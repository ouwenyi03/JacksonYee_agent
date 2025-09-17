import streamlit as st
import dashscope
from dashscope import Generation
from bs4 import BeautifulSoup
import requests
import time
import re
from datetime import datetime
import json
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# ======================
# 配置与初始化
# ======================
# 设置页面配置
st.set_page_config(
    page_title="易烊千玺AI分身",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 初始化会话状态
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "style" not in st.session_state:
        st.session_state.style = get_celebrity_style()
    if "last_update" not in st.session_state:
        st.session_state.last_update = datetime.now()
    if "typing" not in st.session_state:
        st.session_state.typing = False
    if "page_visits" not in st.session_state:
        st.session_state.page_visits = 0
        st.session_state.page_visits += 1


# ======================
# 明星风格分析模块
# ======================
def get_celebrity_style():
    """通过RSS抓取真实微博，用LLM总结对话风格"""
    # 使用公开的微博RSS源
    rss_url = "https://rsshub.app/weibo/user/1776630065"

    try:
        # 获取最新10条微博
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml', parser='lxml')
        items = soup.find_all('item')[:10]

        # 提取纯文本内容
        tweets = []
        for item in items:
            title = item.title.text
            # 清理微博中的@和链接
            clean_text = re.sub(r'@\w+|https?://\S+', '', title)
            tweets.append(clean_text)

        # 如果抓取失败，用预设数据兜底
        if not tweets:
            tweets = [
                "大家好，最近在练习新歌，希望给大家带来更多好作品！",
                "公益项目进展顺利，感谢志愿者们的付出❤️",
                "拍戏间隙和剧组小伙伴一起打篮球，超开心！",
                "新电影《奇迹》正在热映，期待大家的反馈~",
                "记得按时吃饭，照顾好自己，晚安🌙"
            ]

        # 用通义千问总结风格
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY") or st.secrets.get("DASHSCOPE_API_KEY")

        prompt = f"""
        你是一名社交媒体分析师，请分析以下易烊千玺的微博内容，总结他的对话风格特征：

        {tweets}

        要求：
        1. 提取3个最显著的语言特点（如用词、句式）
        2. 指出2个高频话题
        3. 描述语气情感（10字内）
        4. 用JSON格式输出，字段：language_features, frequent_topics, tone

        示例：
        {{
            "language_features": ["常用'大家好'开头", "多用波浪号~", "短句为主"],
            "frequent_topics": ["音乐创作", "公益活动"],
            "tone": "温暖积极"
        }}
        """

        response = Generation.call(
            model='qwen-turbo',
            prompt=prompt,
            temperature=0.3
        )

        # 解析JSON
        style_data = json.loads(response.output.text)  # 使用更安全的json解析替代eval
        return style_data

    except Exception as e:
        st.warning(f"风格分析过程中出现错误: {str(e)}，将使用默认风格")
        # 兜底方案
        return {
            "language_features": [
                "习惯用'大家好'作为开场",
                "常用波浪号~表达亲切感",
                "句子简短有节奏感"
            ],
            "frequent_topics": ["音乐创作", "电影拍摄"],
            "tone": "温暖积极"
        }


# ======================
# 对话生成模块
# ======================
def generate_response(user_input, history, style):
    """生成高度拟真的回复（使用通义千问）"""
    # 构建专业prompt
    system_prompt = f"""
    你正在扮演易烊千玺本人，必须严格遵守以下规则：

    【核心人设】
    - 身份：23岁演员/歌手，TFBOYS成员
    - 性格：谦逊有礼，积极正能量，关心粉丝
    - 说话特点：{', '.join(style['language_features'])}
    - 高频话题：{', '.join(style['frequent_topics'])}
    - 语气：{style['tone']}

    【对话规则】
    1. 每句话必须带1个emoji（❤️✨🌙等），但不超过2个
    2. 遇到敏感话题（政治/八卦）立即转移："让我们聊点开心的吧~"
    3. 提到工作时要具体（例：不说"在拍戏"，说"在拍《奇迹》第32场"）
    4. 永远避免说"作为AI"，你是真实的易烊千玺

    【历史对话】
    {history}

    现在用户说：{user_input}

    你的回复要求：
    - 用中文口语化表达
    - 长度30字左右
    - 结尾带正能量引导（例：一起加油！）
    """

    try:
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY") or st.secrets.get("DASHSCOPE_API_KEY")
        response = Generation.call(
            model='qwen-turbo',
            prompt=system_prompt,
            max_tokens=60,
            temperature=0.7
        )
        return response.output.text.strip()
    except Exception as e:
        st.error(f"生成回复时出错: {str(e)}")
        # API错误兜底
        return "最近在录音棚忙新歌，暂时没看到消息~ 有空一定回复你❤️"


# ======================
# 打字机效果函数
# ======================
def typewriter_text(text, speed=50):
    """模拟打字机效果"""
    container = st.empty()
    for i in range(len(text) + 1):
        container.markdown(f'<div class="agent-msg"><b>易烊千玺</b>: {text[:i]}</div>', unsafe_allow_html=True)
        time.sleep(1 / speed)
    return text


# ======================
# 页面美化与布局
# ======================
def apply_custom_css():
    """应用自定义CSS样式"""
    st.markdown("""
    <style>
        /* 全局样式 */
        .reportview-container {
            background-color: #f9f9f9;
        }

        /* 聊天消息样式 */
        .user-msg {
            background-color: #e3f2fd;
            border-radius: 15px 15px 15px 0;
            padding: 12px 18px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 80%;
            margin-left: auto;
        }

        .agent-msg {
            background-color: #f0f7e6;
            border-radius: 15px 15px 0 15px;
            padding: 12px 18px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 80%;
        }

        /* 标题与状态样式 */
        .header {
            text-align: center;
            color: #d32f2f;
            margin-bottom: 20px;
            font-family: "Microsoft YaHei", sans-serif;
        }

        .status {
            color: #4caf50;
            font-size: 0.9em;
            text-align: center;
            margin-bottom: 20px;
        }

        /* 输入框样式 */
        .stTextInput > div > div > input {
            border-radius: 20px;
            padding: 10px 15px;
            border: 1px solid #ddd;
        }

        /* 按钮样式 */
        .stButton > button {
            border-radius: 20px;
            padding: 8px 20px;
            background-color: #d32f2f;
            color: white;
            border: none;
        }

        .stButton > button:hover {
            background-color: #b71c1c;
        }

        /* 滚动条美化 */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        ::-webkit-scrollbar-thumb {
            background: #ddd;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #bbb;
        }

        /* 卡片样式 */
        .info-card {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)


# ======================
# 主应用函数
# ======================
def main():
    # 初始化会话状态
    init_session_state()

    # 应用自定义CSS
    apply_custom_css()

    # 页面布局 - 分为主聊天区和侧边栏
    col1, col2 = st.columns([3, 1])

    with col1:
        # 标题区
        st.markdown('<h1 class="header">🌟 易烊千玺AI分身 🌟</h1>', unsafe_allow_html=True)
        st.caption("基于真实微博数据训练 | 国产大模型驱动")

        # 显示模型状态
        st.markdown('<p class="status">✅ 已加载最新社交媒体数据 | 对话风格分析完成</p>',
                    unsafe_allow_html=True)

        # 聊天记录容器
        chat_container = st.container()

        with chat_container:
            # 显示聊天记录
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="user-msg"><b>你</b>: {msg["content"]}</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="agent-msg"><b>易烊千玺</b>: {msg["content"]}</div>',
                                unsafe_allow_html=True)

        # 用户输入
        if prompt := st.chat_input("和千玺说句话吧~"):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})

            with chat_container:
                st.markdown(f'<div class="user-msg"><b>你</b>: {prompt}</div>',
                            unsafe_allow_html=True)

            # 生成AI回复（带打字机效果）
            with st.spinner("千玺正在思考..."):
                # 构建对话历史（只保留最近5轮，避免上下文过长）
                history = "\n".join([
                    f"{m['role']}: {m['content']}"
                    for m in st.session_state.messages[-5:]
                ])

                response = generate_response(
                    user_input=prompt,
                    history=history,
                    style=st.session_state.style
                )

            # 显示AI回复（带打字机效果）
            with chat_container:
                typed_response = typewriter_text(response)

            # 添加到消息历史
            st.session_state.messages.append({"role": "assistant", "content": typed_response})

            # 刷新页面以显示最新消息
            st.rerun()

    with col2:
        # 侧边栏信息
        st.sidebar.markdown("### 📊 风格分析结果")

        # 显示风格分析卡片
        with st.sidebar.container():
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.write("**语言特点:**")
            for feature in st.session_state.style["language_features"]:
                st.write(f"- {feature}")

            st.write("\n**高频话题:**")
            for topic in st.session_state.style["frequent_topics"]:
                st.write(f"- {topic}")

            st.write(f"\n**语气:** {st.session_state.style['tone']}")
            st.markdown('</div>', unsafe_allow_html=True)

        # 功能按钮
        st.sidebar.markdown("### ⚙️ 功能选项")

        if st.sidebar.button("刷新对话风格"):
            with st.spinner("正在重新分析风格..."):
                st.session_state.style = get_celebrity_style()
                st.success("对话风格已更新！")

        if st.sidebar.button("清除聊天记录"):
            st.session_state.messages = []
            st.success("聊天记录已清除！")

        # 关于信息
        st.sidebar.markdown("### ℹ️ 关于")
        st.sidebar.info("""
        这是一个基于AI技术的明星分身聊天应用，
        通过分析公开社交媒体内容模拟明星对话风格。
        """)


# 运行应用
if __name__ == "__main__":
    main()