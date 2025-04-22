import streamlit as st
import pandas as pd

# --- データ読み込み関数 ---
@st.cache_data
def load_data():
    df_cosmic_oculus = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_Cosmic:Oculus.csv")
    df_crystal_pylon = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_Crystal:Pylon.csv")
    df_volt = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_Volt.csv")
    df_archmage = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_ArchMage.csv")
    df_flak = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_Flak.csv")
    df_mage_lightning = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/TowerMergeOptimizer/main/Data_Mage:Lightning.csv")
    return {
        "Cosmic/Oculus": df_cosmic_oculus,
        "Crystal/Pylon": df_crystal_pylon,
        "Volt": df_volt,
        "ArchMage": df_archmage,
        "Flak": df_flak,
        "Mage/Lightning": df_mage_lightning
    }

df_dict = load_data()

# --- 統合後のレベルを計算 ---
def calculate_merged_level(base_df, base_level, material_list):
    # ベースの累積値
    base_rubble = base_df[base_df['level'] == base_level]['culmative_rubble'].values[0]
    base_xp = base_df[base_df['level'] == base_level]['XP_culmative'].values[0]

    # 素材の合計
    total_rubble = 0
    total_xp = 0
    resource_after = {
        "ElectrumBar": 0,
        "ElementalEmber": 0,
        "CosmicCharge": 0,
        "time(days)": 0
    }

    for material in material_list:
        mat_df = df_dict[material['type']]
        row = mat_df[mat_df['level'] == material['level']]
        if not row.empty:
            count = material['count']
            total_rubble += int(row['culmative_rubble'].values[0]) * count
            total_xp += int(row['XP_culmative'].values[0]) * count
            resource_after["ElectrumBar"] += int(row['electrumBar_culmative'].values[0]) * count
            resource_after["ElementalEmber"] += int(row['elementalEmber_culmative'].values[0]) * count
            resource_after["CosmicCharge"] += int(row['cosmicCharge_culmative'].values[0]) * count
            resource_after["time(days)"] += float(row['time_culmative(days)'].values[0]) * count

    # 合計値を加算
    merged_rubble = base_rubble + total_rubble
    merged_xp = base_xp + total_xp

    # 統合後のレベルを求める
    result_df = base_df[base_df['culmative_rubble'] <= merged_rubble]
    if result_df.empty:
        final_level = base_level
    else:
        final_level = result_df.iloc[-1]['level']

    # リソース比較
    target_row = base_df[base_df['level'] == final_level]
    resource_before = {
        "ElectrumBar": int(target_row['electrumBar_culmative'].values[0]) - base_df[base_df['level'] == base_level]['electrumBar_culmative'].values[0],
        "ElementalEmber": int(target_row['elementalEmber_culmative'].values[0]) - base_df[base_df['level'] == base_level]['elementalEmber_culmative'].values[0],
        "CosmicCharge": int(target_row['cosmicCharge_culmative'].values[0]) - base_df[base_df['level'] == base_level]['cosmicCharge_culmative'].values[0],
        "time(days)": float(target_row['time_culmative(days)'].values[0]) - base_df[base_df['level'] == base_level]['time_culmative(days)'].values[0]
    }

    # 効率
    efficiency = round((total_rubble / (target_row['culmative_rubble'].values[0] - base_rubble)) * 100, 1) if (target_row['culmative_rubble'].values[0] - base_rubble) > 0 else 100

    return int(final_level), efficiency, resource_before, resource_after

# --- UI部 ---
st.title("タワー統合計算")

tower_type = st.selectbox("統合対象タワーを選択", list(df_dict.keys()))
initial_level = st.number_input("初期レベル", min_value=1, max_value=200, step=1)

st.markdown("### 統合に使用するタワー")

material_rows = []
if "material_rows" not in st.session_state:
    st.session_state.material_rows = 1

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("テンプレート行を追加"):
        st.session_state.material_rows += 1
with col2:
    if st.button("行をリセット"):
        st.session_state.material_rows = 1

for i in range(st.session_state.material_rows):
    st.markdown(f"#### 素材タワー {i+1}")
    col1, col2, col3 = st.columns(3)
    with col1:
        mat_type = st.selectbox(f"タワー種別 {i+1}", list(df_dict.keys()), key=f"type_{i}")
    with col2:
        mat_level = st.number_input(f"レベル {i+1}", min_value=1, max_value=200, step=1, key=f"level_{i}")
    with col3:
        mat_count = st.number_input(f"個数 {i+1}", min_value=1, max_value=50, step=1, key=f"count_{i}")
    material_rows.append({
        "type": mat_type,
        "level": mat_level,
        "count": mat_count
    })

if st.button("計算実行"):
    df_target = df_dict[tower_type]
    merged_level, efficiency, before_res, after_res = calculate_merged_level(df_target, initial_level, material_rows)

    st.subheader("統合後のレベル")
    st.write(f"Lv.{merged_level}")

    st.subheader("リソース活用効率")
    st.write(f"{efficiency}%")

    st.subheader("リソース比較表")
    df_compare = pd.DataFrame({
        "Resource": ["ElectrumBar", "ElementalEmber", "CosmicCharge", "Time (days)"],
        "Before Merge": [before_res["ElectrumBar"], before_res["ElementalEmber"], before_res["CosmicCharge"], before_res["time(days)"]],
        "After Merge": [after_res["ElectrumBar"], after_res["ElementalEmber"], after_res["CosmicCharge"], after_res["time(days)"]],
    })
    st.dataframe(df_compare)
