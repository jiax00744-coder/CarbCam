import os
import base64
import json
import re
from datetime import datetime, date
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 1. 优先读取 Secrets，没有则读取 .env
load_dotenv()
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

# 2. 页面基础配置 (隐藏默认侧边栏)
st.set_page_config(
    page_title="CarbCam - 智能膳食营养管理",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 3. 初始化全局状态 (Session State)
if "is_subscribed" not in st.session_state:
    st.session_state.is_subscribed = False

if "show_sub_in_settings" not in st.session_state:
    st.session_state.show_sub_in_settings = False

if "language" not in st.session_state:
    st.session_state.language = "简体中文"

if "health_info" not in st.session_state:
    st.session_state.health_info = {
        "nickname": "",
        "height": 0.0,
        "weight": 0.0,
        "conditions": ""
    }

if "daily_meals_checked" not in st.session_state:
    st.session_state.daily_meals_checked = {
        "breakfast": False,
        "lunch": False,
        "dinner": False
    }

if "meal_history" not in st.session_state:
    st.session_state.meal_history = {}


# ==========================================
# 4. 顶部 Header 栏：左侧标题 + 右侧 ⚙️ 设置弹窗
# ==========================================
top_col1, top_col2 = st.columns([5, 1])

with top_col1:
    st.markdown("<h1 style='color: #28a745; margin:0; padding:0; font-size: 2.2rem;'>CarbCam</h1>", unsafe_allow_html=True)

with top_col2:
    # 右上角齿轮设置按钮 (使用 Popover 弹窗形式)
    with st.popover("⚙️ 设置"):
        st.markdown("### ⚙️ 系统与个人设置")
        st.divider()
        
        # 4.1 修改个人健康信息
        st.markdown("#### 1. 个人健康信息")
        info = st.session_state.health_info
        with st.form("settings_health_form"):
            set_nick = st.text_input("昵称", value=info["nickname"])
            set_h = st.number_input("身高 (cm)", value=float(info["height"]))
            set_w = st.number_input("体重 (kg)", value=float(info["weight"]))
            set_cond = st.text_area("健康状况", value=info["conditions"])
            if st.form_submit_button("保存健康信息", type="primary", use_container_width=True):
                st.session_state.health_info = {
                    "nickname": set_nick,
                    "height": set_h,
                    "weight": set_w,
                    "conditions": set_cond
                }
                st.success("✅ 健康信息已更新！")
                st.rerun()

        st.divider()

        # 4.2 语言切换功能
        st.markdown("#### 2. 语言设置 / Language")
        selected_lang = st.selectbox(
            "选择界面语言",
            ["简体中文", "繁體中文", "English"],
            index=["简体中文", "繁體中文", "English"].index(st.session_state.language)
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.success(f"语言已切换为: {selected_lang}")
            st.rerun()

        st.divider()

        # 4.3 订阅栏目
        st.markdown("#### 3. 会员与订阅管理")
        if st.session_state.is_subscribed:
            st.success("👑 您当前已是激活会员状态")
            if st.button("重新显示订阅方案", use_container_width=True):
                st.session_state.is_subscribed = False
                st.rerun()
        else:
            st.info("当前状态：未订阅")
            if st.button("展开订阅方案卡片", type="primary", use_container_width=True):
                st.session_state.show_sub_in_settings = True
                st.rerun()

st.divider()


# ==========================================
# 5. 首页顶部：订阅卡片区域 (未订阅时显示，点击后消失)
# ==========================================
if not st.session_state.is_subscribed or st.session_state.show_sub_in_settings:
    st.markdown("### 选择最适合你的健康管理方案")
    st.caption("开启智能热量与血糖管理，随时随地拍照分析。")

    st.markdown("""
    <style>
    .pricing-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        position: relative;
    }
    .pricing-card.featured {
        border: 2px solid #28a745;
    }
    .badge {
        position: absolute;
        top: -10px;
        right: 10px;
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: bold;
        border-radius: 10px;
    }
    .price-title { font-size: 15px; font-weight: bold; color: #333; }
    .price-amount { font-size: 20px; font-weight: 800; color: #111; margin: 8px 0; }
    .price-desc { font-size: 11px; color: #666; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

    col_sub1, col_sub2, col_sub3 = st.columns(3)

    with col_sub1:
        st.markdown("""
        <div class="pricing-card">
            <div class="price-title">免费试用</div>
            <div class="price-amount">HK$ 0</div>
            <div class="price-desc">体验 7 天全功能 AI 识图</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("开启 7 天试用", use_container_width=True, key="btn_trial"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.rerun()

    with col_sub2:
        st.markdown("""
        <div class="pricing-card">
            <div class="price-title">月度会员</div>
            <div class="price-amount">HK$ 18<span style="font-size:12px;">/月</span></div>
            <div class="price-desc">灵活按月订阅</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("订阅月付版", use_container_width=True, key="btn_monthly"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.rerun()

    with col_sub3:
        st.markdown("""
        <div class="pricing-card featured">
            <div class="badge">30% OFF</div>
            <div class="price-title">年度会员</div>
            <div class="price-amount">HK$ 148<span style="font-size:12px;">/年</span></div>
            <div class="price-desc">超高性价比推荐</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("订阅年付版", type="primary", use_container_width=True, key="btn_annual"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.rerun()

    st.divider()


# ==========================================
# 6. 用户档案与 Greeting 问候
# ==========================================
info = st.session_state.health_info
if not info["nickname"]:
    st.header("Hi！请完善你的个人身高体重信息")
    st.caption("填写后 AI 将结合你的身体状况量身定制膳食建议。")

    with st.form("health_form"):
        col1, col2 = st.columns(2)
        with col1:
            nickname_in = st.text_input("1. 昵称", value=info["nickname"])
            height_in = st.number_input("2. 身高 (cm)", min_value=0.0, max_value=250.0, value=float(info["height"]), step=0.5)
        with col2:
            weight_in = st.number_input("3. 体重 (kg)", min_value=0.0, max_value=300.0, value=float(info["weight"]), step=0.5)
        
        conditions_in = st.text_area(
            "4. 身体健康状况及是否有疾病",
            value=info["conditions"],
            placeholder="高血压、关注血糖平稳、痛风、无特殊疾病等..."
        )
        
        submit_profile = st.form_submit_button("保存健康档案", type="primary", use_container_width=True)
        if submit_profile:
            st.session_state.health_info = {
                "nickname": nickname_in,
                "height": height_in,
                "weight": weight_in,
                "conditions": conditions_in
            }
            st.success("✅ 健康档案已成功保存！")
            st.rerun()
    st.divider()
else:
    st.subheader(f"Hi, {info['nickname']}")
    st.caption(f"身高: {info['height']}cm | 体重: {info['weight']}kg | 健康状况: {info['conditions'] or '无'}")
    st.divider()


# ==========================================
# 7. 核心功能一：📸 记录你的美食 (识图分析)
# ==========================================
st.subheader("📸 记录你的美食")

meal_col, photo_col = st.columns(2)
with meal_col:
    selected_meal = st.radio("餐食分类", ["早", "中", "晚"], horizontal=True)
with photo_col:
    photo_option = st.radio("图片获取方式", ["1. 拍照", "2. 上传"], horizontal=True)

input_food_name = st.text_input(
    "食物名称（可选）",
    placeholder="输入食物名称以提高识别精确度"
)

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
            with st.spinner("AI 正在解析食物营养并生成表格，请稍候..."):
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://open.bigmodel.cn/api/paas/v4/"
                    )
                    
                    bytes_data = st.session_state.current_image_data.getvalue()
                    base64_image = base64.b64encode(bytes_data).decode("utf-8")
                    
                    user_context = (
                        f"昵称：{info['nickname'] or '未填写'}，"
                        f"身高：{info['height']}cm，"
                        f"体重：{info['weight']}kg，"
                        f"健康状况：{info['conditions'] or '无'}"
                    )
                    
                    meal_map = {"早": "早餐", "中": "午餐", "晚": "晚餐"}
                    full_meal_name = meal_map.get(selected_meal, selected_meal)
                    food_hint = f"\n用户输入的食物名称：{input_food_name}" if input_food_name.strip() else ""

                    # 强约束 Markdown 表格输出与全中文表述
                    prompt_text = f"""你是一个专业的血糖管理与膳食规划师。
用户的个人健康档案：【{user_context}】
本次分析的餐食分类为：【{full_meal_name}】{food_hint}

请对这张照片中的食物进行深入分析，严格按顺序输出以下内容：
1. 识别食物名称与大概分量；
2. 强制使用 Markdown 格式生成一个【营养成分分析表格】，表格列名必须为：| 营养成分 | 预估含量 | 健康级别/评估 |；
   表格必须包含的行：热量(千卡)、碳水化合物(克)、蛋白质(克)、脂肪(克)、膳食纤维(克)。
3. 结合【{full_meal_name}】餐食特点及用户健康状况，给出合理的进食建议；
4. 请在全篇回复的最末尾，附带一段纯 JSON 格式的数据（必须用 ```json ... ``` 包裹），格式如下：
```json
{{"热量(千卡)": 数值, "碳水化合物(克)": 数值, "蛋白质(克)": 数值, "脂肪(克)": 数值, "膳食纤维(克)": 数值}}
```"""

                    response = client.chat.completions.create(
                        model="glm-4v-flash",
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
                    
                    # 过滤纯 JSON 部分，确保页面展示美观的 Markdown 表格
                    clean_markdown = re.sub(r'```json\s*\{.*?\}\s*```', '', analysis_result, flags=re.DOTALL)

                    st.success("🎉 分析完成！")
                    st.markdown("### 📋 专属膳食分析报告")
                    st.markdown(clean_markdown)
                    
                    st.session_state.meal_history[full_meal_name] = clean_markdown
                    
                except Exception as e:
                    st.error(f"❌ 分析失败，错误信息: {e}")

st.divider()


# ==========================================
# 8. 核心功能二：📅 制定你的专属健康饮食计划 & 每日打卡
# ==========================================
st.subheader("📅 制定你的专属健康饮食计划")
st.caption("选择计划周期，记录每日打卡并生成智能诊断。")

# 8.1 日期选择功能（从某日到某日）
date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input("计划开始日期", value=date.today())
with date_col2:
    end_date = st.date_input("计划结束日期", value=date.today())

st.info(f"📅 当前计划周期：**{start_date.strftime('%Y-%m-%d')}** 至 **{end_date.strftime('%Y-%m-%d')}**")

# 8.2 每日用餐勾选记录
st.markdown("#### 🥗 今日用餐打卡记录")
st.caption("请勾选你今天已经进食的餐次：")

c_b = st.checkbox("🍳 早餐", value=st.session_state.daily_meals_checked["breakfast"])
c_l = st.checkbox("🍱 午餐", value=st.session_state.daily_meals_checked["lunch"])
c_d = st.checkbox("🥗 晚餐", value=st.session_state.daily_meals_checked["dinner"])

st.session_state.daily_meals_checked["breakfast"] = c_b
st.session_state.daily_meals_checked["lunch"] = c_l
st.session_state.daily_meals_checked["dinner"] = c_d


# ==========================================
# 9. 核心功能三：📝 每日总结与智能漏餐建议
# ==========================================
st.markdown("#### 📝 每日健康总结与分析")

if st.button("生成今日总结", type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 未读取到 API Key，请先配置 Key！")
    else:
        with st.spinner("AI 正在根据你的今日用餐打卡情况生成总结与建议..."):
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )
                
                chk = st.session_state.daily_meals_checked
                user_info = st.session_state.health_info
                
                # 收集漏餐情况
                missed_meals = []
                eaten_meals = []
                if not chk["breakfast"]:
                    missed_meals.append("早餐")
                else:
                    eaten_meals.append("早餐")
                    
                if not chk["lunch"]:
                    missed_meals.append("午餐")
                else:
                    eaten_meals.append("午餐")
                    
                if not chk["dinner"]:
                    missed_meals.append("晚餐")
                else:
                    eaten_meals.append("晚餐")

                summary_prompt = f"""你是一个专业的健康管理师。
用户的健康档案：昵称【{user_info['nickname'] or '未填写'}】，身高【{user_info['height']}cm】，体重【{user_info['weight']}kg】，健康状况【{user_info['conditions'] or '无'}】。

今日用户的用餐打卡情况如下：
- 已进食：{', '.join(eaten_meals) if eaten_meals else '无'}
- 未勾选/未进食：{', '.join(missed_meals) if missed_meals else '无（三餐均正常进食）'}

请为用户生成一份【今日总结与建议】：
1. 评判今日的整体进食规律性；
2. 【重点要求】：如果用户有漏吃的餐次（如未吃{', '.join(missed_meals)}），请严厉且温柔地指出“绝对不能不吃{'/'.join(missed_meals)}”的原因（包括对血糖、新陈代谢和身体健康的损害）；
3. 针对未吃的餐次，给出具体的补充食谱建议（推荐具体的早餐、午餐或晚餐食物组合）；
4. 针对明天给出合理的饮食规划建议。"""

                summary_res = client.chat.completions.create(
                    model="glm-4v-flash",
                    messages=[{"role": "user", "content": summary_prompt}],
                    max_tokens=1000
                )
                
                st.success("🎉 今日总结生成成功！")
                st.markdown("---")
                st.markdown(summary_res.choices[0].message.content)
                
            except Exception as e:
                st.error(f"❌ 总结生成失败: {e}")
