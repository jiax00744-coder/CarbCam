import os
import base64
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
    page_title="CarbCam",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 3. 多语言文本字典映射
TRANSLATIONS = {
    "简体中文": {
        "title": "CarbCam",
        "sub_title": "选择最适合你的健康管理方案",
        "sub_desc": "开启智能热量与血糖管理，随时随地拍照分析。",
        "btn_trial": "开启 7 天试用",
        "btn_monthly": "订阅月付版",
        "btn_annual": "订阅年付版",
        "msg_trial": "🎉 您已成功激活 7 天免费试用，全功能已为您开启！",
        "msg_monthly": "✅ 感谢订阅月付版，全功能已为您开启！",
        "msg_annual": "🚀 感谢订阅年付版，全功能已为您开启！",
        "settings": "⚙️ 系统设置",
        "set_health": "1. 个人健康信息",
        "set_lang": "2. 语言设置 / Language",
        "set_sub": "3. 订阅管理",
        "save_btn": "保存健康信息",
        "hi_msg": "Hi, ",
        "profile_caption": "身高: {h}cm | 体重: {w}kg | 健康状况: {c}",
        "fill_profile_title": "Hi！请完善你的个人身高体重信息",
        "fill_profile_desc": "填写后 AI 将结合你的身体状况量身定制膳食建议。",
        "nickname": "1. 昵称",
        "height": "2. 身高 (cm)",
        "weight": "3. 体重 (kg)",
        "conditions": "4. 身体健康状况及是否有疾病",
        "save_profile_btn": "保存健康档案",
        "section_food": "📸 记录你的美食",
        "meal_type": "餐食分类",
        "breakfast": "早",
        "lunch": "中",
        "dinner": "晚",
        "img_method": "图片获取方式",
        "cam": "1. 拍照",
        "upload": "2. 上传",
        "food_hint": "食物名称（可选）",
        "food_placeholder": "输入食物名称以提高识别精确度",
        "analyze_btn": "开始分析",
        "section_plan": "📅 制定你的专属健康饮食计划",
        "start_date": "计划开始日期",
        "end_date": "计划结束日期",
        "plan_period": "📅 当前计划周期：**{s}** 至 **{e}**",
        "section_summary": "📝 每日健康总结与分析",
        "check_b": "🍳 早餐打卡/记录",
        "check_l": "🍱 午餐打卡/记录",
        "check_d": "🥗 晚餐打卡/记录",
        "gen_summary_btn": "生成今日总结",
        "unsub_warn": "⚠️ 请先选择上方订阅方案解锁完整 AI 功能！",
    },
    "繁體中文": {
        "title": "CarbCam",
        "sub_title": "選擇最適合你的健康管理方案",
        "sub_desc": "開啟智能熱量與血糖管理，隨時隨地拍照分析。",
        "btn_trial": "開啟 7 天試用",
        "btn_monthly": "訂閱月付版",
        "btn_annual": "訂閱年付版",
        "msg_trial": "🎉 您已成功激活 7 天免費試用，全功能已為您開啟！",
        "msg_monthly": "✅ 感謝訂閱月付版，全功能已為您開啟！",
        "msg_annual": "🚀 感謝訂閱年付版，全功能已為您開啟！",
        "settings": "⚙️ 系統設定",
        "set_health": "1. 個人健康資訊",
        "set_lang": "2. 語言設定 / Language",
        "set_sub": "3. 訂閱管理",
        "save_btn": "保存健康資訊",
        "hi_msg": "Hi, ",
        "profile_caption": "身高: {h}cm | 體重: {w}kg | 健康狀況: {c}",
        "fill_profile_title": "Hi！請完善你的個人身高體重資訊",
        "fill_profile_desc": "填寫後 AI 將結合你的身體狀況量身定制膳食建議。",
        "nickname": "1. 暱稱",
        "height": "2. 身高 (cm)",
        "weight": "3. 體重 (kg)",
        "conditions": "4. 身體健康狀況及是否有疾病",
        "save_profile_btn": "保存健康檔案",
        "section_food": "📸 記錄你的美食",
        "meal_type": "餐食分類",
        "breakfast": "早",
        "lunch": "中",
        "dinner": "晚",
        "img_method": "圖片獲取方式",
        "cam": "1. 拍照",
        "upload": "2. 上傳",
        "food_hint": "食物名稱（選填）",
        "food_placeholder": "輸入食物名稱以提高識別精確度",
        "analyze_btn": "開始分析",
        "section_plan": "📅 制定你的專屬健康飲食計劃",
        "start_date": "計劃開始日期",
        "end_date": "計劃結束日期",
        "plan_period": "📅 當前計劃週期：**{s}** 至 **{e}**",
        "section_summary": "📝 每日健康總結與分析",
        "check_b": "🍳 早餐打卡/記錄",
        "check_l": "🍱 午餐打卡/記錄",
        "check_d": "🥗 晚餐打卡/記錄",
        "gen_summary_btn": "生成今日總結",
        "unsub_warn": "⚠️ 請先選擇上方訂閱方案解鎖完整 AI 功能！",
    },
    "English": {
        "title": "CarbCam",
        "sub_title": "Choose the Best Plan for You",
        "sub_desc": "Start smart calorie & blood sugar management anytime, anywhere.",
        "btn_trial": "Start 7-Day Free Trial",
        "btn_monthly": "Subscribe Monthly",
        "btn_annual": "Subscribe Annually",
        "msg_trial": "🎉 You have activated the 7-day free trial. All features unlocked!",
        "msg_monthly": "✅ Thank you for subscribing to Monthly Plan! All features unlocked!",
        "msg_annual": "🚀 Thank you for subscribing to Annual Plan! All features unlocked!",
        "settings": "⚙️ Settings",
        "set_health": "1. Personal Health Profile",
        "set_lang": "2. Language Settings",
        "set_sub": "3. Subscription Management",
        "save_btn": "Save Profile",
        "hi_msg": "Hi, ",
        "profile_caption": "Height: {h}cm | Weight: {w}kg | Health Conditions: {c}",
        "fill_profile_title": "Hi! Please complete your height and weight info",
        "fill_profile_desc": "AI will provide tailored dietary advice based on your health background.",
        "nickname": "1. Nickname",
        "height": "2. Height (cm)",
        "weight": "3. Weight (kg)",
        "conditions": "4. Health conditions or allergies",
        "save_profile_btn": "Save Health Profile",
        "section_food": "📸 Food Tracker",
        "meal_type": "Meal Type",
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "img_method": "Image Source",
        "cam": "1. Camera",
        "upload": "2. Upload",
        "food_hint": "Food Name (Optional)",
        "food_placeholder": "Enter food name for higher recognition accuracy",
        "analyze_btn": "Start Analysis",
        "section_plan": "📅 Your Custom Health Meal Plan",
        "start_date": "Start Date",
        "end_date": "End Date",
        "plan_period": "📅 Plan Period: **{s}** to **{e}**",
        "section_summary": "📝 Daily Health Summary & Analysis",
        "check_b": "🍳 Breakfast Logged",
        "check_l": "🍱 Lunch Logged",
        "check_d": "🥗 Dinner Logged",
        "gen_summary_btn": "Generate Daily Summary",
        "unsub_warn": "⚠️ Please select a subscription plan above to unlock full AI capabilities!",
    }
}

# 4. 初始化 Session State
if "is_subscribed" not in st.session_state:
    st.session_state.is_subscribed = False

if "show_sub_in_settings" not in st.session_state:
    st.session_state.show_sub_in_settings = False

if "language" not in st.session_state:
    st.session_state.language = "简体中文"

if "sub_msg" not in st.session_state:
    st.session_state.sub_msg = ""

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

# 获取当前全局语言字典
t = TRANSLATIONS[st.session_state.language]


# ==========================================
# 5. 顶部 Header 栏：左侧标题 + 右侧 ⚙️ 系统设置弹窗
# ==========================================
top_col1, top_col2 = st.columns([5, 1])

with top_col1:
    st.markdown("<h1 style='color: #28a745; margin:0; padding:0; font-size: 2.2rem;'>CarbCam</h1>", unsafe_allow_html=True)

with top_col2:
    with st.popover(t["settings"]):
        st.markdown(f"### {t['settings']}")
        st.divider()
        
        # 5.1 修改个人健康信息
        st.markdown(f"#### {t['set_health']}")
        info = st.session_state.health_info
        with st.form("settings_health_form"):
            set_nick = st.text_input(t["nickname"], value=info["nickname"])
            set_h = st.number_input(t["height"], value=float(info["height"]))
            set_w = st.number_input(t["weight"], value=float(info["weight"]))
            set_cond = st.text_area(t["conditions"], value=info["conditions"])
            if st.form_submit_button(t["save_btn"], type="primary", use_container_width=True):
                st.session_state.health_info = {
                    "nickname": set_nick,
                    "height": set_h,
                    "weight": set_w,
                    "conditions": set_cond
                }
                st.success("✅ " + t["save_btn"])
                st.rerun()

        st.divider()

        # 5.2 语言设置 (即时切换生效)
        st.markdown(f"#### {t['set_lang']}")
        selected_lang = st.selectbox(
            "Select Language / 选择语言",
            ["简体中文", "繁體中文", "English"],
            index=["简体中文", "繁體中文", "English"].index(st.session_state.language)
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        st.divider()

        # 5.3 订阅管理
        st.markdown(f"#### {t['set_sub']}")
        if st.session_state.is_subscribed:
            st.success("👑 VIP Member Active")
            if st.button("重新显示订阅方案", use_container_width=True):
                st.session_state.is_subscribed = False
                st.rerun()
        else:
            st.info("Status: Not Subscribed")
            if st.button("展开订阅方案卡片", type="primary", use_container_width=True):
                st.session_state.show_sub_in_settings = True
                st.rerun()

st.divider()


# ==========================================
# 6. 首页顶部：订阅卡片（刚进入网站即显示，点击后消失）
# ==========================================
if not st.session_state.is_subscribed or st.session_state.show_sub_in_settings:
    st.markdown(f"### {t['sub_title']}")
    st.caption(t["sub_desc"])

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
        if st.button(t["btn_trial"], use_container_width=True, key="btn_trial"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.session_state.sub_msg = t["msg_trial"]
            st.rerun()

    with col_sub2:
        st.markdown("""
        <div class="pricing-card">
            <div class="price-title">月度会员</div>
            <div class="price-amount">HK$ 18<span style="font-size:12px;">/月</span></div>
            <div class="price-desc">灵活按月订阅</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t["btn_monthly"], use_container_width=True, key="btn_monthly"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.session_state.sub_msg = t["msg_monthly"]
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
        if st.button(t["btn_annual"], type="primary", use_container_width=True, key="btn_annual"):
            st.session_state.is_subscribed = True
            st.session_state.show_sub_in_settings = False
            st.session_state.sub_msg = t["msg_annual"]
            st.rerun()

    st.divider()

# 显示订阅成功精准提示消息
if st.session_state.sub_msg:
    st.success(st.session_state.sub_msg)


# ==========================================
# 7. 用户档案与 Greeting 问候区
# ==========================================
info = st.session_state.health_info
if not info["nickname"]:
    st.header(t["fill_profile_title"])
    st.caption(t["fill_profile_desc"])

    with st.form("health_form"):
        col1, col2 = st.columns(2)
        with col1:
            nickname_in = st.text_input(t["nickname"], value=info["nickname"])
            height_in = st.number_input(t["height"], min_value=0.0, max_value=250.0, value=float(info["height"]), step=0.5)
        with col2:
            weight_in = st.number_input(t["weight"], min_value=0.0, max_value=300.0, value=float(info["weight"]), step=0.5)
        
        conditions_in = st.text_area(
            t["conditions"],
            value=info["conditions"],
            placeholder="高血压、关注血糖平稳、痛风、无特殊疾病等..."
        )
        
        submit_profile = st.form_submit_button(t["save_profile_btn"], type="primary", use_container_width=True)
        if submit_profile:
            st.session_state.health_info = {
                "nickname": nickname_in,
                "height": height_in,
                "weight": weight_in,
                "conditions": conditions_in
            }
            st.rerun()
    st.divider()
else:
    st.subheader(f"{t['hi_msg']}{info['nickname']}")
    st.caption(t["profile_caption"].format(h=info['height'], w=info['weight'], c=info['conditions'] or '无'))
    st.divider()


# ==========================================
# 8. 核心功能一：📸 记录你的美食
# ==========================================
st.subheader(t["section_food"])

meal_col, photo_col = st.columns(2)
with meal_col:
    selected_meal = st.radio(t["meal_type"], [t["breakfast"], t["lunch"], t["dinner"]], horizontal=True)
with photo_col:
    photo_option = st.radio(t["img_method"], [t["cam"], t["upload"]], horizontal=True)

input_food_name = st.text_input(
    t["food_hint"],
    placeholder=t["food_placeholder"]
)

if photo_option == t["cam"]:
    uploaded_file = st.camera_input("Take Photo")
else:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.session_state.current_image_data = uploaded_file

if "current_image_data" in st.session_state and st.session_state.current_image_data is not None:
    st.image(st.session_state.current_image_data, caption="待分析餐盘", use_container_width=True)
    
    if st.button(t["analyze_btn"], type="primary", use_container_width=True):
        if not st.session_state.is_subscribed:
            st.warning(t["unsub_warn"])
        elif not api_key:
            st.error("❌ 未读取到 API Key！请检查 Secrets 或 .env 配置。")
        else:
            with st.spinner("AI 正在解析食物营养并生成表格..."):
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
                    
                    # 彻底移除 JSON 输出要求，强约束使用标准 Markdown 表格
                    prompt_text = f"""你是一个专业的血糖管理与膳食规划师。请使用【{st.session_state.language}】进行回复。
用户的个人健康档案：【{user_context}】
本次分析的餐食分类为：【{selected_meal}】\n用户补充说明：{input_food_name}

请严格按照以下格式输出：
1. 识别食物名称与大概分量；
2. 强制使用 Markdown 格式输出【营养成分分析表格】，包含以下列：
   | 营养成分 | 预估含量 | 健康级别/评估 |
   包含项目：热量(千卡)、碳水化合物(克)、蛋白质(克)、脂肪(克)、膳食纤维(克)；
3. 结合用户健康状况给出合理的进食建议；
（切勿包含任何 JSON 或代码块结构）。"""

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

                    st.success("🎉 分析完成！")
                    st.markdown("### 📋 专属膳食分析报告")
                    st.markdown(analysis_result)
                    
                    st.session_state.meal_history[selected_meal] = analysis_result
                    
                except Exception as e:
                    st.error(f"❌ 分析失败，错误信息: {e}")

st.divider()


# ==========================================
# 9. 核心功能二：📅 制定你的专属健康饮食计划
# ==========================================
st.subheader(t["section_plan"])

date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input(t["start_date"], value=date.today())
with date_col2:
    end_date = st.date_input(t["end_date"], value=date.today())

st.info(t["plan_period"].format(s=start_date.strftime('%Y-%m-%d'), e=end_date.strftime('%Y-%m-%d')))
st.divider()


# ==========================================
# 10. 核心功能三：📝 每日健康总结与分析（全勾选方可解锁生成）
# ==========================================
st.subheader(t["section_summary"])
st.caption("请确认今日早餐、午餐、晚餐均已记录/勾选完成：")

cb1, cb2, cb3 = st.columns(3)
with cb1:
    c_b = st.checkbox(t["check_b"], value=st.session_state.daily_meals_checked["breakfast"])
with cb2:
    c_l = st.checkbox(t["check_l"], value=st.session_state.daily_meals_checked["lunch"])
with cb3:
    c_d = st.checkbox(t["check_d"], value=st.session_state.daily_meals_checked["dinner"])

st.session_state.daily_meals_checked["breakfast"] = c_b
st.session_state.daily_meals_checked["lunch"] = c_l
st.session_state.daily_meals_checked["dinner"] = c_d

# 动态解锁逻辑：只有当三餐全部勾选时，才出现生成今日总结按钮
all_checked = c_b and c_l and c_d

if all_checked:
    st.write("")
    if st.button(t["gen_summary_btn"], type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ 未读取到 API Key！")
        else:
            with st.spinner("AI 正在根据你今日的餐盘记录分析健康总结..."):
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://open.bigmodel.cn/api/paas/v4/"
                    )
                    
                    user_info = st.session_state.health_info
                    history = st.session_state.meal_history
                    
                    history_str = "\n".join([f"【{k}】分析记录:\n{v}" for k, v in history.items()]) if history else "今日用户未进行餐盘拍照识别，全靠自行打卡。"

                    summary_prompt = f"""你是一个专业的健康管理师。请用【{st.session_state.language}】撰写。
用户健康档案：昵称【{user_info['nickname']}】，身高【{user_info['height']}cm】，体重【{user_info['weight']}kg】，健康状况【{user_info['conditions']}】。

今日用户的餐盘识别历史与打卡信息如下：
{history_str}

请结合用户拍照识别过的食物数据与个人身体状况，生成一份【今日综合健康总结与建议】：
1. 评估今日整体摄入的热量、碳水与蛋白质是否均衡；
2. 如果记录中发现用户有漏餐、摄入单一或营养结构不合理（如缺乏蔬菜纤维、碳水超标），请明确严谨地指出危害；
3. 给出针对明日的个性化饮食改进方案与食谱推荐。"""

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
else:
    st.info("💡 请将【早餐】、【午餐】、【晚餐】三个勾选项全部确认勾选后，即可解锁“生成今日总结”按钮。")
