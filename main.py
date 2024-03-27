import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_folium import st_folium
import pandas as pd
import folium
from data import fetch_data
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from kneed import KneeLocator
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import altair as alt
from auth import verify_user_login


st.set_page_config(
    page_title="Dashboard Tanaman Pangan",
    page_icon="📈",
    layout="centered"
)
#Fungsi untuk login
def login():
    # Initialize session state
    session_state = st.session_state

    # Check if user is logged in
    if 'is_logged_in' not in session_state:
        session_state.is_logged_in = False
    
    # If user is not logged in, show login form
    if not session_state.is_logged_in:
        st.title("Login")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Login"):
            if verify_user_login(username, password):
                session_state.is_logged_in = True
                st.success("Login successful!")
            else:
                st.error("Invalid username or password. Please try again.")
    # If user is logged in, show dashboard
    if session_state.is_logged_in:
        selection_menu()


# Fungsi untuk logout
def logout():
    # Set status login menjadi False
    st.session_state.is_logged_in = False
    # Rerun aplikasi untuk kembali ke halaman login
    st.rerun()

#dashboard
def dashboard_page():
    # Title
    st.title('Dashboard Tanaman Pangan')
    # Daftar nama tabel yang ingin ditampilkan
    table_names = ['jagung', 'padi', 'kedelai', 'kacang_tanah', 'kacang_hijau', 'ubi_kayu', 'ubi_jalar']

    # Tampilkan pilihan tabel pada sidebar
    selected_table = st.selectbox("Pilih Komoditas", table_names)

    # Query untuk mengambil data dari tabel terpilih
    query = f"SELECT * FROM {selected_table}"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=["Provinsi", "Komoditas", "Tahun", "Luas Panen", "Produksi", "KMeans", "KMeans Label"])

    # Filter komoditas berdasarkan tabel yang dipilih
    filtered_df = df.loc[df['Komoditas'].isin(df.loc[df['Komoditas'].notnull(), 'Komoditas'].unique())]

    # Filter tahun
    selected_year = st.selectbox("Pilih Tahun", filtered_df['Tahun'].unique())

    # Filter data berdasarkan tahun
    filtered_df = filtered_df[filtered_df['Tahun'].isin([selected_year])]

    # Create map
    map = folium.Map(location=[-0.4471363, 120.1655734], zoom_start=4, scrollWheelZoom=False, tiles='CartoDB positron')
    choropleth = folium.Choropleth(
        geo_data='indonesia.geojson',
        data=filtered_df,
        columns=['Provinsi', 'KMeans'],
        key_on='feature.properties.state',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    df_indexed = filtered_df.set_index('Provinsi')
    for feature in choropleth.geojson.data['features']:
        state_name = feature['properties']['state']
        feature['properties']['KMeans'] = 'Cluster: ' + str(df_indexed.loc[state_name, 'KMeans']) if state_name in df_indexed.index else ''

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['state', 'KMeans'], labels=False)
    )
    st_map = st_folium(map, width=800, height=400)

# Display the filtered data in a table
# Tampilkan tabel
    st.dataframe(
        filtered_df.style.format({
            "Tahun": "{:.0f}",
            "Luas Panen": "{:.2f}",
            "Produksi": "{:.2f}",
            "Prediksi Luas Panen": "{:.2f}",
            "Prediksi Produksi": "{:.2f}"
        })
    )

#analisis data
def eda_page():

    st.title('Analisis Data Tanaman Pangan')
    # Nama tabel yang ingin digunakan
    selected_table = "tanaman_pangan"

    # Query untuk mengambil data dari tabel terpilih
    query = f"SELECT * FROM {selected_table}"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=["Provinsi", "Komoditas", "Tahun", "Luas Panen", "Produksi"])

    province = st.selectbox('Pilih Provinsi', df['Provinsi'].unique())
    selected_commodities = st.multiselect('Pilih Komoditas (Dapat Memilih 1 atau lebih)', df['Komoditas'].unique())

    # Filter data
    filtered_data = df[(df['Provinsi'] == province) & (df['Komoditas'].isin(selected_commodities))]

    # Group data by year and commodity, then sum the production
    grouped_data = filtered_data.groupby(['Tahun', 'Komoditas']).sum().reset_index()

    # Visualisasi dengan Altair (Line Chart)
    line_chart = alt.Chart(grouped_data).mark_line(point=True).encode(
        x='Tahun:N',
        y='sum(Produksi):Q',
        color='Komoditas:N'
    ).properties(
        title=f'Total Produksi'
    )
    st.altair_chart(line_chart, use_container_width=True)


    # Visualisasi dengan Altair (Clustered Bar Chart)
    chart = alt.Chart(grouped_data).mark_bar(opacity=1).encode(
        x=alt.X('Komoditas:N', axis=alt.Axis(title='Komoditas')),
        y=alt.Y('sum(Produksi):Q', axis=alt.Axis(title='Total Produksi')),
        color='Komoditas:N'
    ).properties(
        title=f'Total Produksi'
    )

    # Tambahkan label di clustered bar chart
    text = chart.mark_text(
        align='center',
        baseline='bottom',
        dx=4  # shift the text to right slightly for better visualization
    ).encode(
        text='sum(Produksi):Q'
    )
    st.altair_chart(chart + text, use_container_width=True)

    # Tampilkan tabel
    st.markdown(f'Total Produksi')
    st.dataframe(
        filtered_data.style.format({
            "Tahun": "{:.0f}",
            "Luas Panen": "{:.2f}",
            "Produksi": "{:.2f}",
        })
    )

#Prediksi Produksi
def calculator_page():
    # Title
    st.title('Kalkulator Prediksi Produksi')

    # Daftar nama tabel yang ingin ditampilkan
    table_names = ["kacang_tanah", "kacang_hijau", "ubi_jalar", "ubi_kayu", "padi", "kedelai", "jagung", "merged_all_data"]

    # Tampilkan pilihan tabel pada sidebar
    selected_table = st.selectbox("Pilih Komoditas", table_names)

    # Query untuk mengambil data dari tabel terpilih
    query = f"SELECT * FROM {selected_table}"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=["Provinsi", "Komoditas", "Tahun", "Luas Panen", "Produksi", "KMeans", "KMeans Label", "Prediksi Luas Panen", "Prediksi Produksi"])

    # Menentukan fitur yang akan digunakan untuk regresi
    X_feature = "Luas Panen"
    Y_feature = "Produksi"

    # Membuat model regresi linier
    model = LinearRegression()
    X = df[[X_feature]]
    y = df[Y_feature]
    model.fit(X, y)

    # Tampilkan input form untuk kalkulator
    luas_panen_input = st.number_input("Masukkan Luas Panen (Ha):", min_value=df[X_feature].min(), max_value=None, value=df[X_feature].mean())

    # Prediksi produksi berdasarkan luas panen
    predicted_produksi = model.predict([[luas_panen_input]])

    # Tampilkan hasil prediksi
    st.write(f"Prediksi Produksi: {predicted_produksi[0]:,.2f} ton")

#histori produksi
def chart_page():
    # Title
    st.title('Histori Produksi Tanaman Pangan')

    # Daftar nama tabel yang ingin ditampilkan
    table_names = ["kacang_tanah", "kacang_hijau", "ubi_jalar", "ubi_kayu", "padi", "kedelai", "jagung"]

    # Tampilkan pilihan tabel pada sidebar
    selected_table = st.selectbox("", table_names)

    # Query untuk mengambil data dari tabel terpilih
    query = f"SELECT * FROM {selected_table}"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=["Provinsi", "Komoditas", "Tahun", "Luas Panen", "Produksi", "KMeans", "KMeans Label", "Prediksi Luas Panen", "Prediksi Produksi"])

    # Filter provinsi
    selected_province = st.selectbox("Pilih Provinsi", df['Provinsi'].unique())

    # Filter data berdasarkan tahun
    filtered_df = df[df['Provinsi'].isin([selected_province])]

    def display_trend_chart(filtered_df):
        # Kelompokkan nilai berdasarkan tahun   
        produksi = filtered_df.groupby('Tahun')['Produksi'].sum().reset_index()
        prediksi_produksi = filtered_df.groupby('Tahun')['Prediksi Produksi'].sum().reset_index()

        fig = px.line(
            pd.concat([produksi, prediksi_produksi], keys=['Produksi', 'Prediksi Produksi']),
            x='Tahun',
            y='Produksi'
        )

        # Menambahkan garis untuk 'Produksi'
        fig.add_scatter(
            x=produksi['Tahun'],
            y=produksi['Produksi'],
            mode='lines+markers',  # Menampilkan garis tanpa markers
            name='Produksi',  # Menambahkan nama pada legend
            line=dict(color='blue'),
            marker=dict(color='blue', size=8),  # Atur warna dan tipe garis
        )

        # Menambahkan garis untuk 'Prediksi Produksi'
        fig.add_scatter(
            x=prediksi_produksi['Tahun'],
            y=prediksi_produksi['Prediksi Produksi'],
            mode='lines+markers',  # Menampilkan garis dan markers
            name='Prediksi Produksi',
            line=dict(color='orange'),  # Atur warna dan tipe garis
            marker=dict(color='orange', size=8),  # Atur warna dan ukuran markers
        )

    # Menambahkan garis miring untuk melihat tren
        fig.add_shape(
            type='line',
            x0=produksi['Tahun'].iloc[0],  # Nilai awal tahun
            y0=produksi['Produksi'].iloc[0],  # Nilai awal produksi
            x1=produksi['Tahun'].iloc[-1],  # Nilai akhir tahun
            y1=produksi['Produksi'].iloc[-1],  # Nilai akhir produksi
            name='Tren Produksi',
            line=dict(color='red', width=2, dash='dash'),  # Atur warna, lebar, dan tipe garis
        )


        # Menampilkan total produksi dan total prediksi produksi di luar grafik sebagai metrik
        total_produksi = produksi['Produksi'].sum()
        total_prediksi_produksi = prediksi_produksi['Prediksi Produksi'].sum()

        st.subheader(f"Grafik Trend {selected_table}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Total Produksi")
            st.write(f"**{total_produksi:,.2f}**")
        with col2:
            st.write(f"Total Prediksi Produksi")
            st.write(f"**{total_prediksi_produksi:,.2f}**")
        
        # Menampilkan grafik di Streamlit
        st.plotly_chart(fig)

    # Bagian pertama: Grafik


    # Tampilkan grafik trend
    display_trend_chart(filtered_df)

    # Bagian kedua: Tabel
    st.subheader(f"Tabel {selected_table}")

    # Tampilkan tabel
    st.dataframe(
        filtered_df.style.format({
            "Tahun": "{:.0f}",
            "Luas Panen": "{:.2f}",
            "Produksi": "{:.2f}",
            "Prediksi Luas Panen": "{:.2f}",
            "Prediksi Produksi": "{:.2f}"
        })
    )

#model visualisai
def plot_page():
    # Title
    st.title('Scatter Plot KMeans Clustering with Centroids')

    # Daftar nama tabel yang ingin ditampilkan
    table_names = ["kacang_tanah", "kacang_hijau", "ubi_jalar", "ubi_kayu", "padi", "kedelai", "jagung"]

    # Tampilkan pilihan tabel pada sidebar
    selected_table = st.selectbox("Pilih Tabel", table_names)

    # Query untuk mengambil data dari tabel terpilih
    query = f"SELECT * FROM {selected_table}"
    data = fetch_data(query)
    df = pd.DataFrame(data, columns=["Provinsi", "Komoditas", "Tahun", "Luas Panen", "Produksi", "KMeans", "KMeans Label", "Prediksi Luas Panen", "Prediksi Produksi"])

    # Menentukan fitur yang akan digunakan untuk clustering
    features = ["Luas Panen", "Produksi"]

    # Mendapatkan centroids berdasarkan label KMeans
    centroids = df.groupby('KMeans')[features].mean()

    # Visualisasi Scatter Plot KMeans Clustering
    fig_kmeans = px.scatter(
        df,
        x='Luas Panen',
        y='Produksi',
        color='KMeans',
        hover_data=['Provinsi', 'Tahun', 'Komoditas'],
        title='Scatter Plot KMeans Clustering'
    )

    # Menambahkan plot centroid ke scatter plot
    fig_kmeans.add_trace(
        go.Scatter(
            x=centroids[features[0]],
            y=centroids[features[1]],
            mode='markers+text',
            name='Centroid',
            legendgroup='Centroid',  # Menyamakan dengan 'name' pada scatter plot
            marker=dict(size=14, color='red', symbol='x'),
        )
    )

    # Menampilkan grafik Scatter Plot di Streamlit
    st.plotly_chart(fig_kmeans)

    st.title('Scatter Plot Linear Regression')

    # Menentukan fitur yang akan digunakan untuk regresi
    X_feature = "Luas Panen"
    Y_feature = "Produksi"

    # Memisahkan fitur dan target
    X = df[[X_feature]]
    y = df[Y_feature]

    # Membagi data menjadi data pelatihan (80%) dan data pengujian (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Membuat model regresi linier
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Memprediksi nilai Produksi untuk data pengujian
    y_pred = model.predict(X_test)

    # Visualisasi Scatter Plot KMeans Clustering
    fig_regresi = sns.lmplot(x=X_feature, y=Y_feature, data=df, aspect=2, height=6, fit_reg=False)

    # Menampilkan garis regresi pada Scatter Plot
    plt.plot(X_test, y_pred, color='red', linewidth=2)
    plt.title(f'Regresi Linier antara {X_feature} dan {Y_feature}')

    # Menampilkan grafik Scatter Plot di Streamlit
    st.pyplot(fig_regresi)

    # Mengambil subset DataFrame hanya dengan dua kolom yang diinginkan
    subset_df = df[[X_feature, Y_feature]]

    # Menghitung matriks korelasi antara dua kolom tersebut
    correlation_matrix = subset_df.corr()

    # Menampilkan matriks korelasi
    st.title('Matriks Korelasi')
    st.set_option('deprecation.showPyplotGlobalUse', False)
    sns.heatmap(correlation_matrix, annot=True, cmap='Blues', fmt=".2f")
    st.pyplot()


def selection_menu():
    with st.sidebar:
        if st.button('Log Out'):
            logout()

        selected = option_menu(
            menu_title= None, #required
            options= ["Dashboard", "Analisis Data", "Prediksi Produksi", "Histori Produksi", "Model Visualisasi"], #required
            icons = ["house", "house", "house", "house", "house"],
            menu_icon = "cast",
            default_index=0, #optional
            # orientation= "horizontal"
        )

    if selected == "Dashboard":
        dashboard_page()
    if selected == "Analisis Data":
        eda_page()
    if selected == "Prediksi Produksi":
        calculator_page()
    if selected == "Histori Produksi":
        chart_page()
    if selected == "Model Visualisasi":
        plot_page()


# Status awal login
is_authenticated = False

def main():
    global is_authenticated
    # Jika pengguna berhasil login, atur is_authenticated menjadi True
    is_authenticated = True
    selection_menu()


if __name__ == "__main__":
    if login():
        st.write("You are now logged in!")