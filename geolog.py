import sqlite3
from pymongo import MongoClient
import streamlit as st
import folium
from streamlit_folium import st_folium


# SETUP DA PAGINA NO STREAMLIT -------------------------------------------
st.set_page_config(
    page_title="GeoLog",
    page_icon="🚗",
    layout="wide"
)


# SEEDS ------------------------------------------------------------------
MOTORISTAS = [
    (1, "Carlos Andrade", "123456789", "Ativo"),
    (2, "Mariana Silva", "987654321", "Ativo"),
    (3, "Roberto Souza", "456789123", "Em Descanso")
]

VEICULOS = [
    (101, "ABC-1A23", "Volvo FH 540", 1),
    (102, "XYZ-9876", "Scania R450", 2),
    (103, "KGB-4567", "Mercedes Actros", 3)
]

TELEMETRIA_SEED = [
    {
        "veiculo_id": 101,
        "location": {
            "type": "Point",
            "coordinates": [-34.873, -7.115]
        },
        "temperatura": 4.2,
        "velocidade": 65,
        "timestamp": "2026-09-11T10:00:00Z"
    },
    {
        "veiculo_id": 102,
        "location": {
            "type": "Point",
            "coordinates": [-34.832, -7.121]
        },
        "temperatura": -18.5,
        "velocidade": 85,
        "timestamp": "2026-09-11T10:05:00Z"
    },
    {
        "veiculo_id": 103,
        "location": {
            "type": "Point",
            "coordinates": [-34.950, -7.150]
        },
        "temperatura": 22.0,
        "velocidade": 0,
        "timestamp": "2026-09-11T09:45:00Z"
    }
]


# INSTANCIACAO DO SQLITE -------------------------------------------------
def init_sqlite():
    conn = sqlite3.connect("logitech.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motoristas (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cnh TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY,
            placa TEXT NOT NULL,
            modelo TEXT NOT NULL,
            motorista_id INTEGER,
            FOREIGN KEY (motorista_id) REFERENCES motoristas(id)
        )
    """)

    cursor.executemany("""
        INSERT OR IGNORE INTO motoristas
        (id, nome, cnh, status)
        VALUES (?, ?, ?, ?)
    """, MOTORISTAS)

    cursor.executemany("""
        INSERT OR IGNORE INTO veiculos
        (id, placa, modelo, motorista_id)
        VALUES (?, ?, ?, ?)
    """, VEICULOS)

    conn.commit()
    conn.close()


# INSTANCIACAO DO MONGODB ------------------------------------------------
def init_mongodb():
    client = MongoClient("mongodb://localhost:27017/")

    db = client["geolog_db"]
    telemetria = db["telemetria"]

    telemetria.create_index(
        [("location", "2dsphere")]
    )

    if telemetria.count_documents({}) == 0:
        telemetria.insert_many(TELEMETRIA_SEED)

    return client, telemetria


init_sqlite()
client, telemetria = init_mongodb()


# FUNCOES ----------------------------------------------------------------
def buscar_veiculos_proximos(latitude, longitude, raio_km):
    raio_metros = raio_km * 1000

    resultados = telemetria.find({
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "$maxDistance": raio_metros
            }
        }
    })

    return list(resultados)


def criar_mapa(latitude, longitude, raio_km=None, resultados=None):
    mapa = folium.Map(
        location=[latitude, longitude],
        zoom_start=12
    )

    if resultados is not None:
        folium.Marker(
            [latitude, longitude],
            tooltip="Ponto de referência",
            icon=folium.Icon(
                color="blue",
                icon="search",
                prefix="fa"
            )
        ).add_to(mapa)

        folium.Circle(
            radius=raio_km * 1000,
            location=[latitude, longitude],
            tooltip=f"Raio de busca: {raio_km} km",
            fill=True
        ).add_to(mapa)

        for registro in resultados:
            longitude_veiculo = registro["location"]["coordinates"][0]
            latitude_veiculo = registro["location"]["coordinates"][1]

            folium.Marker(
                [latitude_veiculo, longitude_veiculo],
                tooltip=f"Veículo {registro['veiculo_id']}",
                popup=(
                    f"Temperatura: {registro['temperatura']} °C<br>"
                    f"Velocidade: {registro['velocidade']} km/h"
                ),
                icon=folium.DivIcon(
                    html="""
                        <div style="
                            font-size: 28px;
                            text-align: center;
                        ">
                            🚗
                        </div>
                    """
                )
            ).add_to(mapa)

    return mapa

# APP STREAMLIT ----------------------------------------------------------
if "resultados_busca" not in st.session_state:
    st.session_state.resultados_busca = None

if "busca_realizada" not in st.session_state:
    st.session_state.busca_realizada = False


with st.sidebar:
    st.markdown(
        '<h1 style="font-size: 60px; margin-top: -50px">GeoLog</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size: 15px; margin-top: -12px">Sistema de Monitoramento Geoespacial e Persistência Poliglota</p>',
        unsafe_allow_html=True,
    )

    st.header("Busca por proximidade")

    latitude = st.number_input(
        "Latitude",
        value=-7.115,
        format="%.6f"
    )

    longitude = st.number_input(
        "Longitude",
        value=-34.873,
        format="%.6f"
    )

    raio_km = st.number_input(
        "Raio de busca (km)",
        min_value=1.0,
        max_value=100.0,
        value=5.0,
        step=1.0
    )

    buscar = st.button(
        "🔎 Buscar veículos",
        use_container_width=True
    )

    limpar = st.button(
        "🗑️ Limpar busca",
        use_container_width=True
    )


if buscar:
    st.session_state.resultados_busca = buscar_veiculos_proximos(
        latitude,
        longitude,
        raio_km
    )

    st.session_state.busca_realizada = True


if limpar:
    st.session_state.resultados_busca = None
    st.session_state.busca_realizada = False


if st.session_state.busca_realizada:
    resultados = st.session_state.resultados_busca

    mapa = criar_mapa(
        latitude,
        longitude,
        raio_km,
        resultados
    )

else:
    resultados = None

    mapa = criar_mapa(
        -7.115,
        -34.873
    )

st_folium(
    mapa,
    width=None,
    height=530
)

if st.session_state.busca_realizada:
    st.subheader("Resultado da busca")

    st.write(
        f"Veículos encontrados: {len(resultados)}"
    )