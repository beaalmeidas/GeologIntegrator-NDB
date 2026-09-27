import sqlite3
import random
from pymongo import MongoClient
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timezone


# SETUP DA PAGINA NO STREAMLIT -------------------------------------------
st.set_page_config(
    page_title="GeoLog",
    page_icon="🚚",
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
        "veiculo_id": 101,
        "location": {
            "type": "Point",
            "coordinates": [-34.874, -7.116]
        },
        "temperatura": 4.5,
        "velocidade": 68,
        "timestamp": "2026-09-11T10:10:00Z"
    },
    {
        "veiculo_id": 101,
        "location": {
            "type": "Point",
            "coordinates": [-34.875, -7.117]
        },
        "temperatura": 4.1,
        "velocidade": 70,
        "timestamp": "2026-09-11T10:20:00Z"
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
        "veiculo_id": 102,
        "location": {
            "type": "Point",
            "coordinates": [-34.833, -7.122]
        },
        "temperatura": -18.2,
        "velocidade": 82,
        "timestamp": "2026-09-11T10:15:00Z"
    },
    {
        "veiculo_id": 102,
        "location": {
            "type": "Point",
            "coordinates": [-34.834, -7.123]
        },
        "temperatura": -17.9,
        "velocidade": 87,
        "timestamp": "2026-09-11T10:25:00Z"
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
    },
    {
        "veiculo_id": 103,
        "location": {
            "type": "Point",
            "coordinates": [-34.951, -7.151]
        },
        "temperatura": 22.3,
        "velocidade": 10,
        "timestamp": "2026-09-11T09:55:00Z"
    },
    {
        "veiculo_id": 103,
        "location": {
            "type": "Point",
            "coordinates": [-34.952, -7.152]
        },
        "temperatura": 21.8,
        "velocidade": 15,
        "timestamp": "2026-09-11T10:05:00Z"
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

    ultimos_veiculos = {}

    for registro in resultados:
        veiculo_id = registro["veiculo_id"]

        if (
            veiculo_id not in ultimos_veiculos
            or registro["timestamp"] > ultimos_veiculos[veiculo_id]["timestamp"]
        ):
            ultimos_veiculos[veiculo_id] = registro

    return list(ultimos_veiculos.values())


def buscar_veiculos_sqlite():
    conn = sqlite3.connect("logitech.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            veiculos.id AS veiculo_id,
            veiculos.placa,
            veiculos.modelo,
            motoristas.nome AS motorista,
            motoristas.status
        FROM veiculos
        JOIN motoristas
            ON veiculos.motorista_id = motoristas.id
    """)

    resultados = cursor.fetchall()

    conn.close()

    return [dict(row) for row in resultados]


# funcao para buscar a telemetria mais recente de cada veiculo
def buscar_ultima_telemetria():
    pipeline = [
        {
            "$sort": {
                "timestamp": -1
            }
        },
        {
            "$group": {
                "_id": "$veiculo_id",
                "telemetria": {
                    "$first": "$$ROOT"
                }
            }
        }
    ]

    resultados = telemetria.aggregate(pipeline)

    return {
        resultado["_id"]: resultado["telemetria"]
        for resultado in resultados
    }


# join de veiculo e motorista
def criar_visao_unificada():
    veiculos = buscar_veiculos_sqlite()
    ultimas_telemetrias = buscar_ultima_telemetria()

    dados = []

    for veiculo in veiculos:
        veiculo_id = veiculo["veiculo_id"]

        registro = ultimas_telemetrias.get(veiculo_id)

        if registro is None:
            continue

        longitude = registro["location"]["coordinates"][0]
        latitude = registro["location"]["coordinates"][1]

        dados.append({
            "Nome do Motorista": veiculo["motorista"],
            "Placa": veiculo["placa"],
            "Última Temperatura": registro["temperatura"],
            "Velocidade": registro["velocidade"],
            "Latitude": latitude,
            "Longitude": longitude
        })

    return dados


def calcular_kpis():
    dados = criar_visao_unificada()

    total_frotas_ativas = sum(
        1 for veiculo in buscar_veiculos_sqlite()
        if veiculo["status"] == "Ativo"
    )

    temperatura_media = sum(
        registro["Última Temperatura"]
        for registro in dados
    ) / len(dados)

    alertas_velocidade = sum(
        1 for registro in dados
        if registro["Velocidade"] > 80
    )

    return (
        total_frotas_ativas,
        temperatura_media,
        alertas_velocidade
    )


def simular_movimentacao():
    ultimas_telemetrias = buscar_ultima_telemetria()

    for veiculo_id, registro in ultimas_telemetrias.items():
        longitude = registro["location"]["coordinates"][0]
        latitude = registro["location"]["coordinates"][1]

        nova_longitude = longitude + random.uniform(-0.002, 0.002)
        nova_latitude = latitude + random.uniform(-0.002, 0.002)

        nova_temperatura = registro["temperatura"] + random.uniform(-0.5, 0.5)
        nova_velocidade = max(
            0,
            registro["velocidade"] + random.randint(-5, 5)
        )

        nova_telemetria = {
            "veiculo_id": veiculo_id,
            "location": {
                "type": "Point",
                "coordinates": [
                    nova_longitude,
                    nova_latitude
                ]
            },
            "temperatura": round(nova_temperatura, 2),
            "velocidade": nova_velocidade,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        telemetria.insert_one(nova_telemetria)


def criar_grafico_temperatura():
    resultados = telemetria.find(
        {},
        {
            "_id": 0,
            "veiculo_id": 1,
            "temperatura": 1,
            "timestamp": 1
        }
    ).sort("timestamp", 1)

    dados = list(resultados)

    for registro in dados:
        registro["timestamp"] = registro["timestamp"].replace(
            "T", " "
        ).replace(
            "Z", ""
        )

    grafico = px.line(
        dados,
        x="timestamp",
        y="temperatura",
        color="veiculo_id",
        markers=True,
        title="Histórico de temperatura por veículo",
        labels={
            "timestamp": "Data e hora",
            "temperatura": "Temperatura (°C)",
            "veiculo_id": "Veículo"
        }
    )

    return grafico


def criar_grafico_status():
    veiculos = buscar_veiculos_sqlite()

    status = {}

    for veiculo in veiculos:
        situacao = veiculo["status"]

        if situacao not in status:
            status[situacao] = 0

        status[situacao] += 1

    dados = [
        {
            "Status": situacao,
            "Quantidade": quantidade
        }
        for situacao, quantidade in status.items()
    ]

    grafico = px.pie(
        dados,
        names="Status",
        values="Quantidade",
        title="Status dos motoristas"
    )

    return grafico


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
                            🚚
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

    simular = st.button(
        "🚚 Simular Movimentação",
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

if simular:
    simular_movimentacao()

    st.session_state.resultados_busca = buscar_veiculos_proximos(
        latitude,
        longitude,
        raio_km
    )

    st.session_state.busca_realizada = True


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


# KPIs -------------------------------------------------------------------
st.subheader("Indicadores")

total_frotas_ativas, temperatura_media, alertas_velocidade = calcular_kpis()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Frotas ativas",
        total_frotas_ativas
    )

with col2:
    st.metric(
        "Temperatura média",
        f"{temperatura_media:.2f} °C"
    )

with col3:
    st.metric(
        "Alertas de velocidade (80 km/h ou mais)",
        alertas_velocidade
    )


# GRAFICOS ---------------------------------------------------------------
st.subheader("Gráficos")

col1, col2 = st.columns(2)

with col1:
    grafico_temperatura = criar_grafico_temperatura()
    st.plotly_chart(
        grafico_temperatura,
        use_container_width=True
    )

with col2:
    grafico_status = criar_grafico_status()
    st.plotly_chart(
        grafico_status,
        use_container_width=True
    )


# JOIN POLIGLOTA ---------------------------------------------------------
st.subheader("Join poliglota (motorista + veículo)")

dados_unificados = criar_visao_unificada()

st.dataframe(
    dados_unificados,
    use_container_width=True
)
