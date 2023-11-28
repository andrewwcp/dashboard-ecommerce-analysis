import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')


def create_monthly_orders_df(df):
    """function untuk melihat performa penjualan dan revenue dalam beberapa bulan terakhir"""
    monthly_orders_df = df.resample(rule='M', on='order_purchase_timestamp').agg({
    "order_id": "nunique",
    "payment_value": "sum"
    })
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_purchase_timestamp": "order_date",
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)
    # monthly_orders_df = monthly_orders_df[monthly_orders_df['order_date'] >= '2018-01']
    return monthly_orders_df

def create_sales_by_cat(df):
    sales_by_cat = df.groupby(['product_category_name_english']).agg({
    "order_id": "nunique",
    "payment_value": "sum"
    })
    sales_by_cat = sales_by_cat.reset_index()
    sales_by_cat.rename(columns={
        "product_category_name_english": "category_product",
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)

    return sales_by_cat

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby('product_category_name_english').agg({"order_id":"nunique"}).sort_values(by=("order_id"), ascending=False).reset_index()
    sum_order_items_df.rename(columns={
        "product_category_name_english": "category_product",
        "order_id": "order_count"
    }, inplace=True)

    return sum_order_items_df

def create_score_items_df(df):
    df_rating = df[df['review_score'] != 'Not Defined']
    df_rating = df_rating.astype({'review_score': 'float64'})
    avg_rating_items_df = df_rating.groupby('product_category_name_english')['review_score'].mean().sort_values(ascending=False).reset_index()
    avg_rating_items_df.rename(columns={
        "product_category_name_english": "category_product",
        "review_score": "avg_rating"
    }, inplace=True)
    return avg_rating_items_df

def create_bycity(df):
    bycity_df = df.groupby(['customer_city']).customer_id.nunique().sort_values(ascending=False).reset_index()
    bycity_df.rename(columns={
    "customer_id": "customer_count"
    }, inplace=True)
    return bycity_df

def create_bystate(df):
    bystate_df = df.groupby(['customer_state']).customer_id.nunique().sort_values(ascending=False).reset_index()
    bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    return bystate_df


all_df = pd.read_csv("e-comm_delivered.csv")

datetime_columns = ["order_purchase_timestamp"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    #menambahkan logo perusahaan
    st.header('Please Filter Here: ')

    #mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Select Range of Date',
        min_value=min_date,
        max_value=max_date,
        value=[min_date,max_date]
    )

    state_filter = st.multiselect(
        "Select the State:",
        options=all_df["customer_state"].unique(),
        default=all_df["customer_state"].unique()
    )

    payment_type_filter = st.multiselect(
        "Select the Payment Type:",
        options=all_df["payment_type"].unique(),
        default=all_df["payment_type"].unique()
    )
    
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))] 

main_df = main_df.query(
    "customer_state == @state_filter & payment_type == @payment_type_filter"
)

monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
avg_rating_items_df = create_score_items_df(main_df)
bycity_df = create_bycity(main_df)
bystate_df = create_bystate(main_df)
sales_by_cat = create_sales_by_cat(main_df)

st.header(':bar_chart: E-comm Dashboard')
st.markdown('##')

#DAILY ORDER
st.subheader('Daily Orders')
col1, col2, col3 = st.columns([0.3, 0.2, 0.5])
with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)
with col2:
    df_rating_nn = main_df[main_df['review_score'] != 'Not Defined']
    df_rating_nn = df_rating_nn.astype({'review_score': 'float'})
    avarage_rating = round(df_rating_nn['review_score'].mean(), 1)
    star_rating = ":star:" * int(round(avarage_rating, 0))
    st.metric("Avarage Rating", value=avarage_rating)
with col3:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "USD", locale='es_CO', currency_digits=False)
    st.metric("Total Revenue", value=total_revenue)
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_df['order_date'],
    monthly_orders_df['order_count'],
    marker='o',
    linewidth=2,
    color='#90CAF9'
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15, rotation=45)
st.pyplot(fig)


#SALES BY CAT
st.subheader("Top 5 Sales by Category")
fig, ax = plt.subplots(nrows=1, figsize=(24, 15))
color_best = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x="revenue", y="category_product", data=sales_by_cat.sort_values(by=('revenue'), ascending=False).head(), palette=color_best, ax=ax)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis ='y', labelsize=12)
st.pyplot(fig)

#BEST AND WORST PERFORMING PRODUCT
st.subheader("Best & Worst Performing Product")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 15))
color_best = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
color_worst = ["#FF6961", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x="order_count", y="category_product", data=sum_order_items_df.head(5), palette=color_best, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Product", loc="center", fontsize=15)
ax[0].tick_params(axis ='y', labelsize=12)
sns.barplot(x="order_count", y="category_product", data=sum_order_items_df.sort_values(by="order_count", ascending=True).head(5), palette=color_worst, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
st.pyplot(fig)

#BEST AND WORST RATING PRODUCT
st.subheader("Best & Worst Rating Product by Rating")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 15), dpi=300)
color_best = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
color_worst = ["#FF6961", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x="avg_rating", y="category_product", data=avg_rating_items_df.head(5), palette=color_best, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Rating Product", loc="center", fontsize=15)
ax[0].tick_params(axis ='y', labelsize=12)
sns.barplot(x="avg_rating", y="category_product", data=avg_rating_items_df.sort_values(by="avg_rating", ascending=True).head(5), palette=color_worst, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Rating Product", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
st.pyplot(fig)  

