import os
import base64
import json
import re
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# 1. 优先读取 Secrets，没有则读取 .env
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
    st.session_state.is_subscribed = False  # 默认未订阅

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
# 4. 侧边栏导航 (找回计划与设置页面)
# ==========================================
st.sidebar.title("📌 导航菜单")
page = st.sidebar.radio("选择页面", ["📸 美食记录", "📅 膳食计划", "⚙️ 个人设置"])

st.sidebar.divider()
if st.session_state.is_subscribed:
    st.sidebar.success("👑 会员状态：已激活")
else:
    st.sidebar.info("💡 状态：未订阅会员")


# ==========================================
# 页面 1：📸 美食记录 (主核心区)
# ==========================================
if page == "📸 美食记录":

    # 1.1 绿色标题 (去除了 🥑 图标)
    st.markdown("<h1 style='color: #28a745; font-size: 2.2rem;'>CarbCam</h1>", unsafe_allow_html=True)

    # 1.2 订阅模块：用户未订阅时显示，点击任意订阅按钮后该区域自动删除/隐藏
    if not st.session_state.is_subscribed:
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
                st.rerun()

        st.divider()

    # 1.3 个人健康档案模块：未填写时显示表单，填写保存后隐藏表单，直接显示 "Hi, [用户名字]"
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
        # 已填写后，直接简洁显示 Greeting 问候语
        st.subheader(f"Hi, {info['nickname']}")
        st.caption(f"身高: {info['height']}cm | 体重: {info['weight']}kg | 健康状况: {info['conditions'] or '无'}")
        st.divider()

    # 1.4 核心：美食记录与 AI 分析模块
    st.subheader("📸 记录你的美食")

    meal_col, photo_col = st.columns(2)
    with meal_col:
        selected_meal = st.radio("餐食", ["早", "中", "晚"], horizontal=True)
    with photo_col:
        photo_option = st.radio("图片获取方式", ["1. 拍照", "2. 上传"], horizontal=True)

    # 精简占位符：只写“输入食物名称以提高识别精确度”
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
                with st.spinner("AI 正在解析食物营养，请稍候..."):
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

                        # 提示词修改：强约束使用全中文表述 + 强制输出标准 Markdown 营养表格
                        prompt_text = f"""你是一个专业的血糖管理与膳食规划师。
用户的个人健康档案：【{user_context}】
本次分析的餐食分类为：【{full_meal_name}】{food_hint}

请对这张照片中的食物进行深入分析，严格按照以下 4 点要求进行输出（所有营养成分名称与单位必须全部使用中文）：
1. 识别食物名称与大概分量；
2. 制作一个清晰易读的 Markdown 格式【营养成分表格】，表格需包含：热量(千卡)、碳水化合物(克)、蛋白质(克)、脂肪(克)、膳食纤维(克)；
3. 结合【{full_meal_name}】餐食特点及用户的健康状况，给出合理的进食建议；
4. 请在全篇回复的最末尾，附带一段纯 JSON 格式的数据（必须用 ```json ... ``` 包裹），所有字段名及数值如下：
```json
{{"热量(千卡)": 热量数值, "碳水化合物(克)": 碳水数值, "蛋白质(克)": 蛋白质数值, "脂肪(克)": 脂肪数值, "膳食纤维(克)": 膳食纤维数值}}
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
                        
                        # 解析后置 JSON，保存数据，并在前端把原始的 JSON 代码块隐藏，只呈现优雅的分析与表格
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', analysis_result, re.DOTALL)
                        if json_match:
                            clean_markdown = re.sub(r'```json\s*\{.*?\}\s*```', '', analysis_result, flags=re.DOTALL)
                        else:
                            clean_markdown = analysis_result

                        st.success("🎉 分析完成！")
                        st.markdown("### 📋 专属膳食分析报告")
                        st.markdown(clean_markdown)
                        
                        st.session_state.meal_history[full_meal_name] = clean_markdown
                        
                    except Exception as e:
                        st.error(f"❌ 分析失败，错误信息: {e}")


# ==========================================
# 页面 2：📅 膳食计划 (恢复之前的计划功能)
# ==========================================
elif page == "📅 膳食计划":
    st.markdown("<h1 style='color: #28a745; font-size: 2.0rem;'>📅 专属膳食计划</h1>", unsafe_allow_html=True)
    st.caption("基于你的个人身体数据与健康目标，AI 为你量身推荐的每日三餐方案。")
    st.divider()

    info = st.session_state.health_info
    if not info["nickname"]:
        st.warning("⚠️ 请先在“📸 美食记录”页面填写并保存你的基本个人档案（身高、体重与健康状况）！")
    else:
        st.markdown(f"**当前档案**：{info['nickname']}（身高: {info['height']}cm / 体重: {info['weight']}kg）")
        
        target = st.selectbox("你的健康目标", ["平稳血糖/控糖", "减脂瘦身", "增肌塑形", "均衡日常饮食"])
        
        if st.button("生成今日推荐定制计划", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ 未检测到 API Key，请先配置 Key。")
            else:
                with st.spinner("AI 正在为你规划最佳膳食组合..."):
                    try:
                        client = OpenAI(
                            api_key=api_key,
                            base_url="https://open.bigmodel.cn/api/paas/v4/"
                        )
                        plan_prompt = f"""作为专业营养师，请为用户【{info['nickname']}】生成一日三餐健康计划。
用户数据：身高 {info['height']}cm，体重 {info['weight']}kg，健康状况：{info['conditions'] or '无特殊'}。
健康目标：{target}。

请用优雅的 Markdown 格式输出：
1. 一日总建议热量与三大营养素比例；
2. 【早餐】推荐菜谱与控糖/健康建议；
3. 【午餐】推荐菜谱与控糖/健康建议；
4. 【晚餐】推荐菜谱与控糖/健康建议；
5. 针对该用户健康状况的特别提示。"""

                        plan_res = client.chat.completions.create(
                            model="glm-4v-flash",
                            messages=[{"role": "user", "content": plan_prompt}],
                            max_tokens=1000
                        )
                        st.markdown(plan_res.choices[0].message.content)
                    except Exception as e:
                        st.error(f"❌ 计划生成失败: {e}")


# ==========================================
# 页面 3：⚙️ 个人设置 (恢复设置功能)
# ==========================================
elif page == "⚙️ 个人设置":
    st.markdown("<h1 style='color: #28a745; font-size: 2.0rem;'>⚙️ 个人设置</h1>", unsafe_allow_html=True)
    st.caption("管理你的健康档案、会员状态与偏好设置。")
    st.divider()

    st.subheader("1. 重新修改健康档案")
    info = st.session_state.health_info
    with st.form("edit_profile_form"):
        new_nick = st.text_input("昵称", value=info["nickname"])
        new_h = st.number_input("身高 (cm)", value=float(info["height"]))
        new_w = st.number_input("体重 (kg)", value=float(info["weight"]))
        new_cond = st.text_area("健康状况及特殊需求", value=info["conditions"])
        
        if st.form_submit_button("更新个人档案", type="primary"):
            st.session_state.health_info = {
                "nickname": new_nick,
                "height": new_h,
                "weight": new_w,
                "conditions": new_cond
            }
            st.success("✅ 个人档案已更新！")

    st.divider()
    st.subheader("2. 会员与订阅状态")
    if st.session_state.is_subscribed:
        st.success("已激活会员功能。")
        if st.button("取消当前订阅/重置体验"):
            st.session_state.is_subscribed = False
            st.rerun()
    else:
        st.info("当前未订阅。你可以随时在美食记录页激活订阅试用。")
