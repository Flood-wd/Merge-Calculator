import streamlit as st
import pandas as pd

# --- データ読み込み関数 ---
@st.cache_data
def load_data():
    df_cosmic_oculus = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20Cosmic_Oculus.csv")
    df_crystal_pylon = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20Crystal_Pylon.csv")
    df_volt = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20Volt.csv")
    df_archmage = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20ArchMage.csv")
    df_flak = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20Flak.csv")
    df_mage_lightning = pd.read_csv("https://raw.githubusercontent.com/Flood-wd/Merge-Calculator/main/Data_.xlsx%20-%20Mage_lightning.csv")
    return {
        "Cosmic/Oculus": df_cosmic_oculus,
        "Crystal/Pylon": df_crystal_pylon,
        "Volt": df_volt,
        "ArchMage": df_archmage,
        "Flak": df_flak,
        "Mage/Lightning": df_mage_lightning
    }

tower_data = load_data()

# --- UI表示 ---
st.title("タワー統合計算")

col1, col2 = st.columns([3, 1])
with col1:
    target_tower_type = st.selectbox("対象タワー", list(tower_data.keys()))
with col2:
    base_level = st.number_input("初期Lv", min_value=10, max_value=225, step=1)

st.subheader("素材タワーの入力")
num_materials = st.number_input("素材タワーの数", min_value=1, max_value=20, step=1)

for i in range(num_materials):
    cols = st.columns([3, 1])
    with cols[0]:
        st.selectbox(f"タワー{i+1}", list(tower_data.keys()), key=f"type_{i}")
    with cols[1]:
        st.number_input(f"タワー{i+1}のLv", min_value=10, max_value=225, step=1, key=f"level_{i}")

# 実行ボタン
if st.button("計算実行"):
    result = calculate_merge_result(tower_data, target_tower_type, base_level, num_materials)
    st.markdown(f"### 統合後のレベル: **Lv.{result['new_level']}**")
    st.markdown(f"#### リソース活用効率: {result['efficiency']}％")
    
    st.subheader("リソース比較")
    st.dataframe(result["resource_df"])




def calculate_merge_result(tower_data, target_tower_type, base_level, num_materials):
    df_target = tower_data[target_tower_type]
    base_row = df_target[df_target['level'] == base_level]
    if base_row.empty:
        raise ValueError("無効なベースタワーレベルです")

    base_rubble = base_row['cumulative_rubble'].values[0]
    base_xp = base_row['XP_cumulative'].values[0]

    total_material_rubble = 0
    total_material_xp = 0
    resource_costs = {
        "electrumBar": 0,
        "elementalEmber": 0,
        "cosmicCharge": 0,
        "lumber": 0,
        "time": 0
    }

    for i in range(num_materials):
        mat_type = st.session_state[f"type_{i}"]
        mat_level = st.session_state[f"level_{i}"]
        df_mat = tower_data[mat_type]
        row = df_mat[df_mat['level'] == mat_level]
        if not row.empty:
            total_material_rubble += row['cumulative_rubble'].values[0]
            total_material_xp += row['XP_cumulative'].values[0]
            resource_costs["electrumBar"] += row['electrumBar_cumulative'].values[0]
            resource_costs["elementalEmber"] += row['elementalEmber_cumulative'].values[0]
            resource_costs["cosmicCharge"] += row['cosmicCharge_cumulative'].values[0]
            resource_costs["lumber"] += row['lumber_cumulative'].values[0]
            resource_costs["time"] += row['time_cumulative(days)'].values[0]

    effective_rubble = max(total_material_rubble * 0.95 - 200, 0)
    total_available_rubble = base_rubble + effective_rubble
    total_available_xp = base_xp + total_material_xp

    possible_levels = df_target[
        (df_target['cumulative_rubble'] <= total_available_rubble) &
        (df_target['XP_cumulative'] <= total_available_xp)
    ]
    new_level = base_level if possible_levels.empty else possible_levels['level'].max()

    final_row = df_target[df_target['level'] == new_level]
    new_rubble = final_row['cumulative_rubble'].values[0]
    new_xp = final_row['XP_cumulative'].values[0]

    rubble_gain = new_rubble - base_rubble
    efficiency = round((rubble_gain / total_material_rubble) * 100, 1) if total_material_rubble > 0 else 0

    levelup_costs = {
        "electrumBar": final_row['electrumBar_cumulative'].values[0] - base_row['electrumBar_cumulative'].values[0],
        "elementalEmber": final_row['elementalEmber_cumulative'].values[0] - base_row['elementalEmber_cumulative'].values[0],
        "cosmicCharge": final_row['cosmicCharge_cumulative'].values[0] - base_row['cosmicCharge_cumulative'].values[0],
        "lumber": final_row['lumber_cumulative'].values[0] - base_row['lumber_cumulative'].values[0],
        "time": final_row['time_cumulative(days)'].values[0] - base_row['time_cumulative(days)'].values[0],
    }

    resource_df = pd.DataFrame({
        "リソース": ["ElectrumBar", "ElementalEmber", "CosmicCharge", "Lumber", "時間（日）"],
        "レベルアップ": [
            levelup_costs["electrumBar"],
            levelup_costs["elementalEmber"],
            levelup_costs["cosmicCharge"],
            levelup_costs["lumber"],
            levelup_costs["time"]
        ],
        "統合（素材合計）": [
            resource_costs["electrumBar"],
            resource_costs["elementalEmber"],
            resource_costs["cosmicCharge"],
            resource_costs["lumber"],
            resource_costs["time"]
        ]
    })

    return {
        "new_level": new_level,
        "efficiency": efficiency,
        "resource_df": resource_df
    }