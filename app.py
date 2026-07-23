import base64
import datetime
import json
import os
import re
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
import streamlit as st

# 1. 页面基本配置（隐藏侧边栏，页面居中）
st.set_page_config(
    page_title="CarbCam",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式（修复暗黑模式下的白色亮块问题）
st.markdown("""
    <style>
    /* 全局圆角按钮样式 */
    div.stButton > button {
        border-radius: 12px;
        height: 2.8em;
        font-weight: bold;
        font-size: 16px;
    }
    /* 首次信息收集卡片背景：改为半透明自适应深色 */
    .health-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    /* AI 总结卡片 */
    .summary-card {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 18px;
        border-radius: 12px;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 加载环境变量与 API 初始化
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 初始化 Session State
if "health_info" not in st.session_state:
    st.session_state.health_info = {
        "submitted": False,
        "nickname": "",
        "height": 0.0,
        "weight": 0.0,
        "conditions": ""
    }

if "meal_history" not in st.session_state:
    st.session_state.meal_history = {
        "早餐": None,
        "午餐": None,
        "晚餐": None
    }

# 用于存储三餐精确解析出的营养成分数据，供柱状图/折线图使用
if "meal_nutrition" not in st.session_state:
    st.session_state.meal_nutrition = {
        "早餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0},
        "午餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0},
        "晚餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0}
    }

if "daily_summary" not in st.session_state:
    st.session_state.daily_summary = None


# ----------------- 🔝 顶栏：左上角 CarbCam(果蔬绿) + 右上角 ⚙️ 设置 -----------------
top_col1, top_col2 = st.columns([3, 1])

with top_col1:
    st.markdown("<h2 style='margin:0; padding:0; color:#16a34a; font-weight:800;'>CarbCam</h2>", unsafe_allow_html=True)

with top_col2:
    with st.popover("⚙️ 设置", use_container_width=True):
        st.subheader("⚙️ 设置选项")
        setting_tab = st.radio("功能", ["个人健康信息", "重置今天打卡", "关于 CarbCam"])
        
        if setting_tab == "个人健康信息":
            st.markdown("---")
            st.write("<b>修改个人档案</b>", unsafe_allow_html=True)
            new_nickname = st.text_input("昵称", value=st.session_state.health_info["nickname"])
            new_height = st.number_input("身高 (cm)", value=float(st.session_state.health_info["height"] or 0.0), min_value=0.0)
            new_weight = st.number_input("体重 (kg)", value=float(st.session_state.health_info["weight"] or 0.0), min_value=0.0)
            new_conditions = st.text_area("健康状况及疾病", value=st.session_state.health_info["conditions"])
            
            if st.button("保存修改", use_container_width=True):
                st.session_state.health_info.update({
                    "nickname": new_nickname,
                    "height": new_height,
                    "weight": new_weight,
                    "conditions": new_conditions,
                    "submitted": True
                })
                st.success("健康档案已保存！")
                st.rerun()

        elif setting_tab == "重置今天打卡":
            st.markdown("---")
            if st.button("清空今天打卡记录", use_container_width=True):
                st.session_state.meal_history = {"早餐": None, "午餐": None, "晚餐": None}
                st.session_state.meal_nutrition = {
                    "早餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0},
                    "午餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0},
                    "晚餐": {"calories": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0}
                }
                st.session_state.daily_summary = None
                st.success("已重置记录！")
                st.rerun()

        elif setting_tab == "关于 CarbCam":
            st.markdown("---")
            st.info("CarbCam v3.0 - 智能膳食分析与血糖领航助手")


# ----------------- 🏠 主界面内容 -----------------

# 1. 首次进入：填写个人健康信息
if not st.session_state.health_info["submitted"]:
    st.title("Hi！请完善你的个人身体健康信息")
    st.caption("填写后 AI 将结合你的身体状况量身定制膳食建议。")
    
    st.markdown('<div class="health-card">', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        input_nickname = st.text_input("1. 昵称", placeholder="")
        input_height = st.number_input("2. 身高 (cm)", min_value=0.0, max_value=250.0, value=0.0)
    with col_b:
        input_weight = st.number_input("3. 体重 (kg)", min_value=0.0, max_value=200.0, value=0.0)
        
    input_conditions = st.text_area(
        "4. 身体健康状况及是否有疾病", 
        placeholder="高血压、关注血糖平稳、痛风、无特殊疾病等..."
    )
    
    if st.button("保存健康档案", type="primary", use_container_width=True):
        if not input_nickname.strip():
            st.error("请填写昵称！")
        else:
            st.session_state.health_info = {
                "submitted": True,
                "nickname": input_nickname,
                "height": input_height,
                "weight": input_weight,
                "conditions": input_conditions or "无特殊疾病"
            }
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # 2. 填写完成后：顶部显示 Hi + 昵称
    user_name = st.session_state.health_info["nickname"]
    st.title(f"Hi，{user_name}！")
    st.caption("拍照或上传餐盘，获取专属 AI 膳食分析与进食建议")
    st.markdown("---")

    # 3. 记录美食栏目
    st.subheader("📸 记录你的美食")
    
    meal_col, photo_col = st.columns(2)
    
    with meal_col:
        selected_meal = st.radio(
            "餐食",
            ["早", "中", "晚"],
            horizontal=True
        )
        
    with photo_col:
        photo_option = st.radio(
            "图片获取方式",
            ["1. 拍照", "2. 上传"],
            horizontal=True
        )

    # 🆕 新增：食物名称输入框
    input_food_name = st.text_input(
        "食物名称",
        placeholder="输入食物名称以提高识别精确度（如：红烧肉盖码饭、无糖拿铁）"
    )

    uploaded_image = None
    if photo_option == "1. 拍照":
        uploaded_image = st.camera_input("调用相机拍照")
    else:
        uploaded_image = st.file_uploader("从相册选择图片", type=["jpg", "jpeg", "png"])

    # 食物分析与 API 调用
    if uploaded_image:
        st.image(uploaded_image, caption="待分析餐盘", use_container_width=True)
        
        if st.button("开始分析", type="primary", use_container_width=True):
            if not api_key:
                st.error("未找到 API Key，请检查 .env 文件！")
            else:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )
                
                bytes_data = uploaded_image.getvalue()
                base64_image = base64.b64encode(bytes_data).decode("utf-8")
                
                info = st.session_state.health_info
                user_context = (
                    f"用户昵称：{info['nickname']}，身高：{info['height']}cm，"
                    f"体重：{info['weight']}kg，身体健康状况及疾病：{info['conditions']}"
                )
                
                # 转换选中的餐食名称
                meal_map = {"早": "早餐", "中": "午餐", "晚": "晚餐"}
                full_meal_name = meal_map.get(selected_meal, selected_meal)
                
                # 用户提示食物名称
                food_hint = f"\n【用户输入的参考食物名称】：{input_food_name}（请重点参考此信息辅助识别）" if input_food_name.strip() else ""

                # Prompt：严格控制 Markdown 输出并在末尾附带用于生成图表的 JSON
                prompt_text = f"""
你是一个专业的血糖管理与膳食规划师。
用户的个人健康档案如下：
【{user_context}】
本次分析的餐食分类为：【{full_meal_name}】{food_hint}

请对这张照片中的食物进行分析，严格按照以下 4 点进行输出：

1. 识别食物名称与大概分量（如果用户提供了参考食物名称，请结合图片进行验证）；

2. 预估食物各种有关健康的含量，制作成标准的 Markdown 表格（纵轴为食物不同成分，横轴为“预估含量”与“级别”）：
   - 必须包含：热量(kcal)、碳水化合物总量(g)、GI值、蛋白质(g)、脂肪(g)、膳食纤维(g)等关键成分。
   - 级别包括：高 / 中 / 低。

3. 结合【{full_meal_name}】的餐食特点以及用户的实际健康状况（{user_context}）给出合理的进食建议：
   - 必须结合【{full_meal_name}】这一具体餐次进行针对性评估。
   - 切忌盲目给建议或一味要求减少摄入！如果搭配合理请直接肯定。只有在成分确实偏高时才给出温和平抑血糖与健康的微调方案。

4. 【非常重要】为了方便系统制作统计图表，请在全篇回复的最末尾，附带一段纯 JSON 格式的数据（必须用 ```json ... ``` 包裹），格式如下：
```json
{{"calories": 热量数值, "carbs": 碳水g数, "protein": 蛋白质g数, "fat": 脂肪g数, "fiber": 膳食纤维g数}}
