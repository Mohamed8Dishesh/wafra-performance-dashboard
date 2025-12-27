import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="🚀")

st.title("📊 لوحة تحكم أداء Wafra Store (الرفع اليدوي)")
st.markdown("---")

# دالة لتنظيف النسب المئوية ومعالجة الخلايا الفارغة
def clean_percentage(value):
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        # إزالة علامة % وتنظيف المسافات
        value = value.replace('%', '').strip()
        try:
            return float(value) / 100
        except:
            return 0.0
    return float(value) if isinstance(value, (int, float)) else 0.0

# 2. أداة رفع الملف
uploaded_file = st.file_uploader("ارفع ملف الإكسيل (Taager Analysis) هنا", type=["xlsx"])

if uploaded_file:
    try:
        # 3. قراءة البيانات من الورقتين الأساسيتين
        with st.spinner('جاري معالجة البيانات...'):
            df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
            df_spend = pd.read_excel(uploaded_file, sheet_name='Dashboard')

        # تنظيف أسماء الأعمدة من أي مسافات مخفية
        df_taager.columns = df_taager.columns.str.strip()
        df_spend.columns = df_spend.columns.str.strip()

        # 4. معالجة البيانات (Data Processing)
        # دمج البيانات بناءً على "كود المنتج"
        df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

        # تنظيف وتحويل النسب المئوية (لحل مشكلة nan% في الصور)
        df['نسبة التأكيد'] = df['نسبة التأكيد'].apply(clean_percentage)
        df['نسبة التوصيل'] = df['نسبة التوصيل'].apply(clean_percentage)
        
        # التأكد من تحويل الأعمدة المالية لأرقام (لحل مشكلة الفواصل في الأرقام الكبيرة)
        for col in ['مجموع_الارباح_التي_تم_توصيلها', 'صرف الفيسبوك', 'عدد_القطع التي تم توصيلها بدون مرتجعات']:
             df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # 5. الحسابات المالية (Logic)
        EXCHANGE_RATE = 0.036  # تحويل الدينار العراقي لجنيه مصري
        df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
        df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
        
        # حساب تكلفة الطلب المستلم الحقيقية (Net CPO)
        df['Net CPO'] = df.apply(
            lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
            if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
        )

        # 6. عرض المقاييس الأساسية (Top Metrics)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.0f}")
        with m2:
            total_profit = df['صافي الربح'].sum()
            st.metric("صافي الربح الكلي", f"{total_profit:,.0f}", delta=f"{total_profit:,.0f}")
        with m3:
            st.metric("متوسط التأكيد", f"{df['نسبة التأكيد'].mean():.1%}")
        with m4:
            st.metric("متوسط التسليم", f"{df['نسبة التوصيل'].mean():.1%}")

        st.markdown("---")

        # 7. عرض الجدول الملون (تحتاج لمكتبة matplotlib ليعمل الـ gradient)
        st.subheader("📋 تفاصيل أداء المنتجات")
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

        # 8. الرسوم البيانية
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح', 
                                   title="صافي الربح لكل منتج", color_continuous_scale='RdYlGn'), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع ميزانية الإعلانات"), use_container_width=True)

    except Exception as e:
        st.error(f"❌ حدث خطأ في معالجة الملف: {e}")
else:
    st.info("👋 يا هندسة، ارفع ملف Taager Analysis.xlsx اللي جواه الورقتين عشان أبدأ التحليل.")
