import streamlit as st
import os
from openai import OpenAI # 例としてOpenAIを使用

# -----------------
# 1. 初期設定とAPIクライアント
# -----------------
# APIキーは環境変数などから安全に取得することを推奨
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 3体のAIエージェントの定義
magi_units = {
    "メルキオール (科学者)": "あなたは冷静沈着な科学者です。論理的、客観的、かつデータに基づいて問題を分析し、実現可能性とリスクを最優先に考えた回答を提供してください。",
    "バルタザール (母)": "あなたは母親の視点を持つ倫理学者です。人々の感情、倫理的な影響、長期的な持続可能性を重視し、最も人間的で調和の取れた回答を提供してください。",
    "カスパー (女)": "あなたは女性の視点を持つ実業家です。直感的な判断力と実利を重視し、迅速かつ具体的なアクションプランを盛り込んだ回答を提供してください。"
}

# -----------------
# 2. LLM呼び出し関数
# -----------------
def generate_opinion(unit_name, system_prompt, user_query):
    # API呼び出しの実行
    response = client.chat.completions.create(
        model="gpt-4o-mini", # 使用するモデル
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    return response.choices[0].message.content

# -----------------
# 3. Streamlit UIとメインロジック
# -----------------
st.title("個人用MAGIシステム - 合議制")

# ユーザー入力エリア
user_input = st.text_area("審議したい内容を入力してください：", height=100)
st.markdown("---")

if st.button("審議開始"):
    if user_input:
        # StreamlitのColumns機能で3列を作成
        col1, col2, col3 = st.columns(3)
        
        # 3体のAIからの回答を格納するディクショナリ
        opinions = {}
        
        # 進行状況の表示
        st.info("審議中です...")

        # 各ユニットに対して処理を実行
        # Streamlitでは、API呼び出しに時間がかかるため、並列化（concurrent.futuresなど）を推奨しますが、
        # ここでは分かりやすさのため、直列で記述しています。
        
        with st.spinner("メルキオール 審議中..."):
            opinions["メルキオール (科学者)"] = generate_opinion(
                "メルキオール (科学者)", magi_units["メルキオール (科学者)"], user_input
            )
        
        with st.spinner("バルタザール 審議中..."):
            opinions["バルタザール (母)"] = generate_opinion(
                "バルタザール (母)", magi_units["バルタザール (母)"], user_input
            )

        with st.spinner("カスパー 審議中..."):
            opinions["カスパー (女)"] = generate_opinion(
                "カスパー (女)", magi_units["カスパー (女)"], user_input
            )
            
        st.success("審議完了！意見を比較してください。")

        # 3列に結果を並列表示
        # メルキオール
        with col1:
            st.subheader("メルキオール (科学者)")
            st.markdown(f"**{opinions['メルキオール (科学者)']}**")
            
        # バルタザール
        with col2:
            st.subheader("バルタザール (母)")
            st.markdown(f"**{opinions['バルタザール (母)']}**")
            
        # カスパー
        with col3:
            st.subheader("カスパー (女)")
            st.markdown(f"**{opinions['カスパー (女)']}**")
            
    else:
        st.error("審議内容を入力してください。")

# 実行方法:
# ターミナルで `streamlit run your_script_name.py` を実行