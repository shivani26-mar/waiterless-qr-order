

# 🔐 Manager Login
def manager_login():

    if st.session_state.get("manager_authenticated", False):
        return True

    st.subheader("🔐 Manager Login")

    email = st.text_input("Manager Email")
    password = st.text_input(
        "Manager Password",
        type="password"
    )

    if st.button("Login"):

        correct_email = st.secrets["MANAGER_EMAIL"]
        correct_password = st.secrets["MANAGER_PASSWORD"]

        if email == correct_email and password == correct_password:

            st.session_state.manager_authenticated = True
            st.success("✅ Login successful!")
            st.rerun()

        else:
            st.error("❌ Incorrect email or password")

    return False


import streamlit.components.v1 as components
import streamlit as st
import razorpay

RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
RAZORPAY_KEY_SECRET = st.secrets["RAZORPAY_KEY_SECRET"]

razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

def create_razorpay_order(amount):
    amount_paise = int(amount * 100)

    razorpay_order = razorpay_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    return razorpay_order

def add_daily_sale(amount):
    from datetime import date

    today = date.today().isoformat()

    existing = (
        supabase
        .table("daily_sales")
        .select("id,total_amount")
        .eq("sale_date", today)
        .execute()
    )

    if existing.data:
        sale_id = existing.data[0]["id"]
        old_total = float(existing.data[0]["total_amount"])
        new_total = old_total + float(amount)

        supabase.table("daily_sales").update({
            "total_amount": new_total
        }).eq("id", sale_id).execute()

    else:
        supabase.table("daily_sales").insert({
            "sale_date": today,
            "total_amount": float(amount)
        }).execute()








# from pyngrok import ngrok
import qrcode
import sqlite3
from io import BytesIO
import time
from streamlit import fragment
import json
import html
import csv
import io
table_no = st.query_params.get("table", "1")

# Streamlit Secrets se automatic credentials uthane ke liye 
url = "https://rrrfxgjapvdefyrblkja.supabase.co"
# Move Supabase key to Streamlit Secrets
key = st.secrets["SUPABASE_KEY"]
from supabase import create_client
supabase = create_client(url, key)
admin_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
supabase_admin = create_client(url, admin_key)
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
view_mode = st.sidebar.radio(
    "स्क्रीन बदलें:",
    [
        "Customer Menu (ग्राहक)",
        "Kitchen Dashboard (किचन/मैनेजर)",
        "Admin Dashboard (Owner)"
    ]
)





# view_mode = st.sidebar.radio("स्क्रीन बदलें:", ["Customer Menu (ग्राहक)", "Kitchen Dashboard (किचन/मैनेजर)"])

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
    # st.title(f"🍔 डिजिटल रेस्टोरेंट - टेबल नंबर {table_no}")
    st.title("🍽️ Welcome to Shreeji Restaurant")
    st.subheader("हमारे रेस्टोरेंट में आपका स्वागत है ❤️")
    st.title(f"टेबल नंबर {table_no}")

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
             order_summary_text += f"{item} | Quantity: {qty} | Price: ₹{price} each | Total: ₹{cost}\n"


            
             st.write("---")
             st.subheader(f"कुल बिल (Total): ₹{total_bill}")
            
             if st.button("कार्ट साफ़ करें 🗑️"):
                st.session_state.cart = {}
                st.rerun()
                
             st.write("---")             
            # 📌 बटन 1: केवल ऑर्डर को किचन में भेजने के लिए (स्टेटस = 'Ordered')
             if st.button("Please order 👨‍🍳", key="only_order_btn_new"):
                 order_data = {
                     "table_no": str(table_no),
                     "items": str(order_summary_text),
                     "total": int(total_bill),
                     "status": "ordered"
                 }
                 response = supabase.table("orders").insert(order_data).execute()
                 if response.data:
                     order_id = response.data[0]["id"]
                     st.session_state["current_order_id"] = order_id

                 
                 st.success(f"🎉 ऑर्डर टेबल नंबर {table_no} से सीधे किचन में भेज दिया गया है! शेफ आपका खाना तैयार कर रहे हैं।")
    
                 st.write("---")
            
            # 📌 बटन 2: खाना खाने के बाद पेमेंट करने के लिए (यह स्टेटस को 'Paid' कर देगा)
            # 📌 बटन 2: Final Bill Payment

             if st.button("Proceed to Pay (Final Bill) 💳", key="final_pay_btn"):
            
                order_id = st.session_state.get("current_order_id")
            
                if not order_id:
                    st.error("❌ पहले Order Place करें, फिर Payment करें।")
                    st.stop()
            
                amount = int(total_bill)
            
                try:
                    # 1. Razorpay Order Create
                    razorpay_order = create_razorpay_order(amount)
            
                    # 2. Supabase में Pending Payment Save
                    supabase_admin.table("payment_records").insert({
                        "order_id": order_id,
                        "amount": amount,
                        "payment_status": "pending",
                        "razorpay_order_id": razorpay_order["id"],
                        "table_no": str(table_no),
                        "items": str(order_summary_text)
                    }).execute()
                    # supabase_admin.table("payment_records").insert({
                    #     "order_id": order_id,
                    #     "amount": amount,
                    #     "payment_status": "pending",
                    #     "razorpay_order_id": razorpay_order["id"]
                    # }).execute()
            
                    st.info(
                        f"टेबल नंबर {table_no} का कुल फाइनल बिल ₹{amount} है।"
                    )
            
                    # 3. Payment Data
                    payment_data = {
                        "key": RAZORPAY_KEY_ID,
                        "amount": amount * 100,
                        "currency": "INR",
                        "name": "Digital Hotel",
                        "description": f"Table {table_no} Final Bill",
                        "order_id": razorpay_order["id"]
                    }
            
                    # Python Dictionary को JSON में Convert करना
                    payment_data_json = json.dumps(payment_data)
            
                    # 4. Razorpay Checkout
                    st.components.v1.html(
                        f"""
                        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
            
                        <button id="rzp-button"
                            style="
                            padding:12px 25px;
                            font-size:16px;
                            border:none;
                            border-radius:8px;
                            cursor:pointer;
                            background-color:#16a34a;
                            color:white;">
                            💳 Pay ₹{amount}
                        </button>
            
                        <script>
            
                            var options = {payment_data_json};
            
                            options.handler = function(response) {{
            
                                document.getElementById("payment-result").innerHTML =
                                "⏳ Payment response received. Confirmation pending.";
            
                            }};
            
                            var rzp = new Razorpay(options);
            
                            document.getElementById("rzp-button").onclick =
                                function(e) {{
            
                                    rzp.open();
                                    e.preventDefault();
            
                                }};
            
                        </script>
            
                        <div id="payment-result"
                            style="margin-top:15px;font-size:18px;">
                        </div>
                        """,
                        height=180
                    )
            
                except Exception as e:
            
                    st.error(f"❌ Razorpay Error: {e}")
            # 📌 Payment Status Check
             if st.button("Check Payment Status 🔍", key="check_payment_status"):
            
                order_id = st.session_state.get("current_order_id")
            
                if not order_id:
                    st.warning("Pehle order place karein.")
                else:
                    try:
                        response = (
                            supabase_admin.table("payment_records")
                            .select("*")
                            .eq("order_id", order_id)
                            .order("created_at", desc=True)
                            .limit(1)
                            .execute()
                        )
            
                        if response.data:
                            payment = response.data[0]
            
                            if payment["payment_status"] == "captured":
                                st.session_state["show_receipt"] = True
                                st.success("Payment Successful! 🎉")
                            else:
                                st.info("Payment abhi confirm nahi hua hai. Thodi der baad check karein.")
                        else:
                            st.warning("Payment record nahi mila.")
            
                    except Exception as e:
                        st.error(f"Payment check error: {e}")
            # 📌 Payment Successful hone par Complete Receipt
             if st.session_state.get("show_receipt", False):
            
                order_id = st.session_state.get("current_order_id")
            
                receipt_response = (
                    supabase_admin.table("payment_records")
                    .select("*")
                    .eq("order_id", order_id)
                    .eq("payment_status", "captured")
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
            
                if receipt_response.data:
            
                    receipt = receipt_response.data[0]
            
                    st.success("🎉 Payment Successful!")
            
                    st.title("🙏 Thank You for Visiting Shreeji Restaurant!")
                    st.write(
                        "Have a wonderful time ahead, please visit again. ❤️"
                    )
            
                    st.markdown("---")
                    st.header("🧾 YOUR FINAL BILL")
            
                    st.subheader("🍽️ Shreeji Restaurant")
            
                    st.write(f"**Table Number:** {receipt.get('table_no', '')}")
                    st.write(f"**Order ID:** {receipt.get('order_id', '')}")
                    st.write(f"**Payment ID:** {receipt.get('payment_id', '')}")
                    st.write(f"**Date & Time:** {receipt.get('created_at', '')}")
            
                    st.markdown("### Food Details")
            
                    st.text(receipt.get("items", ""))
            
                    st.markdown("---")
            
                    st.subheader(f"Total Amount: ₹{receipt.get('amount', 0)}")
            
                    st.success("PAYMENT STATUS: PAID ✅")
            
                    # Print Bill Button
                    print_items = html.escape(str(receipt.get("items", "")))
                    print_table = html.escape(str(receipt.get("table_no", "")))
                    print_order = html.escape(str(receipt.get("order_id", "")))
                    print_payment = html.escape(str(receipt.get("payment_id", "")))
                    print_date = html.escape(str(receipt.get("created_at", "")))
                    print_amount = receipt.get("amount", 0)
            
                    st.components.v1.html(
                        f"""
                        <button onclick="window.print()"
                        style="padding:12px 25px;background:#16a34a;
                        color:white;border:0;border-radius:8px;font-size:16px;">
                        🖨️ Print Bill
                        </button>
            
                        <div id="bill" style="display:none;">
                            <h2>Shreeji Restaurant</h2>
                            <h3>FINAL BILL</h3>
                            <p>Table Number: {print_table}</p>
                            <p>Order ID: {print_order}</p>
                            <p>Payment ID: {print_payment}</p>
                            <p>Date: {print_date}</p>
                            <pre>{print_items}</pre>
                            <h3>Total: ₹{print_amount}</h3>
                            <h3>PAID</h3>
                            <p>Thank you for visiting us!</p>
                        </div>
            
                        <style>
                        @media print {{
                            body * {{ visibility: hidden; }}
                            #bill, #bill * {{ visibility: visible; }}
                            #bill {{ display:block; position:absolute; top:0; left:0; }}
                        }}
                        </style>
                        """,
                        height=55
                    )
            
                    # Exit Button
                    if st.button("Exit 🚪", key="receipt_exit"):
                        st.session_state["show_receipt"] = False
                        st.session_state["current_order_id"] = None
                        st.session_state.cart = {}
                        st.rerun()
            
                else:
                    st.warning("Receipt nahi mil rahi. Payment status dobara check karein.")

# --- 🚀 स्क्रीन B: किचन/मैनेजर लाइव डैशबोर्ड ---
elif view_mode == "Kitchen Dashboard (किचन/मैनेजर)":
    auto_refresh_kitchen_dashboard()
    st.title("👨‍🍳 किचन लाइव ऑर्डर डैशबोर्ड")
    
# 1. Cloud Database (Supabase) se keval 'Ordered' status wale orders nikalna
   
    response = supabase.table("orders").select("*").eq("status", "ordered").order("id", desc=True).execute()
    # st.write(response.data)
    active_orders = response.data if response.data else []
    
    # 2. [AUTO-SUM CONCEPT]: Paid orders ka Total (SUM) nikalne ke liye cloud call
    # आज की कुल कमाई daily_sales से प्राप्त करें
    today_date = time.strftime("%Y-%m-%d")
    
    total_response = supabase.table("daily_sales").select("total_amount").eq("sale_date", today_date).execute()
    
    grand_total = sum(
        float(row["total_amount"] or 0)
        for row in (total_response.data or [])
    )
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

        # 🗑️ PRACTICAL / TEST ORDERS CLEAR BUTTON
    st.write("---")

    if st.button(
        "🗑️ Clear All Kitchen Orders",
        type="secondary",
        use_container_width=True
    ):
        st.session_state.confirm_order_delete = True

    # ⚠️ Delete Confirmation
    if st.session_state.get("confirm_order_delete", False):

        st.warning(
            "⚠️ क्या आप सभी current Kitchen Orders delete करना चाहते हैं?"
        )

        col_delete, col_cancel = st.columns(2)

        with col_delete:
            if st.button(
                "हाँ, सभी Orders Delete करें 🗑️",
                key="delete_all_kitchen_orders",
                type="primary"
            ):

                supabase.table("orders").delete().eq(
                    "status", "ordered"
                ).execute()

                st.session_state.confirm_order_delete = False

                st.success(
                    "✅ सभी practical Kitchen Orders delete हो गए!"
                )

                time.sleep(1)
                st.rerun()

        with col_cancel:
            if st.button(
                "❌ Cancel",
                key="cancel_delete_orders"
            ):

                st.session_state.confirm_order_delete = False
                st.rerun() 
    
    # एक्टिव ऑर्डर्स को दिखाना
    if not active_orders:
        st.info("अभी किचन में कोई पेंडिंग ऑर्डर नहीं है। शेफ आराम कर रहे हैं! 🍹")
    else:
        for order in active_orders:
            order_id = order['id']
            t_no = order['table_no']
            food_items = order['items']
            bill_amount = order['total']
            # order_id, t_no, food_items, bill_amount = order
            
            with st.expander(f"⚠️ टेबल नंबर {t_no} से नया ऑर्डर! (ID: {order_id})", expanded=True):
                st.write(f"🍛 **ऑर्डर किया गया खाना:** {food_items}")
                st.subheader(f"💰 संभावित बिल (Unpaid): ₹{bill_amount}")
                st.caption("नोट: यह राशि पेमेंट होने के बाद ही मुख्य टोटल गल्ले में जुड़ेगी।")
                
   
# --- 📊 स्क्रीन C: Admin Dashboard ---
else:
    if not manager_login():
        st.stop()

    st.title("📊 Restaurant Admin Dashboard")
    today_date = time.strftime("%Y-%m-%d")
    month_start = time.strftime("%Y-%m-01")

    # Today's Revenue
    today_response = supabase.table("daily_sales").select("total_amount").eq("sale_date", today_date).execute()

    today_revenue = sum(
        float(row.get("total_amount") or 0)
        for row in (today_response.data or [])
    )

    # This Month Revenue
    month_response = supabase.table("daily_sales").select("total_amount").gte("sale_date", month_start).lte("sale_date", today_date).execute()

    month_revenue = sum(
        float(row.get("total_amount") or 0)
        for row in (month_response.data or [])
    )

    col1, col2 = st.columns(2)

        # Total Successful Payments
    payment_response = supabase_admin.table("payment_records").select("id").eq("payment_status", "captured").execute()

    total_payments = len(payment_response.data or [])

    col1, col2, col3 = st.columns(3)

    col1.metric("Today's Revenue", f"₹{today_revenue:,.2f}")
    col2.metric("This Month Revenue", f"₹{month_revenue:,.2f}")
    col3.metric("Successful Payments", total_payments)


     # Recent Sales Records
    st.subheader("📅 Recent Sales Records")

    sales_response = (
        supabase.table("daily_sales")
        .select("sale_date, total_amount")
        .order("sale_date", desc=True)
        .limit(7)
        .execute()
    )

    if sales_response.data:
        st.dataframe(sales_response.data, use_container_width=True)
    else:
        st.info("No sales records available.")

    
   # Daily Sales Chart
    st.subheader("📈 Daily Revenue Chart")

    if sales_response.data:
        chart_data = {
            "Date": [
                row["sale_date"] for row in sales_response.data
            ],
            "Revenue": [
                float(row.get("total_amount") or 0)
                for row in sales_response.data
            ]
        }

        st.bar_chart(chart_data, x="Date", y="Revenue")
    else:
        st.info("No data available for sales chart.")


    #📅 Add Monthly Revenue Chart
    st.subheader("📅 Monthly Revenue Chart")

    monthly_response = (
        supabase.table("daily_sales")
        .select("sale_date, total_amount")
        .order("sale_date", desc=True)
        .limit(365)
        .execute()
    )
    
    monthly_sales = {}
    
    for row in (monthly_response.data or []):
        month = str(row["sale_date"])[:7]
        amount = float(row.get("total_amount") or 0)
    
        monthly_sales[month] = monthly_sales.get(month, 0) + amount

    if monthly_sales:
        monthly_chart_data = {
            "Month": list(sorted(monthly_sales.keys())),
            "Revenue": [monthly_sales[m] for m in sorted(monthly_sales.keys())]
        }

        st.line_chart(monthly_chart_data, x="Month", y="Revenue")
    else:
        st.info("No monthly sales data available.")
        






    
       # Top Selling Food Items
    st.subheader("🍕 Top Selling Food Items")

    food_response = (
        supabase_admin.table("payment_records")
        .select("items")
        .eq("payment_status", "captured")
        .execute()
    )

    food_sales = {}

    for record in (food_response.data or []):
        items_text = record.get("items") or ""

        for line in items_text.splitlines():
            parts = line.split("|")

            if len(parts) == 4:
                try:
                    food_name = parts[0].strip()
                    quantity = int(parts[1].split(":", 1)[1].strip())
                    revenue = float(parts[3].split("₹")[-1].strip())

                    if food_name not in food_sales:
                        food_sales[food_name] = {
                            "Quantity": 0,
                            "Revenue": 0
                        }

                    food_sales[food_name]["Quantity"] += quantity
                    food_sales[food_name]["Revenue"] += revenue

                except (ValueError, IndexError):
                    continue

    if food_sales:
        sorted_food = sorted(
            food_sales.items(),
            key=lambda x: x[1]["Quantity"],
            reverse=True
        )

        st.bar_chart({
            name: details["Quantity"]
            for name, details in sorted_food
        })

        st.dataframe(
            [
                {
                    "Food Item": name,
                    "Quantity Sold": details["Quantity"],
                    "Revenue": f"₹{details['Revenue']:,.2f}"
                }
                for name, details in sorted_food
            ],
            use_container_width=True
        )
    else:
        st.info("No food sales available yet.")

#  Recent Payment Transaction
    st.subheader("💳 Recent Payment Transactions")

    transaction_response = (
        supabase_admin.table("payment_records")
        .select("created_at, order_id, table_no, amount, payment_status")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    if transaction_response.data:
        st.dataframe(
            transaction_response.data,
            use_container_width=True
        )
    else:
        st.info("No payment transactions available.")
    
# add  transaction_response    
    if transaction_response.data:
    csv_buffer = io.StringIO()

    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=[
            "created_at",
            "order_id",
            "table_no",
            "amount",
            "payment_status"
        ]
    )

    writer.writeheader()
    writer.writerows(transaction_response.data)

    st.download_button(
        label="📥 Download Payment Report",
        data=csv_buffer.getvalue(),
        file_name="payment_report.csv",
        mime="text/csv"
    )



























































































































































































































































































































































































































































































































