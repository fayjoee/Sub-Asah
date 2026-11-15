from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set_style("whitegrid")
BASE_DIR = Path(__file__).parent

st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")


@st.cache_data
def load_data():
    day = pd.read_csv(BASE_DIR / "main_data.csv", parse_dates=["dteday"])
    hour = pd.read_csv(BASE_DIR / "hour_data.csv", parse_dates=["dteday"])
    return day, hour


day_df, hour_df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.header("Filter Data")
tgl_min, tgl_maks = day_df["dteday"].min().date(), day_df["dteday"].max().date()
rentang = st.sidebar.date_input(
    "Rentang tanggal (Pertanyaan 1)",
    value=(tgl_min, tgl_maks),
    min_value=tgl_min,
    max_value=tgl_maks,
)
if isinstance(rentang, tuple) and len(rentang) == 2:
    tgl_awal, tgl_akhir = rentang
else:
    tgl_awal, tgl_akhir = tgl_min, tgl_maks

tahun = st.sidebar.selectbox("Tahun (Pertanyaan 2)", [2012, 2011], index=0)

# ---------------- Header ----------------
st.title("🚲 Bike Sharing Dashboard")
st.caption("Capital Bikeshare, Washington D.C. (2011-2012)")

day_f = day_df[(day_df["dteday"].dt.date >= tgl_awal) & (day_df["dteday"].dt.date <= tgl_akhir)]
if day_f.empty:
    st.warning("Tidak ada data pada rentang tanggal tersebut.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Total Penyewaan", f"{day_f['cnt'].sum():,}")
k2.metric("Rata-rata per Hari", f"{day_f['cnt'].mean():,.0f}")
k3.metric("Jumlah Hari", f"{len(day_f)}")

# ---------------- Pertanyaan 1 ----------------
st.header("Pertanyaan 1: Pengaruh Cuaca terhadap Penyewaan Harian")

cuaca_df = (
    day_f.groupby("weathersit")["cnt"]
    .agg(jumlah_hari="count", rata_rata="mean")
    .round(1)
    .sort_values("rata_rata", ascending=False)
)

col_a, col_b = st.columns([3, 2])
with col_a:
    fig, ax = plt.subplots(figsize=(8, 5))
    warna = ["#d95f02" if i == cuaca_df["rata_rata"].idxmin() else "#b0b0b0" for i in cuaca_df.index]
    sns.barplot(x=cuaca_df.index, y=cuaca_df["rata_rata"], hue=cuaca_df.index,
                palette=warna, legend=False, ax=ax)
    for i, (nilai, n) in enumerate(zip(cuaca_df["rata_rata"], cuaca_df["jumlah_hari"])):
        ax.text(i, nilai + cuaca_df["rata_rata"].max() * 0.01, f"{nilai:,.0f}\n(n = {n} hari)", ha="center")
    ax.set_ylim(0, cuaca_df["rata_rata"].max() * 1.2)
    ax.set_title("Rata-rata Penyewaan Harian Berdasarkan Kondisi Cuaca")
    ax.set_xlabel("Kondisi Cuaca")
    ax.set_ylabel("Rata-rata Penyewaan per Hari")
    st.pyplot(fig)

with col_b:
    if "Clear" in cuaca_df.index:
        rata_cerah = cuaca_df.loc["Clear", "rata_rata"]
        cuaca_df["selisih_vs_cerah_%"] = ((cuaca_df["rata_rata"] - rata_cerah) / rata_cerah * 100).round(1)
    st.dataframe(cuaca_df)
    st.caption("Kategori dengan hari sedikit perlu dibaca hati-hati.")

# Analisis lanjutan: binning suhu
st.subheader("Analisis Lanjutan: Kategori Suhu")
day_f = day_f.assign(
    kategori_suhu=pd.cut(
        day_f["temp"],
        bins=[-float("inf"), 10, 20, 28, float("inf")],
        labels=["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-28°C)", "Panas (>28°C)"],
        right=False,
    )
)
suhu_df = day_f.groupby("kategori_suhu", observed=True)["cnt"].mean().round(1)
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(x=suhu_df.index, y=suhu_df.values, color="#4c78a8", ax=ax)
ax.set_title("Rata-rata Penyewaan Harian per Kategori Suhu")
ax.set_xlabel("Kategori Suhu")
ax.set_ylabel("Rata-rata Penyewaan per Hari")
st.pyplot(fig)

# ---------------- Pertanyaan 2 ----------------
st.header(f"Pertanyaan 2: Pola Penyewaan per Jam ({tahun})")

hour_f = hour_df[hour_df["yr"] == tahun].copy()
hour_f["tipe_hari"] = hour_f["workingday"].map({1: "Hari Kerja", 0: "Akhir Pekan/Libur"})
pola_jam = hour_f.pivot_table(index="hr", columns="tipe_hari", values="cnt", aggfunc="mean").round(1)

fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=pola_jam, dashes=False, markers=True, ax=ax)
for kolom in pola_jam.columns:
    jam = pola_jam[kolom].idxmax()
    ax.annotate(f"Puncak jam {jam}:00\n({pola_jam[kolom].max():.0f})",
                (jam, pola_jam[kolom].max()), textcoords="offset points", xytext=(10, 8))
ax.set_xticks(range(0, 24))
ax.set_ylim(0, pola_jam.max().max() * 1.2)
ax.set_title(f"Rata-rata Penyewaan per Jam: Hari Kerja vs Akhir Pekan/Libur ({tahun})")
ax.set_xlabel("Jam")
ax.set_ylabel("Rata-rata Penyewaan per Jam")
ax.legend(title="Tipe Hari")
st.pyplot(fig)

rata_total = hour_f.groupby("tipe_hari")["cnt"].mean()
m1, m2, m3 = st.columns(3)
m1.metric("Rata-rata/jam Hari Kerja", f"{rata_total['Hari Kerja']:.1f}")
m2.metric("Rata-rata/jam Akhir Pekan/Libur", f"{rata_total['Akhir Pekan/Libur']:.1f}")
m3.metric("Selisih", f"{rata_total['Hari Kerja'] - rata_total['Akhir Pekan/Libur']:.1f}")

# Analisis lanjutan: manual grouping jam
st.subheader("Analisis Lanjutan: Kelompok Waktu")
hour_f["kelompok_waktu"] = pd.cut(
    hour_f["hr"],
    bins=[-1, 5, 10, 14, 18, 23],
    labels=["Dini hari (00-05)", "Pagi (06-10)", "Siang (11-14)", "Sore (15-18)", "Malam (19-23)"],
)
waktu_df = hour_f.pivot_table(index="kelompok_waktu", columns="tipe_hari", values="cnt",
                              aggfunc="mean", observed=True).round(1)
fig, ax = plt.subplots(figsize=(10, 4))
waktu_df.plot(kind="bar", ax=ax, color=["#4c78a8", "#f58518"])
ax.set_title(f"Rata-rata Penyewaan per Kelompok Waktu ({tahun})")
ax.set_xlabel("Kelompok Waktu")
ax.set_ylabel("Rata-rata Penyewaan per Jam")
ax.tick_params(axis="x", rotation=0)
st.pyplot(fig)

st.caption("Sumber data: Fanaee-T & Gama (2013), Bike Sharing Dataset.")
