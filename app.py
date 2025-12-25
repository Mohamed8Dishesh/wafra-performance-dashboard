import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="📊")

st.title("🚀 لوحة تحكم أداء Wafra Store")
st.markdown(f"**رابط المصدر:** [Google Sheets]({'https://docs.google.com/spreadsheets/d/1Vh8dCL8DCR93ZPah-itG06dk_i9WgJ5LtF_TmvcARbQ/edit?usp=sharing'})")
st.markdown("---")

# 2. إنشاء الاتصال بجوجل شيت
conn = st.connection("gsheets", type=GSheetsConnection)

# الرابط الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Vh8dCL8DCR93ZPah-itG06dk_i9WgJ5LtF_TmvcARbQ/edit?usp=sharing"

try:
    # 3. قراءة الورقتين من نفس الرابط
    # تأكد أن الأسماء (Taager_Data) و (Dashboard) مكتوبة في الشيت بالظبط كدا
    df_taager = conn.read(spreadsheet=SHEET_URL, worksheet="Taager_Data")
    df_spend = conn.read(spreadsheet=SHEET_URL, worksheet="Dashboard")

    # 4. معالجة البيانات
    # دمج البيانات بناءً على كود المنتج
    # سنفترض أن عمود الصرف في ورقة Dashboard اسمه "صرف الفيسبوك"
    df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

    # حسابات العملة والربح
    EXCHANGE_RATE = 0.036
    df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
    df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
    
    # حساب تكلفة الطلب المستلم (Net CPO)
    df['Net CPO'] = df.apply(
        lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
        if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
    )

    # 5. عرض الخلاصة (Top Metrics)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.2f}")
    with m2:
        total_profit = df['صافي الربح'].sum()
        st.metric("صافي الربح الكلي", f"{total_profit:,.2f}", delta=f"{total_profit:,.2f}")
    with m3:
        avg_conf = df['نسبة التأكيد'].mean()
        st.metric("متوسط التأكيد", f"{avg_conf:.1%}")
    with m4:
        avg_deliv = df['نسبة التوصيل'].mean()
        st.metric("متوسط التسليم", f"{avg_deliv:.1%}")

    st.markdown("---")

    # 6. الجدول التفصيلي
    st.subheader("📋 أداء كل منتج على حدة")
    
    display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
    
    # تنسيق الجدول
    st.dataframe(
        display_df.style.background_gradient(cmap='RdYlGn', subset=['صافي الربح']),
        use_container_width=True
    )

    # 7. الرسوم البيانية
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_profit = px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح',
                           title="صافي الربح لكل منتج", color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_profit, use_container_width=True)
        
    with col_right:
        fig_spend = px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع الصرف")
        st.plotly_chart(fig_spend, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ خطأ في قراءة البيانات: {e}")
    st.info("تأكد من أن أسماء أوراق العمل (Tabs) هي 'Taager_Data' و 'Dashboard' بالضبط.")
