import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Store | Advanced Analytics", layout="wide", page_icon="📈")

# ستايل مخصص للعناوين
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 نظام تحليل الأداء الاحترافي - Wafra Store")
st.markdown("---")

# دالة تنظيف البيانات
def clean_data(df):
    # تنظيف أسماء الأعمدة
    df.columns = df.columns.str.strip()
    # تنظيف النسب المئوية
    for col in ['نسبة التأكيد', 'نسبة التوصيل']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) / 100
    # تنظيف الأرقام المالية
    for col in ['مجموع_الارباح_التي_تم_توصيلها', 'صرف الفيسبوك', 'عدد_القطع التي تم توصيلها بدون مرتجعات']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    return df

# 2. أداة رفع الملف
uploaded_file = st.file_uploader("📂 ارفع ملف Taager Analysis.xlsx", type=["xlsx"])

if uploaded_file:
    try:
        # 3. قراءة ومعالجة البيانات
        with st.spinner('جاري معالجة البيانات وبناء الداش بورد...'):
            df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
            df_spend = pd.read_excel(uploaded_file, sheet_name='Dashboard')
            
            df_taager = clean_data(df_taager)
            df_spend = clean_data(df_spend)
            
            # دمج البيانات
            df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')
            
            # الحسابات المالية (بناءً على 0.036 معامل تحويل)
            EXCHANGE_RATE = 0.036
            df['الربح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
            df['صافي الربح'] = df['الربح بالجنيه'] - df['صرف الفيسبوك']
            df['Net CPO'] = df.apply(lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
                                    if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1)

        # 4. القسم الأول: الأداء العام (Global Metrics)
        st.subheader("🌐 ملخص الأداء العام")
        c1, c2, c3, c4 = st.columns(4)
        total_spend = df['صرف الفيسبوك'].sum()
        total_profit = df['صافي الربح'].sum()
        
        c1.metric("إجمالي الصرف", f"{total_spend:,.0f} ج.م")
        c2.metric("صافي الربح", f"{total_profit:,.0f} ج.م", delta=f"{total_profit:,.0f}")
        c3.metric("متوسط التأكيد", f"{df['نسبة التأكيد'].mean():.1%}")
        c4.metric("متوسط التسليم", f"{df['نسبة التوصيل'].mean():.1%}")

        st.markdown("---")

        # 5. القسم الثاني: داش بورد لكل منتج (Product Drill-down)
        st.subheader("🎯 تحليل تفصيلي لكل منتج")
        selected_product = st.selectbox("اختر المنتج لتحليله بدقة:", df['اسم المنتج'].unique())
        
        product_data = df[df['اسم المنتج'] == selected_product].iloc[0]
        
        p_col1, p_col2 = st.columns([1, 2])
        
        with p_col1:
            st.info(f"**بيانات: {selected_product}**")
            st.write(f"**كود المنتج:** `{product_data['كود المنتج']}`")
            st.metric("تكلفة الطلب المستلم (Net CPO)", f"{product_data['Net CPO']:,.2f} ج.م")
            st.metric("صافي ربح المنتج", f"{product_data['صافي الربح']:,.2f} ج.م")
            
        with p_col2:
            # رسم بياني لمقارنة الصرف بالربح للمنتج المختار
            fig_compare = go.Figure(data=[
                go.Bar(name='الصرف (جنيه)', x=['الأداء المالي'], y=[product_data['صرف الفيسبوك']], marker_color='#ef553b'),
                go.Bar(name='الربح الصافي (جنيه)', x=['الأداء المالي'], y=[product_data['صافي الربح']], marker_color='#00cc96')
            ])
            fig_compare.update_layout(barmode='group', height=300, margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("---")

        # 6. القسم الثالث: مقارنة شاملة (Comparison Table)
        st.subheader("📑 جدول مقارنة المنتجات")
        display_df = df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']]
        
        st.dataframe(
            display_df.style.background_gradient(cmap='RdYlGn', subset=['صافي الربح'])
            .format({
                'نسبة التأكيد': '{:.1%}', 'نسبة التوصيل': '{:.1%}', 
                'صافي الربح': '{:,.2f}', 'Net CPO': '{:,.2f}', 'صرف الفيسبوك': '{:,.0f}'
            }),
            use_container_width=True
        )

        # 7. الرسوم البيانية العامة
        st.subheader("📈 التحليل البصري للبراند")
        g1, g2 = st.columns(2)
        with g1:
            fig_bar = px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح', 
                             title="صافي الربح لكل منتج", color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_bar, use_container_width=True)
        with g2:
            fig_pie = px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع ميزانية الإعلانات", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    except Exception as e:
        st.error(f"❌ حدث خطأ: {e}")
else:
    st.info("👋 يا هندسة، ارفع ملف Taager Analysis.xlsx عشان نفتح الداش بورد الاحترافية.")
