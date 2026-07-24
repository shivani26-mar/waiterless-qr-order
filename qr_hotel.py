
import streamlit as st
# from pyngrok import ngrok
import qrcode
import sqlite3
from io import BytesIO
import time
from streamlit import fragment

# Streamlit Secrets se automatic credentials uthane ke liye
url = "https://supabase.com/dashboard/project/rrrfxgjapvdefyrblkja/settings/api-keys"
key = "sb_publishable_-eJ3jHavs4HW55E5iODB1g_nbE9J3Hr"
from supabase import create_client
supabase = create_client(url, key)
internet_url = "https://smart-waiterless-qr-hotel.streamlit.app/" 

# 1. ⚙️ डेटाबेस (तिजोरी) सेटअप
def init_db():
    conn = sqlite3.connect("hotel_orders.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_no TEXT,
            items TEXT,
            total INTEGER,
            status TEXT DEFAULT 'Ordered'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. 🍔 वेबसाइट सेटिंग्स
st.set_page_config(page_title="Delicious Hotel", page_icon="🍔", layout="wide")

query_params = st.query_params
table_no = query_params.get("table", "1")

if "cart" not in st.session_state:
    st.session_state.cart = {}


    # 🍱 होटल का प्रोफेशनल कैटगरी वाइज मेनू (Half/Full प्लेट के साथ)
menu_items = {
    "शाकाहारी सब्ज़ियाँ (Vegetables)": {
        "शाही पनीर (Shahi Paneer)": {
            "is_plated": True, # यह कंप्यूटर को बताएगा कि इसके दो रेट हैं
            "Half": 140, "Full": 240,
            "image": "paneer.jpg", "desc": "ताजा पनीर और काजू की मखमली ग्रेवी के साथ।"
        },
        "मिक्स वेज (Mix Veg)": {
            "is_plated": True,
            "Half": 100, "Full": 180,
            "image": "mix veg.jpeg", "desc": "ताज़ा मौसमी सब्ज़ियों का स्वादिष्ट मिश्रण।"
        }
    },
    "चावल के व्यंजन (Rice Dishes)": {
        "वेज पुलाव (Veg Pulao)": {
            "is_plated": True,
            "Half": 90, "Full": 150,
            "image": "veg pulao.jpg", "desc": "बासमती चावल ताज़ा मटर और मसालों के साथ।"
        },
        "जीरा राइस (Jeera Rice)": {
            "is_plated": True,
            "Half": 60, "Full": 100,
            "image": "jeera rice.jpg", "desc": "शुद्ध घी और भूने जीरे से महकते बासमती चावल।"
        }
    },
    "रोटी और नान (Breads)": {
        "बटर रोटी (Butter Roti)": {"price": 25, "image": "roti.jpg", "desc": "गेहूं की तंदूरी रोटी, शुद्ध अमूल बटर के साथ।"},
        "बटर नान (Butter Naan)": {"price": 50, "image": "butter naan.jpg", "desc": "मैदे की मखमली तंदूरी नान मक्खन के साथ।"}
    },
    "कुछ मीठा (Desserts)": {
        "गुलाब जामुन (Gulab Jamun)": {"price": 60, "image": "gulab jamun.jpg", "desc": "चाशनी में डूबे दो पीस गुलाब जामुन।"}
    }
}

# 🛠️ 3. होटल कंट्रोल पैनल (साइडबार)
st.sidebar.header("⚙️ होटल कंट्रोल पैनल")
view_mode = st.sidebar.radio("स्क्रीन बदलें:", ["Customer Menu (ग्राहक)", "Kitchen Dashboard (किचन/मैनेजर)"])

selected_table = st.sidebar.selectbox("QR कोड जनरेट करें:", ["1", "2", "3", "4", "5"])
network_ip = "10.86.61.100"  # आपका फिक्स असली आईपी एड्रेस

if st.sidebar.button(f"टेबल {selected_table} का QR कोड बनाएं 🖨️"):
    scan_url = f"{internet_url}/?table={selected_table}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(scan_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    st.sidebar.image(buf.getvalue(), caption=f"Table {selected_table}", width=200)
@st. fragment(run_every=5)
def auto_refresh_kitchen_dashboard():
    current_time = time.strftime('%I:%M:%S %p')
    st.caption(f"🔄 Kitchen Live Sync: {current_time}")


# --- 🚀 स्क्रीन A: ग्राहक का मेनू कार्ड और बिलिंग कार्ट ---
if view_mode == "Customer Menu (ग्राहक)":
    st.title(f"🍔 डिजिटल रेस्टोरेंट - टेबल नंबर {table_no}")
    st.subheader("बिना कतार के, सीधे अपने मोबाइल से स्वादिष्ट खाना ऑर्डर करें!")
    st.write("---")
    
    col1, col2 = st.columns(2)


    with col1:
         st.header("🍱 आज का स्पेशल मेनू")
    for category, items in menu_items.items():
        st.markdown(f"### 📌 {category}")
        for item_name, info in items.items():
            with st.container():
                img_col, text_col = st.columns(2)
                with img_col:
                    st.image(info["image"], use_container_width=True)
                with text_col:
                    # 1️⃣ अगर डिश हाफ/फुल (प्लेट) वाली है (शाही पनीर, मिक्स वेज आदि)
                    if info.get("is_plated", False):
                        plate_type = st.selectbox(f"साइज चुनें:", ["Full", "Half"], key=f"size_{item_name}")
                        current_price = info[plate_type]
                        st.subheader(f"{item_name} ({plate_type}) - ₹{current_price}")
                        final_item_name = f"{item_name} [{plate_type}]"
                        qty_to_add = 1 # प्लेट वाले आइटम एक बार में 1 ही जुड़ेंगे
                        
                    # 2️⃣ अगर डिश सिंगल आइटम वाली है (रोटी, नान, गुलाब जामुन)
                    else:
                        current_price = info["price"]
                        st.subheader(f"{item_name} - ₹{current_price}")
                        final_item_name = item_name
                        # ⚡ जादुई सुधार: यहाँ 1 से 5 तक की संख्या चुनने का ड्रॉपडाउन बॉक्स खोलना
                        qty_to_add = st.selectbox(f"संख्या चुनें (Quantity):", [1, 2, 3, 4, 5], key=f"qty_{item_name}")
                        
                    st.write(info["desc"])
                    
                    # 🛒 कार्ट में आइटम और उसकी चुनी हुई संख्या को जोड़ना
                    if st.button(f"Add ➕", key=final_item_name):
                        if final_item_name in st.session_state.cart:
                            # ग्राहक ने जो संख्या (1 से 5) चुनी है, उसे सीधे कार्ट में प्लस करना
                            st.session_state.cart[final_item_name] += qty_to_add
                        else:
                            st.session_state.cart[final_item_name] = qty_to_add
                        st.toast(f"{final_item_name} ({qty_to_add} पीस) कार्ट में जुड़ गया! 🛒")
                st.write("---")


    with col2:
        st.header("🛒 आपका ऑर्डर (Bill)")
        total_bill = 0
        
        if not st.session_state.cart:
            st.write("आपकी थाली अभी खाली है। बाईं तरफ से कुछ स्वादिष्ट ऐड करें! 🍽️")
        else:
             order_summary_text = ""
             for item, qty in st.session_state.cart.items():
             # नाम में से असली डिश और प्लेट टाइप अलग करना
                 price = 0
                 base_name = item.split(" [")[0]
        
                 for cat, items in menu_items.items():
                     if base_name in items:
                         info = items[base_name]
                         if info.get("is_plated", False):
                            plate_type = "Half" if "[Half]" in item else "Full"
                            price = info[plate_type]
                         else:
                             price = info["price"]
        
             cost = price * qty
             total_bill += cost
             st.write(f"**{item}** x {qty} = ₹{cost}")
             order_summary_text += f"{item}({qty}), "

            
             st.write("---")
             st.subheader(f"कुल बिल (Total): ₹{total_bill}")
            
             if st.button("कार्ट साफ़ करें 🗑️"):
                st.session_state.cart = {}
                st.rerun()
                
             st.write("---")
            
            # 📌 बटन 1: केवल ऑर्डर को किचन में भेजने के लिए (स्टेटस = 'Ordered')
             if st.button("Please Order 🍽️", key="only_order_btn"):
                
                        order_data = {
                            "table_no": str(selected_table), 
                            "items": str(order_summary_text), 
                            "total": int(total_bill), 
                            "status": "Ordered"
                        }
                        supabase.table("orders").insert(order_data).execute()
                        st.success(f"🎉 ऑर्डर टेबल नंबर {table_no} से सीधे किचन में भेज दिया गया है! शेफ आपका खाना तैयार कर रहे हैं|")
                
             st.write("---")
            
            # 📌 बटन 2: खाना खाने के बाद पेमेंट करने के लिए (यह स्टेटस को 'Paid' कर देगा)
             if st.button("Proceed to Pay (Final Bill) 💳", key="final_pay_btn"):
                # Supabase cloud database se 'Paid' status wale orders ko delete karna
                supabase.table("orders").delete().eq("status", "Paid").execute()
                HOTEL_UPI_ID = "yourname@ybl" 
                upi_url = f"upi://pay?pa={HOTEL_UPI_ID}&pn=Digital_Hotel&am={total_bill}&cu=INR"
                pay_qr = qrcode.make(upi_url)
                pay_buf = BytesIO()
                pay_qr.save(pay_buf, format="PNG")
                st.info(f"टेबल नंबर {table_no} का कुल फाइनल बिल ₹{total_bill} है।")
                st.image(pay_buf.getvalue(), caption="फाइनल पेमेंट क्यूआर कोड", width=250)
                st.session_state.cart = {}

# --- 🚀 स्क्रीन B: किचन/मैनेजर लाइव डैशबोर्ड ---
else:
    auto_refresh_kitchen_dashboard()
    st.title("👨‍🍳 किचन लाइव ऑर्डर डैशबोर्ड")
    
# 1. Cloud Database (Supabase) se keval 'Ordered' status wale orders nikalna
    # response = supabase.table("orders").select("*").eq("status", "Ordered").order("id", desc=True).execute()
    response = supabase.table("orders").select("id, table_no, items, total, status").eq("status", "Ordered").order("id", desc=True).execute()

    active_orders = response.data if response.data else []
    
    # 2. [AUTO-SUM CONCEPT]: Paid orders ka Total (SUM) nikalne ke liye cloud call
    total_response = supabase.table("orders").select("total").eq("status", "Paid").execute()
    grand_total = sum(row['total'] for row in total_response.data) if total_response.data else 0
    # --- 💰 मैनेजर के लिए लाइव गल्ला काउंटर ---
    st.write("---")
    metric_col1, metric_col2, clear_sales_col = st.columns(3)
    
    with metric_col1:
        st.metric(label="👨‍🍳 किचन में एक्टिव ऑर्डर्स", value=len(active_orders))
        
    with metric_col2:
        st.metric(label="💰 आज का शुद्ध गल्ला (Paid Amount Only)", value=f"₹{grand_total:,}")
        
    with clear_sales_col:
        st.write("##") 
        if st.button("🗑️ गल्ला साफ़ करें", type="primary", use_container_width=True):
            st.session_state.confirm_sales_delete = True

    # 🚨 गल्ला साफ़ करने का सुरक्षा चेतावनी बॉक्स
    if st.session_state.get("confirm_sales_delete", False):
        st.warning("⚠️ क्या आप सच में अपनी डायरी में नोट करने के बाद कुल कमाई को साफ़ (0) करना चाहते हैं?")
        conf_c1, conf_c2 = st.columns(2)
        with conf_c1:
            if st.button("हाँ, कमाई साफ़ करें 🚨", key="confirm_sales_yes", type="primary"):
                # Supabase cloud database se 'Paid' status wale orders ko delete karna
                supabase.table("orders").delete().eq("status", "Paid").execute()
                st.session_state.confirm_sales_delete = False
                st.success("🧹 कुल कमाई का डेटा सफलतापूर्वक साफ़ कर दिया गया है!")
                time.sleep(1)
                st.rerun()
        with conf_c2:
            if st.button("नहीं, कैंसिल करें ❌", key="confirm_sales_no"):
                st.session_state.confirm_sales_delete = False
                st.rerun()

    st.write("---")

    if st.button("🔄 ऑर्डर लिस्ट रिफ्रेश करें", use_container_width=True):
        st.rerun()
                
    st.write("---")
    
    # एक्टिव ऑर्डर्स को दिखाना
    if not active_orders:
        st.info("अभी किचन में कोई पेंडिंग ऑर्डर नहीं है। शेफ आराम कर रहे हैं! 🍹")
    else:
        for order in active_orders:
            order_id, t_no, food_items, bill_amount = order
            
            with st.expander(f"⚠️ टेबल नंबर {t_no} से नया ऑर्डर! (ID: {order_id})", expanded=True):
                st.write(f"🍛 **ऑर्डर किया गया खाना:** {food_items}")
                st.subheader(f"💰 संभावित बिल (Unpaid): ₹{bill_amount}")
                st.caption("नोट: यह राशि पेमेंट होने के बाद ही मुख्य टोटल गल्ले में जुड़ेगी।")






































































































































































































































































































































































































































































































































