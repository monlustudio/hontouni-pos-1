import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import altair as alt

# 頁面基本設定
st.set_page_config(
    page_title="紅斗泥快閃櫃 POS 與庫存管理系統",
    page_icon="🍓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 本地資料持久化檔案路徑 (防止重新整理資料消失)
DATA_FILE = "daifuku_pos_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 初始化 Session State (優先從本地檔案讀取)
saved_data = load_data()

if 'projects' not in st.session_state:
    if saved_data and 'projects' in saved_data:
        st.session_state.projects = saved_data['projects']
    else:
        st.session_state.projects = [
            {"id": "proj_1", "name": "台中勤美快閃櫃", "status": "進行中"},
            {"id": "proj_2", "name": "台北華山快閃櫃", "status": "已完成"}
        ]

if 'flavors' not in st.session_state:
    if saved_data and 'flavors' in saved_data:
        st.session_state.flavors = saved_data['flavors']
    else:
        st.session_state.flavors = [
            {"id": "fav_1", "project_id": "proj_1", "name": "法式經典奶酥", "price": 280, "stock": 45, "color": "#8D6E63"},
            {"id": "fav_2", "project_id": "proj_1", "name": "草莓濃乳奶酥", "price": 320, "stock": 8, "color": "#E57373"},
            {"id": "fav_3", "project_id": "proj_1", "name": "金牌蜜桔奶酥", "price": 300, "stock": 30, "color": "#FFB74D"},
            {"id": "fav_4", "project_id": "proj_2", "name": "法式經典奶酥", "price": 280, "stock": 0, "color": "#8D6E63"}
        ]

if 'orders' not in st.session_state:
    if saved_data and 'orders' in saved_data:
        st.session_state.orders = saved_data['orders']
    else:
        st.session_state.orders = []

if 'pos_cart' not in st.session_state:
    st.session_state.pos_cart = {}

if 'show_confirm_dialog' not in st.session_state:
    st.session_state.show_confirm_dialog = False

if 'toast_message' not in st.session_state:
    st.session_state.toast_message = None

if 'delete_proj_target' not in st.session_state:
    st.session_state.delete_proj_target = None

if 'delete_order_target' not in st.session_state:
    st.session_state.delete_order_target = None

if 'delete_flavor_target' not in st.session_state:
    st.session_state.delete_flavor_target = None

def persist_state():
    data = {
        "projects": st.session_state.projects,
        "flavors": st.session_state.flavors,
        "orders": st.session_state.orders
    }
    save_data(data)

# 顯示持續性成功提示訊息
if st.session_state.toast_message:
    st.success(st.session_state.toast_message)
    st.session_state.toast_message = None

# ---------------------------------------------------------
# 側邊欄：專案切換與模式選擇
# ---------------------------------------------------------
st.sidebar.title("🍓 紅斗泥快閃櫃管理系統")
mode = st.sidebar.radio("選擇操作模式", ["🛒 前台 POS 點餐結帳", "📊 後台庫存與營收管理", "⚙️ 專案與口味設定"])

st.sidebar.markdown("---")

active_projects = [p for p in st.session_state.projects if p["status"] == "進行中"]
active_project_names = {p["name"]: p["id"] for p in active_projects}

if active_project_names:
    selected_proj_name = st.sidebar.selectbox("📍 目前運作中的快閃櫃", list(active_project_names.keys()))
    current_project_id = active_project_names[selected_proj_name]
else:
    st.sidebar.warning("目前沒有進行中的專案，請至設定新增或開啟專案。")
    current_project_id = None

# ---------------------------------------------------------
# Mode 1: Front-end POS (前台點餐)
# ---------------------------------------------------------
if mode == "🛒 前台 POS 點餐結帳":
    st.title("🛒 櫃台快速點餐結帳 (POS)")
    
    if not current_project_id:
        st.info("請先於左側確認或建立進行中的快閃櫃專案。")
        st.stop()
        
    st.markdown(f"**目前快閃櫃**：`{selected_proj_name}`")
    
    project_flavors = [f for f in st.session_state.flavors if f["project_id"] == current_project_id]
    
    if not project_flavors:
        st.warning("此專案尚未設定任何口味與價格，請先至後台設定新增。")
        st.stop()
        
    col_main, col_cart = st.columns([2, 1])
    
    with col_main:
        st.subheader("📦 點餐區 (一排 2 個按鈕，點擊直接加進購物車 +1)")
        
        # 強制每行 2 個按鈕配置
        cols = st.columns(2)
        for idx, f in enumerate(project_flavors):
            col_target = cols[idx % 2]
            with col_target:
                btn_color = f.get('color', '#8D6E63')
                stock_status = f"剩餘庫存: {f['stock']} 盒" if f['stock'] > 0 else "❌ 已售完"
                
                card_html = f"""
                    <div style="background-color: {btn_color}; color: white; padding: 18px; border-radius: 12px 12px 0 0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="font-size: 20px; font-weight: bold; margin-bottom: 4px;">{f['name']}</div>
                        <div style="font-size: 15px; opacity: 0.95;">NT$ {f['price']} | {stock_status}</div>
                    </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                if st.button(f"➕ 加入 【{f['name']}】", key=f"pos_click_{f['id']}_{idx}", use_container_width=True):
                    if f['stock'] > 0:
                        current_qty = st.session_state.pos_cart.get(f['id'], {}).get('qty', 0)
                        if current_qty < f['stock']:
                            st.session_state.pos_cart[f['id']] = {
                                "name": f['name'],
                                "price": f['price'],
                                "qty": current_qty + 1,
                                "max_stock": f['stock']
                            }
                            st.toast(f"✅ 已將 {f['name']} 加入購物車！", icon="🛒")
                            st.rerun()
                        else:
                            st.toast(f"⚠️ {f['name']} 庫存不足，無法再加!", icon="⚠️")
                    else:
                        st.toast(f"❌ {f['name']} 已售完!", icon="❌")
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    with col_cart:
        st.subheader("🛒 目前購物車")
        
        if st.session_state.pos_cart:
            total_amount = 0
            total_boxes = 0
            
            items_to_remove = []
            for fid, item in list(st.session_state.pos_cart.items()):
                subtotal = item['price'] * item['qty']
                total_amount += subtotal
                total_boxes += item['qty']
                
                st.markdown(f"**{item['name']}**")
                c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                with c1:
                    if st.button("➖", key=f"minus_{fid}"):
                        if item['qty'] > 1:
                            st.session_state.pos_cart[fid]['qty'] -= 1
                        else:
                            items_to_remove.append(fid)
                        st.rerun()
                with c2:
                    st.markdown(f"<div style='text-align:center; padding-top:12px; font-weight:bold; font-size:16px;'>{item['qty']}</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕", key=f"plus_{fid}"):
                        if item['qty'] < item['max_stock']:
                            st.session_state.pos_cart[fid]['qty'] += 1
                        else:
                            st.toast("已達現有庫存上限！", icon="⚠️")
                        st.rerun()
                with c4:
                    st.markdown(f"<div style='text-align:right; padding-top:12px; color:#666; font-weight:bold;'>NT$ {subtotal}</div>", unsafe_allow_html=True)
                st.markdown("---")
                
            for fid in items_to_remove:
                del st.session_state.pos_cart[fid]
                st.rerun()
                
            st.markdown(f"### 總計: NT$ {total_amount:,} ({total_boxes} 盒)")
            
            if st.button("🗑️ 清空購物車"):
                st.session_state.pos_cart = {}
                st.rerun()
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💳 結帳送出訂單", type="primary", use_container_width=True):
                st.session_state.show_confirm_dialog = True
                st.rerun()
        else:
            st.info("購物車是空的，請點擊左側彩色大按鈕點餐。")

    # 結帳確認彈出對話框
    if st.session_state.show_confirm_dialog:
        @st.dialog("📋 確認購買訂單明細")
        def confirm_dialog():
            total_amt = sum(item['price'] * item['qty'] for item in st.session_state.pos_cart.values())
            total_cnt = sum(item['qty'] for item in st.session_state.pos_cart.values())
            
            st.markdown("請向客人覆核以下購買品項與金額：")
            st.markdown("---")
            for item in st.session_state.pos_cart.values():
                st.markdown(f"- **{item['name']}** x {item['qty']} 盒 ＝ **NT$ {item['price'] * item['qty']}**")
            st.markdown("---")
            st.markdown(f"### 總金額：NT$ {total_amt:,} ({total_cnt} 盒)")
            
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✅ 確認無誤，送出訂單", type="primary", use_container_width=True):
                    cart_items_list = [{"name": item["name"], "price": item["price"], "qty": item["qty"]} for item in st.session_state.pos_cart.values()]
                    new_order = {
                        "id": f"ord_{len(st.session_state.orders)+1}",
                        "project_id": current_project_id,
                        "items": cart_items_list,
                        "total": total_amt,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.orders.append(new_order)
                    
                    for fid, item in st.session_state.pos_cart.items():
                        for f in st.session_state.flavors:
                            if f["id"] == fid:
                                f["stock"] -= item["qty"]
                                
                    st.session_state.pos_cart = {}
                    st.session_state.show_confirm_dialog = False
                    persist_state()
                    st.session_state.toast_message = "🎉 訂單已成功送出！庫存已同步扣除。"
                    st.balloons()
                    st.rerun()
            with col_no:
                if st.button("❌ 返回修改", use_container_width=True):
                    st.session_state.show_confirm_dialog = False
                    st.rerun()
                    
        confirm_dialog()

    st.markdown("---")
    st.subheader("📈 今日櫃位即時業績總覽")
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in st.session_state.orders if o["project_id"] == current_project_id and o["time"].startswith(today_str)]
    
    today_revenue = sum(o["total"] for o in today_orders)
    today_boxes_sold = sum(sum(item["qty"] for item in o["items"]) for o in today_orders)
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("今日總營業額", f"NT$ {today_revenue:,}")
    with m2:
        st.metric("今日銷售總盒數", f"{today_boxes_sold} 盒")
    with m3:
        st.metric("今日成交訂單數", f"{len(today_orders)} 筆")

# ---------------------------------------------------------
# Mode 2: Back-end Analytics & Restock (後台管理)
# ---------------------------------------------------------
elif mode == "📊 後台庫存與營收管理":
    st.title("📊 後台管理：庫存調整、圖表與營收分析")
    
    if not current_project_id:
        st.info("請先選擇專案。")
        st.stop()
        
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理與快速加減", "📉 橫向庫存圖表與見底警示", "💰 歷史銷售與營業額"])
    
    project_flavors = [f for f in st.session_state.flavors if f["project_id"] == current_project_id]
    
    with tab1:
        st.subheader("📥 批次補貨登錄")
        with st.form("restock_form"):
            flavor_options = {f["name"]: f["id"] for f in project_flavors}
            selected_flavor_name = st.selectbox("選擇口味進行批次補貨", list(flavor_options.keys()) if flavor_options else [])
            restock_qty = st.number_input("補貨數量 (盒)", min_value=1, value=20, step=1)
            
            submit_restock = st.form_submit_button("確認批次補貨")
            if submit_restock and flavor_options:
                fid = flavor_options[selected_flavor_name]
                for item in st.session_state.flavors:
                    if item["id"] == fid:
                        item["stock"] += restock_qty
                persist_state()
                st.session_state.toast_message = f"✅ 成功為【{selected_flavor_name}】補貨 {restock_qty} 盒！"
                st.rerun()
                
        st.markdown("---")
        st.subheader("📦 庫存即時調整 (支援單獨加減數量)")
        
        if project_flavors:
            for idx, f in enumerate(project_flavors):
                c_name, c_stock, c_minus, c_plus = st.columns([3, 2, 1, 1])
                with c_name:
                    st.markdown(f"**{f['name']}** (售價: NT$ {f['price']})")
                with c_stock:
                    stock_color = "red" if f['stock'] <= 5 else ("orange" if f['stock'] <= 10 else "green")
                    st.markdown(f"目前庫存: <span style='color:{stock_color}; font-weight:bold; font-size:18px;'>{f['stock']} 盒</span>", unsafe_allow_html=True)
                with c_minus:
                    if st.button("➖ 減 1", key=f"backend_minus_{f['id']}_{idx}"):
                        for item in st.session_state.flavors:
                            if item["id"] == f["id"]:
                                item["stock"] = max(0, item["stock"] - 1)
                        persist_state()
                        st.toast(f"已將 {f['name']} 庫存減 1", icon="ℹ️")
                        st.rerun()
                with c_plus:
                    if st.button("➕ 加 1", key=f"backend_plus_{f['id']}_{idx}"):
                        for item in st.session_state.flavors:
                            if item["id"] == f["id"]:
                                item["stock"] += 1
                        persist_state()
                        st.toast(f"已將 {f['name']} 庫存加 1", icon="ℹ️")
                        st.rerun()
                st.markdown("---")
        else:
            st.info("尚無口味資料。")
            
    with tab2:
        st.subheader("📉 各口味橫向庫存量與見底警示")
        if project_flavors:
            df_chart = pd.DataFrame(project_flavors)
            
            chart = alt.Chart(df_chart).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                x=alt.X('stock:Q', title='目前庫存 (盒)'),
                y=alt.Y('name:N', sort='-x', title='口味名稱'),
                color=alt.Color('color:N', scale=None, legend=None)
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)
            
            st.markdown("### ⚠️ 庫存見底警示 (< 10 盒)")
            low_stock_items = [f for f in project_flavors if f["stock"] <= 10]
            if low_stock_items:
                for item in low_stock_items:
                    st.error(f"🔴 【{item['name']}】目前庫存僅剩 **{item['stock']} 盒**，請儘速補貨！")
            else:
                st.success("🟢 目前所有口味庫存充足。")
        else:
            st.info("尚無口味資料。")
            
    with tab3:
        st.subheader("💰 歷史銷售與營業額 (支援訂單刪除與密碼確認)")
        project_orders = [o for o in st.session_state.orders if o["project_id"] == current_project_id]
        
        if project_orders:
            for o in project_orders:
                items_str = ", ".join([f"{i['name']}x{i['qty']}" for i in o['items']])
                
                c_info, c_btn = st.columns([4, 1])
                with c_info:
                    st.markdown(f"**訂單編號**: `{o['id']}` | **時間**: {o['time']} | **明細**: {items_str} | **總金額**: **NT$ {o['total']:,}**")
                with c_btn:
                    if st.button("🗑️ 刪除訂單", key=f"del_ord_btn_{o['id']}"):
                        st.session_state.delete_order_target = o['id']
                        st.rerun()
                
                # 訂單刪除第二層確認框
                if st.session_state.delete_order_target == o['id']:
                    with st.container():
                        st.warning(f"⚠️ 您正在嘗試刪除訂單 **【{o['id']}】**（金額 NT$ {o['total']:,}）。刪除後該筆訂單所扣除的庫存將會自動加回！")
                        with st.form(f"delete_order_form_{o['id']}"):
                            ord_pwd = st.text_input("請輸入管理員密碼確認刪除 (8888)", type="password", key=f"opwd_{o['id']}")
                            oc1, oc2 = st.columns(2)
                            with oc1:
                                confirm_del_ord = st.form_submit_button("🚨 確認刪除訂單", type="primary")
                                if confirm_del_ord:
                                    if ord_pwd == "8888":
                                        # 將該訂單品項的庫存加回
                                        for item in o['items']:
                                            for f in st.session_state.flavors:
                                                if f['name'] == item['name'] and f['project_id'] == o['project_id']:
                                                    f['stock'] += item['qty']
                                        
                                        st.session_state.orders = [item for item in st.session_state.orders if item["id"] != o["id"]]
                                        st.session_state.delete_order_target = None
                                        persist_state()
                                        st.session_state.toast_message = f"🗑️ 已成功刪除訂單 {o['id']} 並自動同步恢復庫存！"
                                        st.rerun()
                                    else:
                                        st.error("❌ 密碼錯誤！刪除失敗。")
                            with oc2:
                                cancel_del_ord = st.form_submit_button("❌ 取消")
                                if cancel_del_ord:
                                    st.session_state.delete_order_target = None
                                    st.rerun()
                st.markdown("---")
            
            # 每日營業額趨勢圖
            order_summary = []
            for o in project_orders:
                items_str = ", ".join([f"{i['name']}x{i['qty']}" for i in o['items']])
                order_summary.append({
                    "銷售時間": o["time"],
                    "總金額 (NT$)": o["total"]
                })
            df_orders = pd.DataFrame(order_summary)
            df_orders["日期"] = pd.to_datetime(df_orders["銷售時間"]).dt.date
            daily_rev = df_orders.groupby("日期")["總金額 (NT$)"].sum().reset_index()
            st.markdown("### 📅 每日營業額趨勢")
            st.line_chart(daily_rev.set_index("日期"))
        else:
            st.info("目前尚無銷售記錄。")

# ---------------------------------------------------------
# Mode 3: Project & Flavor Settings (專案與口味設定)
# ---------------------------------------------------------
elif mode == "⚙️ 專案與口味設定":
    st.title("⚙️ 快閃櫃專案與口味設定")
    
    tab_p, tab_f = st.tabs(["📁 快閃櫃專案管理", "🏷️ 口味與定價管理 (新增/編輯/刪除)"])
    
    with tab_p:
        st.subheader("新增快閃櫃專案 (需輸入密碼 8888)")
        with st.form("new_project_form"):
            new_proj_name = st.text_input("專案名稱 (例如：高雄漢神巨蛋快閃櫃)")
            new_proj_pwd = st.text_input("管理員確認密碼", type="password", placeholder="請輸入 8888")
            create_proj_btn = st.form_submit_button("建立新專案")
            
            if create_proj_btn:
                if not new_proj_name:
                    st.error("❌ 請輸入專案名稱！")
                elif new_proj_pwd != "8888":
                    st.error("❌ 密碼錯誤！新增專案需輸入正確密碼 (8888)。")
                else:
                    new_id = f"proj_{len(st.session_state.projects)+1}"
                    st.session_state.projects.append({"id": new_id, "name": new_proj_name, "status": "進行中"})
                    persist_state()
                    st.session_state.toast_message = f"✅ 成功建立專案：{new_proj_name}"
                    st.rerun()
                
        st.markdown("---")
        st.subheader("現有專案管理與狀態切換")
        
        if st.session_state.projects:
            for p in list(st.session_state.projects):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.markdown(f"**{p['name']}**")
                with col2:
                    st.markdown(f"狀態: `{p['status']}`")
                with col3:
                    new_status = st.selectbox(
                        "變更狀態", 
                        ["進行中", "已完成"], 
                        index=0 if p["status"]=="進行中" else 1,
                        key=f"status_{p['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != p["status"]:
                        p["status"] = new_status
                        persist_state()
                        st.rerun()
                with col4:
                    if st.button("🗑️ 刪除專案", key=f"del_proj_btn_{p['id']}"):
                        st.session_state.delete_proj_target = p['id']
                        st.rerun()
                
                if st.session_state.delete_proj_target == p['id']:
                    with st.container():
                        st.warning(f"⚠️ 您正在嘗試刪除專案 **【{p['name']}】**。此操作將一併刪除該專案所有口味與歷史訂單且無法復原！")
                        with st.form(f"delete_verify_form_{p['id']}"):
                            del_pwd = st.text_input("請輸入管理員密碼確認刪除 (8888)", type="password", key=f"dpwd_{p['id']}")
                            c_confirm, c_cancel = st.columns(2)
                            with c_confirm:
                                sub_del = st.form_submit_button("🚨 確認永久刪除", type="primary")
                                if sub_del:
                                    if del_pwd == "8888":
                                        st.session_state.projects = [item for item in st.session_state.projects if item["id"] != p["id"]]
                                        st.session_state.flavors = [item for item in st.session_state.flavors if item["project_id"] != p["id"]]
                                        st.session_state.orders = [item for item in st.session_state.orders if item["project_id"] != p["id"]]
                                        st.session_state.delete_proj_target = None
                                        persist_state()
                                        st.session_state.toast_message = f"🗑️ 已成功永久刪除專案：{p['name']}"
                                        st.rerun()
                                    else:
                                        st.error("❌ 密碼錯誤！刪除失敗。")
                            with c_cancel:
                                cancel_del = st.form_submit_button("❌ 取消")
                                if cancel_del:
                                    st.session_state.delete_proj_target = None
                                    st.rerun()
                st.markdown("---")
        else:
            st.info("目前尚無任何專案。")
                    
    with tab_f:
        st.subheader("➕ 新增口味 (需輸入密碼 8888)")
        all_proj_options = {p["name"]: p["id"] for p in st.session_state.projects}
        
        if all_proj_options:
            with st.form("new_flavor_form"):
                target_proj_name = st.selectbox("選擇專案", list(all_proj_options.keys()))
                target_proj_id = all_proj_options[target_proj_name]
                
                flavor_name = st.text_input("口味名稱 (例如：法式經典奶酥)")
                flavor_price = st.number_input("單價 (NT$)", min_value=0, value=280, step=10)
                initial_stock = st.number_input("初始庫存數量 (盒)", min_value=0, value=50, step=5)
                flavor_color = st.color_picker("按鈕與圖表顯示顏色", "#8D6E63")
                new_fav_pwd = st.text_input("管理員確認密碼", type="password", placeholder="請輸入 8888")
                
                add_flavor_btn = st.form_submit_button("確認新增口味")
                if add_flavor_btn:
                    if not flavor_name:
                        st.error("❌ 請輸入口味名稱！")
                    elif new_fav_pwd != "8888":
                        st.error("❌ 密碼錯誤！新增口味需輸入正確密碼 (8888)。")
                    else:
                        new_fav_id = f"fav_{len(st.session_state.flavors)+1}"
                        st.session_state.flavors.append({
                            "id": new_fav_id,
                            "project_id": target_proj_id,
                            "name": flavor_name,
                            "price": flavor_price,
                            "stock": initial_stock,
                            "color": flavor_color
                        })
                        persist_state()
                        st.session_state.toast_message = f"✅ 成功為【{target_proj_name}】新增口味：{flavor_name}！"
                        st.rerun()
                    
            st.markdown("---")
            st.subheader("✏️ 現有口味清單 (支援編輯與第二層密碼刪除)")
            
            if st.session_state.flavors:
                for idx, f in enumerate(list(st.session_state.flavors)):
                    proj_name = next((p["name"] for p in st.session_state.projects if p["id"] == f["project_id"]), "未知專案")
                    
                    with st.expander(f"📦 [{proj_name}] {f['name']} (售價: NT${f['price']} | 庫存: {f['stock']}盒)"):
                        with st.form(f"edit_flavor_form_{f['id']}_{idx}"):
                            edit_name = st.text_input("修改口味名稱", value=f['name'], key=f"ename_{f['id']}_{idx}")
                            edit_price = st.number_input("修改單價 (NT$)", min_value=1, value=f['price'], step=10, key=f"eprice_{f['id']}_{idx}")
                            edit_color = st.color_picker("修改按鈕顏色", value=f.get('color', '#8D6E63'), key=f"ecolor_{f['id']}_{idx}")
                            
                            c_save, c_del = st.columns(2)
                            with c_save:
                                save_btn = st.form_submit_button("💾 儲存變更")
                                if save_btn:
                                    f['name'] = edit_name
                                    f['price'] = edit_price
                                    f['color'] = edit_color
                                    persist_state()
                                    st.session_state.toast_message = f"✅ 成功更新【{edit_name}】資訊！"
                                    st.rerun()
                            with c_del:
                                trigger_del_fav = st.form_submit_button("🗑️ 刪除此口味")
                                if trigger_del_fav:
                                    st.session_state.delete_flavor_target = f['id']
                                    st.rerun()
                        
                        # 口味刪除第二層密碼確認框
                        if st.session_state.delete_flavor_target == f['id']:
                            with st.container():
                                st.warning(f"⚠️ 您正在嘗試刪除口味 **【{f['name']}】**。此操作將一併移除該口味設定與購物車快取！")
                                with st.form(f"delete_flavor_verify_form_{f['id']}"):
                                    fav_del_pwd = st.text_input("請輸入管理員密碼確認刪除 (8888)", type="password", key=f"fpwd_{f['id']}")
                                    fc1, fc2 = st.columns(2)
                                    with fc1:
                                        confirm_del_fav = st.form_submit_button("🚨 確認永久刪除", type="primary")
                                        if confirm_del_fav:
                                            if fav_del_pwd == "8888":
                                                st.session_state.flavors = [item for item in st.session_state.flavors if item["id"] != f["id"]]
                                                if f['id'] in st.session_state.pos_cart:
                                                    del st.session_state.pos_cart[f['id']]
                                                st.session_state.delete_flavor_target = None
                                                persist_state()
                                                st.session_state.toast_message = f"🗑️ 已成功刪除口味：{f['name']}"
                                                st.rerun()
                                            else:
                                                st.error("❌ 密碼錯誤！刪除失敗。")
                                    with fc2:
                                        cancel_del_fav = st.form_submit_button("❌ 取消")
                                        if cancel_del_fav:
                                            st.session_state.delete_flavor_target = None
                                            st.rerun()
            else:
                st.info("目前尚無任何口味資料。")
        else:
            st.info("請先至左側建立專案。")
