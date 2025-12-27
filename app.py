import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. إعدادات الصفحة
st.set_page_config(page_title="Wafra Analytics Engine", layout="wide", page_icon="🚀")

# دالة التحقق من كلمة السر (اختياري، لحماية أداتك الخاصة)
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 نظام Wafra Store المحمي")
        pwd = st.text_input("أدخل كلمة السر للوصول لأداة التحليل", type="password")
        if st.button("دخول"):
            if pwd == st.secrets.get("APP_PASSWORD", "123"): # الباسورد الافتراضي 123 لو مغيرتوش
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ كلمة السر خاطئة")
        return False
    return True

# دالة تنظيف البيانات (لحل مشاكل الفواصل والنسب المئوية)
def clean_numeric_data(df):
    df.columns = df.columns.str.strip()
    # تنظيف النسب المئوية
    for col in ['نسبة التأكيد', 'نسبة التوصيل']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) / 100
    # تنظيف المبالغ المالية (إزالة الفواصل)
    for col in ['مجموع_الارباح_التي_تم_توصيلها', 'صرف الفيسبوك', 'عدد_القطع التي تم توصيلها بدون مرتجعات']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    return df

# تشغيل التطبيق بعد التحقق من الباسورد
if check_password():
    st.title("📊 نظام تحليل الأداء (الرفع اليدوي)")
    st.info("قم برفع ملف الإكسيل المحدث للحصول على آخر التحليلات")
    
    # 2. أداة رفع الملف (هي المصدر الوحيد للبيانات الآن)
    uploaded_file = st.file_uploader("📂 ارفع ملف Taager Analysis.xlsx هنا", type=["xlsx"])

    if uploaded_file:
        try:
            # 3. معالجة الملف المرفوع
            with st.spinner('جاري قراءة الملف وتحليل الأداء...'):
                df_taager = pd.read_excel(uploaded_file, sheet_name='Taager_Data')
                df_spend = pd.read_excel(uploaded_file, sheet_name='Dashboard')
                
                df_taager = clean_numeric_data(df_taager)
                df_spend = clean_numeric_data(df_spend)
                
                # دمج البيانات بناءً على كود المنتج
                df = pd.merge(df_taager, df_spend[['كود المنتج', 'صرف الفيسبوك']], on='كود المنتج', how='inner')
                
                # الحسابات المالية (0.036 معامل تحويل الدينار لجنيه)
                EXCHANGE_RATE = 0.036
                df['الربح بالجنيه'] = df['مجموع_الارباح_التي_تم_توصيلها'] * EXCHANGE_RATE
                df['صافي الربح'] = df['الربح بالجنيه'] - df['صرف الفيسبوك']
                # حساب Net CPO (تكلفة الأوردر المستلم فعلياً)
                df['Net CPO'] = df.apply(lambda x: x['صرف الفيسبوك'] / x['عدد_القطع التي تم توصيلها بدون مرتجعات'] 
                                        if x['عدد_القطع التي تم توصيلها بدون مرتجعات'] > 0 else 0, axis=1)

            # 4. عرض الداش بورد - الأداء العام
            st.markdown("### 🌐 ملخص الأداء العام")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("إجمالي الصرف", f"{df['صرف الفيسبوك'].sum():,.0f} ج.م")
            m2.metric("صافي الربح الكلي", f"{df['صافي الربح'].sum():,.0f} ج.م", delta=f"{df['صافي الربح'].sum():,.0f}")
            m3.metric("متوسط التأكيد", f"{df['نسبة التأكيد'].mean():.1%}")
            m4.metric("متوسط التسليم", f"{df['نسبة التوصيل'].mean():.1%}")

            st.markdown("---")

            # 5. تحليل المنتج المختار (Drill-down)
            st.subheader("🎯 تحليل تفصيلي لمنتج معين")
            selected_product = st.selectbox("اختر المنتج لمراجعة أرقامه:", df['اسم المنتج'].unique())
            p_data = df[df['اسم المنتج'] == selected_product].iloc[0]
            
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("صافي ربح المنتج", f"{p_data['صافي الربح']:,.2f} ج.م")
            pc2.metric("تكلفة الطلب المستلم (CPO)", f"{p_data['Net CPO']:,.2f} ج.م")
            pc3.metric("نسبة توصيل المنتج", f"{p_data['نسبة التوصيل']:.1%}")

            # 6. الجدول الملون الاحترافي
            st.markdown("### 📑 قائمة المنتجات المرفوعة")
            display_cols = ['اسم المنتج', 'صرف الفيسبوك', 'نسبة التأكيد', 'نسبة التوصيل', 'صافي الربح', 'Net CPO']
            st.dataframe(
                df[display_cols].style.background_gradient(cmap='RdYlGn', subset=['صافي الربح'])
                .format({'نسبة التأكيد': '{:.1%}', 'نسبة التوصيل': '{:.1%}', 'صافي الربح': '{:,.2f}', 'Net CPO': '{:,.2f}'}),
                use_container_width=True
            )

            # 7. الرسوم البيانية
            st.markdown("### 📊 تحليل بصري")
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(px.bar(df, x='اسم المنتج', y='صافي الربح', color='صافي الربح', 
                                       title="توزيع الأرباح الصافية"), use_container_width=True)
            with g2:
                st.plotly_chart(px.pie(df, values='صرف الفيسبوك', names='اسم المنتج', hole=0.4, 
                                       title="توزيع ميزانية الإعلانات"), use_container_width=True)

        except Exception as e:
            st.error(f"❌ حدث خطأ في معالجة الملف: {e}")
            st.info("تأكد من أن الملف يحتوي على ورقتين باسم 'Taager_Data' و 'Dashboard'")
