import os
import base64
import json
import re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 从 Streamlit 云端 Secrets 读取 API Key，如果没有则尝试从环境变量/.env读取
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI 客户端（对接 Kimi / Moonshot 接口）
client = OpenAI(
    api_key=api_key,
    base_url="https://api.moonshot.cn/v1"
)

# # 2. 页面基础配置
st.set_page_config(
    page_title="CarbCam - 智能膳食营养管理",
    page_icon="🥗",
    layout="centered"
)

# # 3. 初始化全局状态 (Session State)
if "is_subscribed" not in st.session_state:
    st.session_state.is_subscribed = False  # 默认未订阅/未激活试用

if "health_info" not in st.session_state:
    st.session_state.health_info = {
        "age": 25,
        "gender": "男",
        "height": 175,
        "weight": 65,
        "activity": "中等活动量",
        "goal": "维持体重"
    }

if "history_records" not in st.session_state:
    st.session_state.history_records = []

# 后续你的其他页面组件和功能代码...
