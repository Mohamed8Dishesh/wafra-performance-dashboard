import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store Dashboard", layout="wide", page_icon="🚀")

st.title("📊 لوحة تحكم أداء Wafra Store")
st.markdown("---")

# 2. إعداد الاتصال بجوجل شيت
# تم استخدام الرابط المختصر لتجنب خطأ 400
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Vh8dCL8DCR93ZPah-itG06dk_i9WgJ5LtF_TmvcARbQ/"

conn = st.connection("gsheets", type=GSheetsConnection)

def clean_percentage(value):
    """دالة لتحويل النصوص مثل '%46.67' إلى أرقام عشرية 0.4667"""
    if isinstance(value, str):
        value = value.replace('%', '').strip()
        try:
            return float(value) / 100
        except:
            return 0.0
    return value

try:
    # 3. جلب البيانات (مع إلغاء الكاش لضمان التحديث اللحظي)
    with st.spinner('جاري تحميل البيانات من جوجل شيت...'):
        df_taager = conn.read(spreadsheet=SHEET_URL, worksheet="Taager_Data", ttl=0)
        df_spend = conn.read(spreadsheet=SHEET_URL, worksheet="Dashboard", ttl=0)

    # 4. معالجة البيانات (Data Cleaning)
    # التأكد من أسماء الأعمدة وتنظيف المسافات
    df_taager.columns = df_taager.columns.str.strip()
    df_spend.columns = df_spend.columns.str.strip()

    # دمج البيانات
    df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')

    # تنظيف النسب المئوية وتحويلها لأرقام
    df['نسبة التأكيد'] = df['نسبة التأكيد'].apply(clean_percentage)
    df['نسبة التوصيل'] = df['نسبة التوصيل'].apply(clean_percentage)

    # الحسابات المالية
    EXCHANGE_RATE = 0.036 # تحويل الدينار لجنيه
    df['أرباح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
    df['صافي الربح'] = df['أرباح بالجنيه'] - df['صرف الفيسبوك']
    
    # حساب Net CPO
    df['Net CPO'] = df.apply(
        lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
        if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
    )

    # 5. عرض الخلاصة (Top Performance Metrics)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("إجمالي الصرف (جنيه)", f"{df['صرف الفيسبوك'].sum():,.0f}")
    with m2:
        total_profit = df['صافي الربح'].sum()
        st.metric("إجمالي صافي الربح", f"{total_profit:,.2f}", delta=f"{total_profit:,.2f}")
    with m3:
        avg_conf = df['نسبة التأكيد'].mean()
        st.metric("متوسط نسبة التأكيد", f"{avg_conf:.1%}")
    with m4:
        avg_deliv = df['نسبة التوصيل'].mean()
        st.metric("متوسط نسبة التوصيل", f"{avg_deliv:.1%}")

    st.markdown("---")

    # 6. الجدول الاحترافي
    st.subheader("📋 تفاصيل أداء المنتجات")
    
    display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
    
    # تنسيق الجدول بالألوان (تدرج لوني للربح)
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
                           title="صافي الربح لكل منتج (بالجنيه)", 
                           color_continuous_scale='RdYlGn', template="plotly_white")
        st.plotly_chart(fig_profit, use_container_width=True)
        
    with c2:
        fig_spend = px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', 
                          title="توزيع ميزانية الإعلانات", hole=0.4)
        st.plotly_chart(fig_spend, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ حدث خطأ في النظام: {e}")
    st.warning("تأكد من ضبط الـ Secrets في Streamlit Cloud ومن أن أسماء الصفحات في جوجل شيت صحيحة.")
