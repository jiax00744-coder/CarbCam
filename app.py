import os
import base64
from datetime import datetime, date
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 1. 读取 Secrets 或 .env
load_dotenv()
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

# 2. 页面基础配置
st.set_page_config(
    page_title="NutriSight",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 3. 辅助函数：计算 BMI
def calculate_bmi(height_cm, weight_kg):
    if height_cm <= 0 or weight_kg <= 0:
        return 0.0, "未填写完整"
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    if bmi < 18.5:
        category = "偏瘦 (Underweight)"
    elif 18.5 <= bmi < 24.0:
        category = "正常 (Normal)"
    elif 24.0 <= bmi < 28.0:
        category = "偏胖 (Overweight)"
    else:
        category = "肥胖 (Obese)"
    return bmi, category

# 4. 多语言字典映射
TRANSLATIONS = {
    "简体中文": {
        "title": "NutriSight",
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
        "profile_caption": "身高: {h}cm | 体重: {w}kg | BMI: {bmi} ({bmi_cat}) | 健康状况: {c}",
        "fill_profile_title": "Hi！请完善你的个人身高体重与健康信息",
        "fill_profile_desc": "填写后 AI 将结合你的 BMI、GI/升糖指数及特殊身体状况（糖尿病、孕期等）量身定制建议。",
        "nickname": "1. 昵称",
        "height": "2. 身高 (cm)",
        "weight": "3. 体重 (kg)",
        "conditions": "4. 身体健康状况/特殊人群（如：糖尿病、孕妇、高血压等）",
        "save_profile_btn": "保存健康档案",
        "section_food": "📸 记录你的美食",
        "select_date": "选择记录日期",
        "meal_type": "餐食分类",
        "img_method": "图片获取方式",
        "cam": "1. 拍照",
        "upload": "2. 上传",
        "food_hint": "食物名称（可选）",
        "food_placeholder": "输入食物名称以提高识别精确度",
        "analyze_btn": "开始分析并记录",
        "section_plan": "📅 制定你的专属健康饮食计划",
        "target_label": "你的核心健康目标",
        "start_date": "计划开始日期",
        "end_date": "计划结束日期",
        "plan_period": "📅 当前计划周期：**{s}** 至 **{e}** | 目标：**{t}**",
        "section_summary": "📝 每日健康总结与分析",
        "gen_summary_btn": "生成选定日期的总结与计划推进分析",
        "unsub_warn": "⚠️ 请先选择上方订阅方案解锁完整 AI 功能！",
    },
    "繁體中文": {
        "title": "NutriSight",
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
        "profile_caption": "身高: {h}cm | 體重: {w}kg | BMI: {bmi} ({bmi_cat}) | 健康狀況: {c}",
        "fill_profile_title": "Hi！請完善你的個人身高體重與健康資訊",
        "fill_profile_desc": "填寫後 AI 將結合你的 BMI、GI/升糖指數及特殊身體狀況（糖尿病、孕期等）量身定制建議。",
        "nickname": "1. 暱稱",
        "height": "2. 身高 (cm)",
        "weight": "3. 體重 (kg)",
        "conditions": "4. 身體健康狀況/特殊人群（如：糖尿病、孕婦、高血壓等）",
        "save_profile_btn": "保存健康檔案",
        "section_food": "📸 記錄你的美食",
        "select_date": "選擇記錄日期",
        "meal_type": "餐食分類",
        "img_method": "圖片獲取方式",
        "cam": "1. 拍照",
        "upload": "2. 上傳",
        "food_hint": "食物名稱（選填）",
        "food_placeholder": "輸入食物名稱以提高識別精確度",
        "analyze_btn": "開始分析並記錄",
        "section_plan": "📅 制定你的專屬健康飲食計劃",
        "target_label": "你的核心健康目標",
        "start_date": "計劃開始日期",
        "end_date": "計劃結束日期",
        "plan_period": "📅 當前計劃週期：**{s}** 至 **{e}** | 目標：**{t}**",
        "section_summary": "📝 每日健康總結與分析",
        "gen_summary_btn": "生成選定日期的總結與計劃推進分析",
        "unsub_warn": "⚠️ 請先選擇上方訂閱方案解鎖完整 AI 功能！",
    },
    "English": {
        "title": "NutriSight",
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
        "profile_caption": "Height: {h}cm | Weight: {w}kg | BMI: {bmi} ({bmi_cat}) | Health Status: {c}",
        "fill_profile_title": "Hi! Please complete your health info",
        "fill_profile_desc": "AI will provide tailored advice based on your BMI, GI (Glycemic Index), and specific conditions.",
        "nickname": "1. Nickname",
        "height": "2. Height (cm)",
        "weight": "3. Weight (kg)",
        "conditions": "4. Health Conditions (e.g., Diabetes, Pregnant, Hypertension)",
        "save_profile_btn": "Save Health Profile",
        "section_food": "📸 Food Tracker",
        "select_date": "Select Log Date",
        "meal_type": "Meal Type",
        "img_method": "Image Source",
        "cam": "1. Camera",
        "upload": "2. Upload",
        "food_hint": "Food Name (Optional)",
        "food_placeholder": "Enter food name for higher recognition accuracy",
        "analyze_btn": "Analyze & Log Meal",
        "section_plan": "📅 Your Custom Health Meal Plan",
        "target_label": "Core Health Goal",
        "start_date": "Start Date",
        "end_date": "End Date",
        "plan_period": "📅 Period: **{s}** to **{e}** | Goal: **{t}**",
        "section_summary": "📝 Daily Health Summary & Progress",
        "gen_summary_btn": "Generate Daily Summary for Selected Date",
        "unsub_warn": "⚠️ Please select a subscription plan above to unlock full AI capabilities!",
    }
}

# 5. 初始化 Session State
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

if "health_goal" not in st.session_state:
    st.session_state.health_goal = "控糖平稳/血糖管理"

# 按日期隔离存储的历史餐盘字典：
# 结构: {"2026-07-23": {"早餐": "报告内容...", "午餐": "报告内容..."}, "2026-07-24": {...}}
if "daily_meal_records" not in st.session_state:
    st.session_state.daily_meal_records = {}

t = TRANSLATIONS[st.session_state.language]


# ==========================================
# 6. 顶部 Header 栏：左侧标题 + 右侧 ⚙️ 系统设置弹窗
# ==========================================
top_col1, top_col2 = st.columns([5, 1])

with top_col1:
    st.markdown("<h1 style='color: #28a745; margin:0; padding:0; font-size: 2.2rem;'>NutriSight</h1>", unsafe_allow_html=True)

with top_col2:
    with st.popover(t["settings"]):
        st.markdown(f"### {t['settings']}")
        st.divider()
        
        # 6.1 修改个人健康信息
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

        # 6.2 语言设置
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

        # 6.3 订阅管理
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
# 7. 首页顶部：订阅卡片
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

if st.session_state.sub_msg:
    st.success(st.session_state.sub_msg)


# ==========================================
# 8. 用户档案区（自动计算 BMI）
# ==========================================
info = st.session_state.health_info
bmi_val, bmi_category = calculate_bmi(info["height"], info["weight"])

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
            placeholder="如：糖尿病、孕妇、高血压、痛风、减重人群等..."
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
    st.caption(t["profile_caption"].format(
        h=info['height'],
        w=info['weight'],
        bmi=bmi_val,
        bmi_cat=bmi_category,
        c=info['conditions'] or '健康无特殊人群标识'
    ))
    st.divider()


# ==========================================
# 9. 核心功能一：📸 记录你的美食（按日期隔离与多天历史记录）
# ==========================================
st.subheader(t["section_food"])

log_date_obj = st.date_input(t["select_date"], value=date.today())
current_date_str = log_date_obj.strftime("%Y-%m-%d")

if current_date_str not in st.session_state.daily_meal_records:
    st.session_state.daily_meal_records[current_date_str] = {}

current_day_records = st.session_state.daily_meal_records[current_date_str]

all_meals = ["早餐", "午餐", "晚餐"]
available_meals = [m for m in all_meals if m not in current_day_records]

if not available_meals:
    st.success(f"🎉【{current_date_str}】的早餐、午餐、晚餐已全部记录完毕！你可以切换其他日期继续记录。")
else:
    meal_col, photo_col = st.columns(2)
    with meal_col:
        selected_meal = st.radio(t["meal_type"], available_meals, horizontal=True)
    with photo_col:
        photo_option = st.radio(t["img_method"], [t["cam"], t["upload"]], horizontal=True)

    input_food_name = st.text_input(
        t["food_hint"],
        placeholder=t["food_placeholder"]
    )

    if photo_option == t["cam"]:
        uploaded_file = st.camera_input("Take Photo", key=f"cam_{current_date_str}_{selected_meal}")
    else:
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], key=f"file_{current_date_str}_{selected_meal}")

    if uploaded_file is not None:
        st.image(uploaded_file, caption=f"待分析餐盘（{current_date_str} {selected_meal}）", use_container_width=True)
        
        if st.button(t["analyze_btn"], type="primary", use_container_width=True):
            if not st.session_state.is_subscribed:
                st.warning(t["unsub_warn"])
            elif not api_key:
                st.error("❌ 未读取到 API Key！请检查 Secrets 或 .env 配置。")
            else:
                with st.spinner("AI 正在深度计算 BMI、升糖指数 (GI) 与具体健康建议..."):
                    try:
                        client = OpenAI(
                            api_key=api_key,
                            base_url="https://open.bigmodel.cn/api/paas/v4/"
                        )
                        
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode("utf-8")
                        
                        user_context = (
                            f"昵称：{info['nickname']}，"
                            f"身高：{info['height']}cm，"
                            f"体重：{info['weight']}kg，"
                            f"BMI：{bmi_val} ({bmi_category})，"
                            f"特殊人群/疾病状况：【{info['conditions'] or '无'}】"
                        )
                        
                        lang_instruction = "Please reply strictly in English." if st.session_state.language == "English" else f"请严格使用【{st.session_state.language}】进行回复。"

                        prompt_text = f"""你是一个高度专业的临床营养师与血糖管理专家。{lang_instruction}

用户的健康档案：【{user_context}】
记录日期与餐次：【{current_date_str} - {selected_meal}】\n用户补充说明：{input_food_name}

请严格按以下四部分输出分析报告：
1. **食物识别**：列出识别出的主要食材及预估分量。
2. **营养成分分析表**（强制使用 Markdown 表格）：
   | 营养成分 | 预估含量 | 健康评估 |
   （必须包含：热量(千卡)、碳水化合物(克)、蛋白质(克)、脂肪(克)、膳食纤维(克)）
3. **📊 BMI 与 GI (升糖指数) 专项评估**：
   - **BMI 适配分析**：结合用户当前 BMI ({bmi_val}, {bmi_category})，评估本餐热量与脂肪摄入是否合适。
   - **餐食 GI 评估**：分析本餐主要碳水属于【高 GI / 中 GI / 低 GI】，预估对餐后血糖升高的冲击程度。
4. **💡 极其具体的个性化膳食调整方案**：
   - **结合特殊人群【{info['conditions']}】**：必须给出具体的落地方案（如：孕妇去冰去生食、糖尿病走糖换无糖、高血压少盐不喝汤底等）。
   - **平稳血糖法**：给出改变进食顺序或搭配建议。"""

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

                        st.session_state.daily_meal_records[current_date_str][selected_meal] = analysis_result
                        st.success(f"🎉 【{current_date_str} {selected_meal}】分析成功并已存档！")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 分析失败: {e}")

if current_day_records:
    st.markdown(f"#### 📋 【{current_date_str}】的餐盘记录列表")
    for m_name, m_report in current_day_records.items():
        with st.expander(f"📌 {current_date_str} - {m_name}分析报告 (点击展开/折叠)", expanded=True):
            st.markdown(m_report)

st.divider()


# ==========================================
# 10. 核心功能二：📅 制定你的专属健康饮食计划
# ==========================================
st.subheader(t["section_plan"])

target_options = ["控糖平稳/血糖管理", "减重瘦身/体脂管理", "孕妇/特殊人群营养平衡", "高血压/高血脂清淡饮食", "增肌塑形"]
st.session_state.health_goal = st.selectbox(t["target_label"], target_options)

date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input(t["start_date"], value=date.today())
with date_col2:
    end_date = st.date_input(t["end_date"], value=date.today())

st.info(t["plan_period"].format(
    s=start_date.strftime('%Y-%m-%d'),
    e=end_date.strftime('%Y-%m-%d'),
    t=st.session_state.health_goal
))

st.divider()


# ==========================================
# 11. 核心功能三：📝 每日健康总结与计划推进分析
# ==========================================
st.subheader(t["section_summary"])
st.caption(f"AI 将调取【{current_date_str}】已记录的餐盘数据，对比你的 BMI 和核心目标生成针对性评估。")

if st.button(t["gen_summary_btn"], type="primary", use_container_width=True):
    if not api_key:
        st.error("❌ 未读取到 API Key！")
    else:
        with st.spinner(f"AI 正在计算【{current_date_str}】的饮食对目标的推进评估..."):
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )
                
                user_info = st.session_state.health_info
                records = st.session_state.daily_meal_records.get(current_date_str, {})
                
                recorded_meals = list(records.keys())
                missing_meals = [m for m in ["早餐", "午餐", "晚餐"] if m not in recorded_meals]
                
                records_text = ""
                for m in ["早餐", "午餐", "晚餐"]:
                    if m in records:
                        records_text += f"\n--- 【{m}记录】 ---\n" + records[m]
                    else:
                        records_text += f"\n--- 【{m}记录】 ---\n（用户本日未记录/未吃{m}）"

                lang_instruction = "Please reply strictly in English." if st.session_state.language == "English" else f"请严格使用【{st.session_state.language}】撰写。"

                summary_prompt = f"""你是一个高级临床健康管理专家。{lang_instruction}

【用户档案】：昵称{user_info['nickname']}，身高{user_info['height']}cm，体重{user_info['weight']}kg，BMI: {bmi_val} ({bmi_category})，健康状况/特殊人群标记：【{user_info['conditions'] or '无'}】。
【当前计划周期目标】：【{st.session_state.health_goal}】。
【评估日期】：【{current_date_str}】。

【用户该日实际摄入与记录】：
{records_text}

请对用户【{current_date_str}】的健康饮食进行全方位评估：
1. **目标推进与 BMI 匹配评估**：结合用户 BMI ({bmi_val}) 和目标【{st.session_state.health_goal}】，评估这天吃的食物对目标的推进效果。
2. **缺漏餐次与健康危害**：如果发现用户在该日漏吃了餐次（未记录：{', '.join(missing_meals) if missing_meals else '无'}），请严肃且关怀地指出不吃{', '.join(missing_meals)}对【{user_info['conditions']}】状况的具体健康危害！
3. **明日食谱改进方案**：针对明日三餐，给出具体的低 GI、营养均衡的食谱搭配建议。"""

                summary_res = client.chat.completions.create(
                    model="glm-4v-flash",
                    messages=[{"role": "user", "content": summary_prompt}],
                    max_tokens=1000
                )
                
                st.success(f"🎉 【{current_date_str}】计划推进总结生成成功！")
                st.markdown("---")
                st.markdown(summary_res.choices[0].message.content)
                
            except Exception as e:
                st.error(f"❌ 总结生成失败: {e}")
