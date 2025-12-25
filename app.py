import streamlit as st
import pandas as pd
import plotly.express as px

# إعدادات الصفحة
st.set_page_config(page_title="Wafra Store - Performance Dashboard", layout="wide")

st.title("📊 لوحة تحكم أداء Wafra Store - السوق العراقي")
st.markdown("---")

# 1. رفع الملف
uploaded_file = st.file_uploader("ارفع ملف Taager Analysis هنا", type=["xlsx"])

if uploaded_file:
    # قراءة البيانات
    try:
        df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
        df_dashboard = pd.read_excel(uploaded_file, sheet_name='Dashboard')
        
        # دمج البيانات بناءً على كود المنتج
        # هناخد 'الصرف' بس من شيت الداش بورد ونربطه بالداتا الأصلية
        df_spend = df_dashboard[['كود المنتج', 'صرف الفيسبوك']]
        final_df = pd.merge(df_taager, df_spend, on='كود المنتج', how='inner')

        # 2. الحسابات والتحويلات (المنطق البرمجي)
        EXCHANGE_RATE = 0.036
        final_df['الربح بالجنيه'] = final_df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
        final_df['صافي الربح'] = final_df['الربح بالجنيه'] - final_df['صرف الفيسبوك']
        
        # حساب التكلفة لكل طلب مستلم (Net CPO)
        final_df['Net CPO'] = final_df.apply(
            lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
            if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1
        )

        # 3. عرض المؤشرات العامة (Top Metrics)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("إجمالي الصرف (جنيه)", f"{final_df['صرف الفيسبوك'].sum():,.0f}")
        with col2:
            st.metric("إجمالي صافي الربح (جنيه)", f"{final_df['صافي الربح'].sum():,.0f}", 
                      delta=f"{final_df['صافي الربح'].sum():,.0f}")
        with col3:
            avg_delivery = final_df['نسبة التوصيل'].mean()
            st.metric("متوسط نسبة التوصيل", f"{avg_delivery:.1%}")
        with col4:
            total_orders = final_df['عدد_القطع المطلوبة'].sum()
            st.metric("إجمالي الأوردرات", f"{total_orders:,.0f}")

        st.markdown("---")

        # 4. جدول الأداء التفصيلي لكل منتج
        st.subheader("📋 تفاصيل أداء المنتجات")
        
        # تنسيق الجدول بالألوان
        def color_profit(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'

        display_df = final_df[['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'الربح بالجنيه', 'صافي الربح', 'Net CPO']]
        st.dataframe(display_df.style.applymap(color_profit, subset=['صافي الربح']).format({
            'نسبة التأكيد': '{:.1%}',
            'نسبة التوصيل': '{:.1%}',
            'صافي الربح': '{:,.2f}',
            'Net CPO': '{:,.2f}'
        }))

        # 5. تحليل بصري (Charts)
        st.markdown("---")
        c1, c2 = st.columns(2)
        
        with c1:
            fig_profit = px.bar(final_df, x='اسم المنتج', y='صافي الربح', title="صافي الربح لكل منتج", color='صافي الربح')
            st.plotly_chart(fig_profit, use_container_width=True)
            
        with c2:
            fig_spend = px.pie(final_df, values='صرف الفيسبوك', names='اسم المنتج', title="توزيع ميزانية الإعلانات")
            st.plotly_chart(fig_spend, use_container_width=True)

    except Exception as e:
        st.error(f"حصلت مشكلة في قراءة البيانات: {e}")
else:
    st.info("يا هندسة ارفع ملف الإكسيل عشان نبدأ التحليل.")