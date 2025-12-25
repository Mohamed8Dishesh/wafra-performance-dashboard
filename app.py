import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="🚀")

st.title("📊 لوحة تحكم أداء Wafra Store")
st.markdown("---")

# دالة مطورة لتنظيف النسب المئوية ومعالجة الـ NaN
def clean_percentage(value):
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        # تشيل علامة % سواء كانت في الأول أو الآخر
        value = value.replace('%', '').strip()
        try:
            return float(value) / 100
        except:
            return 0.0
    return float(value) if isinstance(value, (int, float)) else 0.0

# 2. أداة رفع الملف
uploaded_file = st.file_uploader("ارفع ملف Taager Analysis.xlsx هنا", type=["xlsx"])

if uploaded_file:
    try:
        # 3. قراءة البيانات
        with st.spinner('جاري تحليل البيانات...'):
            # قراءة الورقتين والتأكد من وجودهم
            xls = pd.ExcelFile(uploaded_file)
            if 'Taager_Data' in xls.sheet_names and 'Dashboard' in xls.sheet_names:
                df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
                df_spend = pd.read_excel(uploaded_file, sheet_name='Dashboard')
            else:
                st.error("⚠️ تأكد من تسمية الورقات بـ 'Taager_Data' و 'Dashboard'")
                st.stop()

        # تنظيف الداتا
        df_taager.columns = df_taager.columns.str.strip()
        df_spend.columns = df_spend.columns.str.strip()

        # دمج البيانات
        df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

        # تنظيف وتحويل الأعمدة الرقمية
        df['نسبة التأكيد'] = df['نسبة التأكيد'].apply(clean_percentage)
        df['نسبة التوصيل'] = df['نسبة التوصيل'].apply(clean_percentage)
        df['مجموع_الارباح_التي_تم_توصيلها'] = df['مجموع_الارباح_التي_تم_توصيلها'].fillna(0)
        df['عدد_القطع التي تم توصيلها بدون مرتجعات'] = df['عدد_القطع التي تم توصيلها بدون مرتجعات'].fillna(0)

        # الحسابات المالية
        EXCHANGE_RATE = 0.036
        df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
        df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
        
        # حساب Net CPO (التكلفة الحقيقية لكل أوردر مستلم)
        df['Net CPO'] = df.apply(
            lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
            if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
        )

        # 4. عرض المقاييس الأساسية (Metrics)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.0f}")
        with m2:
            total_profit = df['صافي الربح'].sum()
            st.metric("صافي الربح الكلي", f"{total_profit:,.0f}", delta=f"{total_profit:,.0f}")
        with m3:
            # استخدام mean مع استبعاد الأصفار لو حبيت دقة أكتر
            avg_conf = df['نسبة التأكيد'].mean()
            st.metric("متوسط التأكيد", f"{avg_conf:.1%}")
        with m4:
            avg_deliv = df['نسبة التوصيل'].mean()
            st.metric("متوسط التسليم", f"{avg_deliv:.1%}")

        st.markdown("---")

        # 5. عرض الجدول الملون (تم إصلاح خطأ matplotlib)
        st.subheader("📋 أداء المنتجات المرفوعة")
        display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
        
        # التنسيق اللوني للجدول
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

        # 6. الرسوم البيانية
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح', 
                          title="صافي الربح لكل منتج", color_continuous_scale='RdYlGn')
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع ميزانية الإعلانات")
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء المعالجة: {e}")
else:
    st.info("👋 يا هندسة، ارفع ملف Taager Analysis.xlsx عشان أبدأ التحليل.")
