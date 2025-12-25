import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة والأمان
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="🔒")

# دالة التحقق من كلمة السر
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("أدخل كلمة السر لرؤية الأرقام المالية", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("كلمة السر خاطئة، حاول مرة أخرى", type="password", on_change=password_entered, key="password")
        st.error("😕 كلمة السر غير صحيحة")
        return False
    else:
        return True

if check_password():
    # 2. إعدادات الروابط
    SHEET_ID = "1Vh8dCL8DCR93ZPah-itG06dk_i9WgJ5LtF_TmvcARbQ"
    URL_TAAGER = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Taager_Data"
    URL_SPEND = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Dashboard"

    # دالة لتنظيف الأرقام من الفواصل والنصوص
    def to_float(column):
        return pd.to_numeric(column.astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

    def clean_percentage(value):
        if pd.isna(value) or value == "": return 0.0
        if isinstance(value, str):
            value = value.replace('%', '').strip()
            try: return float(value) / 100
            except: return 0.0
        return float(value)

    st.title("🚀 لوحة تحكم Wafra Store (Live)")
    st.write("---")

    try:
        # 3. جلب البيانات
        df_taager = pd.read_csv(URL_TAAGER)
        df_spend = pd.read_csv(URL_SPEND)

        # دمج البيانات
        df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

        # --- تنظيف الأرقام الحاسم لمنع الخطأ ---
        df['مجموع_الارباح_التي_تم_توصيلها'] = to_float(df['مجموع_الارباح_التي_تم_توصيلها'])
        df['صرف الفيسبوك'] = to_float(df['صرف الفيسبوك'])
        df['عدد_القطع التي تم توصيلها بدون مرتجعات'] = to_float(df['عدد_القطع التي تم توصيلها بدون مرتجعات'])
        
        # معالجة النسب
        df['نسبة التأكيد'] = df['نسبة التأكيد'].apply(clean_percentage)
        df['نسبة التوصيل'] = df['نسبة التوصيل'].apply(clean_percentage)

        # الحسابات المالية (الآن ستعمل بدون خطأ)
        EXCHANGE_RATE = 0.036
        df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
        df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
        
        # حساب Net CPO
        df['Net CPO'] = df.apply(
            lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
            if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
        )

        # 4. عرض الخلاصة (Metrics)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.0f}")
        m2.metric("صافي الربح الكلي", f"{df['صافي الربح'].sum():,.0f}")
        m3.metric("متوسط التأكيد", f"{df['نسبة التأكيد'].mean():.1%}")
        m4.metric("متوسط التسليم", f"{df['نسبة التوصيل'].mean():.1%}")

        st.markdown("---")

        # 5. عرض الجدول الملون
        st.subheader("📋 أداء المنتجات التفصيلي")
        display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
        st.dataframe(
            display_df.style.background_gradient(cmap='RdYlGn', subset=['صافي الربح'])
            .format({'نسبة التأكيد': '{:.1%}', 'نسبة التوصيل': '{:.1%}', 'صافي الربح': '{:,.2f}', 'Net CPO': '{:,.2f}'}),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"⚠️ فشل في معالجة البيانات: {e}")
