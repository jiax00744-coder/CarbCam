import os
import base64
import json
import re
from datetime import datetime
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 1. 优先从 Streamlit Secrets 读取，如果在本地没有 secrets.toml，则退回读取本地 .env 文件
load_dotenv()
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

# 2. 页面基础配置
st.set_page_config(
    page_title="CarbCam - 智能膳食营养管理",
    page_icon="🥗",
    layout="centered"
)

# 3. 初始化全局状态 (Session State)
if "is_subscribed" not in st.session_state:
    st.session_state.is_subscribed = False  # 默认未订阅/未激活试用

if "health_info" not in st.session_state:
    st.session_state.health_info = {
        "nickname": "",
        "height": 0.0,
        "weight": 0.0,
        "conditions": ""
    }

if "meal_nutrition" not in st.session_state:
    st.session_state.meal_nutrition = {}

if "meal_history" not in st.session_state:
    st.session_state.meal_history = {}


# ==========================================
# 4. 页面顶部：SaaS 订阅与定价展示模块
# ==========================================
st.title("🥑 CarbCam")
st.markdown("### 选择最适合你的健康管理方案")
st.caption("开启智能卡路里与血糖管理，随时随地拍照分析。")

# 自定义 CSS 样式美化三个价格卡片及右上角绿色标签
st.markdown("""
<style>
.pricing-container {
    display: flex;
    gap: 15px;
    margin-bottom: 25px;
}
.pricing-card {
    flex: 1;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    background-color: #ffffff;
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    position: relative;
    transition: transform 0.2s;
}
.pricing-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.08);
}
.pricing-card.featured {
    border: 2px solid #28a745;
}
.badge {
    position: absolute;
    top: -12px;
    right: 15px;
    background-color: #28a745;
    color: white;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: bold;
    border-radius: 20px;
    box-shadow: 0 2px 4px rgba(40,167,69,0.3);
}
.price-title {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
}
.price-amount {
    font-size: 22px;
    font-weight: 800;
    color: #111;
    margin-bottom: 12px;
}
.price-desc {
    font-size: 12px;
    color: #666;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# 渲染三个纵向长方形卡片 (使用 3 列布局)
col_sub1, col_sub2, col_sub3 = st.columns(3)

with col_sub1:
    st.markdown("""
    <div class="pricing-card">
        <div class="price-title">免费试用</div>
        <div class="price-amount">HK$ 0</div>
        <div class="price-desc">体验 7 天全功能 AI 识图与膳食分析</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("开启 7 天试用", use_container_width=True, key="btn_trial"):
        st.session_state.is_subscribed = True
        st.success("🎉 7 天免费试用已激活！")

with col_sub2:
    st.markdown("""
    <div class="pricing-card">
        <div class="price-title">月度会员</div>
        <div class="price-amount">HK$ 18<span style="font-size:12px; font-weight:normal;">/月</span></div>
        <div class="price-desc">适合按月灵活管理饮食与健康的用户</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("订阅月付版", use_container_width=True, key="btn_monthly"):
        st.session_state.is_subscribed = True
        st.success("✅ 感谢订阅月付版！")

with col_sub3:
    st.markdown("""
    <div class="pricing-card featured">
        <div class="badge">30% OFF</div>
        <div class="price-title">年度会员</div>
        <div class="price-amount">HK$ 148<span style="font-size:12px; font-weight:normal;">/年</span></div>
        <div class="price-desc">超高性价比，平均仅需 ~HK$ 12.3/月</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("订阅年付版 (推荐)", type="primary", use_container_width=True, key="btn_annual"):
        st.session_state.is_subscribed = True
        st.success("🚀 感谢订阅年付版！已为您开通全功能。")

st.divider()

# ==========================================
# 5. 界面下方：原有的用户个人档案与核心功能区
# ==========================================
st.header("Hi！请完善你的个人身高体重信息")
st.caption("填写后 AI 将结合你的身体状况量身定制膳食建议。")

with st.form("health_form"):
    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input("1. 昵称", value=st.session_state.health_info["nickname"])
        height = st.number_input("2. 身高 (cm)", min_value=0.0, max_value=250.0, value=float(st.session_state.health_info["height"]), step=0.5)
    with col2:
        weight = st.number_input("3. 体重 (kg)", min_value=0.0, max_value=300.0, value=float(st.session_state.health_info["weight"]), step=0.5)
    
    conditions = st.text_area(
        "4. 身体健康状况及是否有疾病",
        value=st.session_state.health_info["conditions"],
        placeholder="高血压、关注血糖平稳、痛风、无特殊疾病等..."
    )
    
    submit_profile = st.form_submit_button("保存健康档案", type="primary", use_container_width=True)
    if submit_profile:
        st.session_state.health_info = {
            "nickname": nickname,
            "height": height,
            "weight": weight,
            "conditions": conditions
        }
        st.success("✅ 健康档案已成功保存！")

st.divider()

# 6. 美食记录与 AI 分析模块
st.subheader("📸 记录你的美食")

meal_col, photo_col = st.columns(2)
with meal_col:
    selected_meal = st.radio("餐食", ["早", "中", "晚"], horizontal=True)
with photo_col:
    photo_option = st.radio("图片获取方式", ["1. 拍照", "2. 上传"], horizontal=True)

input_food_name = st.text_input(
    "食物名称（可选）",
    placeholder="输入食物名称以提高识别精确度（如：红烧肉盖码饭、无糖拿铁）"
)

# 图片获取方式
if photo_option == "1. 拍照":
    uploaded_file = st.camera_input("调用相机拍照")
else:
    uploaded_file = st.file_uploader("从相册选择图片", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.session_state.current_image_data = uploaded_file

if "current_image_data" in st.session_state and st.session_state.current_image_data is not None:
    st.image(st.session_state.current_image_data, caption="待分析餐盘", use_container_width=True)
    
    if st.button("开始分析", type="primary", use_container_width=True):
        if not st.session_state.is_subscribed:
            st.warning("⚠️ 请先在页面上方的订阅方案中选择试用或购买会员，方可解锁 AI 分析功能！")
        elif not api_key:
            st.error("❌ 未读取到 API Key！请检查 Secrets 或 .env 配置。")
        else:
            with st.spinner("AI 正在解析食物营养，请稍候..."):
                try:
                    # 对接 Kimi (Moonshot) 官方 API 地址
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.moonshot.cn/v1"
                    )
                    
                    bytes_data = st.session_state.current_image_data.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode("utf-8")
                    
                    info = st.session_state.health_info
                    user_context = (
                        f"昵称：{info['nickname'] or '未填写'}，"
                        f"身高：{info['height']}cm，"
                        f"体重：{info['weight']}kg，"
                        f"健康状况：{info['conditions'] or '无'}"
                    )
                    
                    meal_map = {"早": "早餐", "中": "午餐", "晚": "晚餐"}
                    full_meal_name = meal_map.get(selected_meal, selected_meal)
                    food_hint = f"\n用户输入的食物名称：{input_food_name}" if input_food_name.strip() else ""

                    prompt_text = f"""你是一个专业的血糖管理与膳食规划师。
用户的个人健康档案：【{user_context}】
本次分析的餐食分类为：【{full_meal_name}】{food_hint}

请对这张照片中的食物进行分析，严格按照以下 4 点进行输出：
1. 识别食物名称与大概分量；
2. 预估食物各种有关健康的含量，制作成标准的 Markdown 表格（纵轴为食物成分，横轴为预估含量与级别）；
3. 结合【{full_meal_name}】餐食特点及用户健康状况给出合理的进食建议；
4. 请在全篇回复的最末尾，附带一段纯 JSON 格式的数据（必须用 ```json ... ``` 包裹），格式如下：
```json
{{"calories": 热量数值, "carbs": 碳水g数, "protein": 蛋白质g数, "fat": 脂肪g数, "fiber": 膳食纤维g数}}
```"""

                    # 指定模型为 kimi-k3
                    response = client.chat.completions.create(
                        model="kimi-k3",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                    },
                                ],
                            }
                        ],
                        max_tokens=1000,
                    )
                    
                    analysis_result = response.choices[0].message.content
                    
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', analysis_result, re.DOTALL)
                    if json_match:
                        try:
                            parsed_data = json.loads(json_match.group(1))
                            st.session_state.meal_nutrition[full_meal_name] = {
                                "calories": float(parsed_data.get("calories", 0)),
                                "carbs": float(parsed_data.get("carbs", 0)),
                                "protein": float(parsed_data.get("protein", 0)),
                                "fat": float(parsed_data.get("fat", 0)),
                                "fiber": float(parsed_data.get("fiber", 0))
                            }
                            clean_markdown = re.sub(r'```json\s*\{.*?\}\s*```', '', analysis_result, flags=re.DOTALL)
                        except Exception:
                            clean_markdown = analysis_result
                    else:
                        clean_markdown = analysis_result

                    st.success("🎉 分析完成！")
                    st.markdown("### 📋 专属膳食分析报告")
                    st.markdown(clean_markdown)
                    
                    st.session_state.meal_history[full_meal_name] = clean_markdown
                    
                except Exception as e:
                    st.error(f"❌ 分析失败，错误信息: {e}")
