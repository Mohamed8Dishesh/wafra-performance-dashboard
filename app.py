import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="🚀")

st.title("📊 لوحة تحكم أداء Wafra Store (رفع يدوي)")
st.markdown("---")

# دالة لتنظيف النسب المئوية
def clean_percentage(value):
    if isinstance(value, str):
        value = value.replace('%', '').strip()
        try:
            return float(value) / 100
        except:
            return 0.0
    return value

# 2. أداة رفع الملف
uploaded_file = st.file_uploader("ارفع ملف الإكسيل (Taager Analysis) هنا", type=["xlsx"])

if uploaded_file:
    try:
        # 3. قراءة الورقتين من الملف المرفوع
        with st.spinner('جاري معالجة الملف...'):
            df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
            df_spend = pd.read_excel(uploaded_file, sheet_name='Dashboard')

        # تنظيف أسماء الأعمدة
        df_taager.columns = df_taager.columns.str.strip()
        df_spend.columns = df_spend.columns.str.strip()

        # 4. معالجة البيانات (Data Processing)
        # دمج البيانات بناءً على كود المنتج
        # نأخذ 'صرف الفيسبوك' فقط من شيت الداش بورد
        df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

        # تنظيف النسب المئوية
        df['نسبة التأكيد'] = df['نسبة التأكيد'].apply(clean_percentage)
        df['نسبة التوصيل'] = df['نسبة التوصيل'].apply(clean_percentage)

        # الحسابات المالية
        EXCHANGE_RATE = 0.036  # تحويل الدينار لجنيه
        df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
        df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
        
        # حساب Net CPO
        df['Net CPO'] = df.apply(
            lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
            if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
        )

        # 5. عرض الخلاصة (Top Metrics)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.0f}")
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
        st.subheader("📋 أداء المنتجات المرفوعة")
        display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
        
        st.dataframe(
            display_df.style.background_gradient(cmap='RdYlGn', subset=['صافي الربح'])
            .format({
                'نسبة التأكيد': '{:.1%}',
                'نسبة التوصيل': '{:.1%}',
                'صافي الربح': '{:,.2f}',
                'Net CPO': '{:,.2f}'
            }),
            use_container_width=True
        )

        # 7. الرسوم البيانية
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            fig_profit = px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح',
                               title="صافي الربح لكل منتج", color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_profit, use_container_width=True)
        with c2:
            fig_spend = px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع ميزانية الإعلانات")
            st.plotly_chart(fig_spend, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ حصلت مشكلة في قراءة الملف: {e}")
        st.info("تأكد أن الملف يحتوي على ورقتين باسم 'Taager_Data' و 'Dashboard'.")
else:
    st.info("👋 يا هندسة، ارفع ملف الإكسيل اللي جواه الورقتين عشان أبدأ التحليل فوراً.")
