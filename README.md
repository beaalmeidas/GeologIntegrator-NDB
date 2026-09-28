# Geolog Integrator
Trabalho da unidade 1 da disciplina Implementação e Gerenciamento de Bancos de Dados NoSQL, Ciência da Computação, 2026.2.

<br/>

O GeoLog é um sistema de monitoramento geoespacial de veículos que permite consultar veículos por proximidade, visualizar suas localizações em um mapa, acompanhar dados de telemetria, gerar indicadores e gráficos e simular a movimentação da frota.

<br/>

### Tecnologias utilizadas
- Python
- Streamlit: interface
- SQLite: armazenamento dos dados relacionais de motoristas e veículos.
- sqlite3: comunicação entre a aplicação Python e o SQLite.
- MongoDB: armazenamento dos dados de telemetria e informações geoespaciais.
- PyMongo: comunicação entre a aplicação Python e o MongoDB.
- Folium: criação do mapa interativo e visualização dos veículos.
- Plotly: criação dos gráficos e visualizações dos indicadores.

<br/>

---

## Como executar

**1.** Clonar o repositório
```
git clone https://github.com/beaalmeidas/GeologIntegrator-NDB.git

cd GeologIntegrator-NDB
```
<br/>

**2.** Criar e ativar o ambiente virtual
```
python -m venv venv
venv\Scripts\activate
```
<br/>

**3.** Instalar as dependências
```
pip install -r requirements.txt
```
<br/>

**4.** Executar a aplicação
```
streamlit run geolog.py
```
Após a execução, o Streamlit disponibilizará a aplicação no navegador. <br/>
Esse arquivo já faz a criação dos bancos SQLite e MongoDB.

<br/>

---

## Sumário do arquivo principal (geolog.py)
Termos de comentários, para busca de funções e seções relacionadas a partes específicas da arquitetura.
```
Setup da pagina no Streamlit

Seeds

Instanciacao do SQLite
- init_sqlite()

Instanciacao do MongoDB
- init_mongodb()

Funções: 
- buscar_veiculos_proximos()
- buscar_veiculos_sqlite()
- buscar_ultima_telemetria()
- criar_visao_unificada()
- calcular_kpis()
- simular_movimentacao()
- criar_grafico_temperatura()
- criar_grafico_status()
- criar_mapa()

App Streamlit
- Sidebar
- Exposicao dos resultados
- KPIs
- Graficos
- Join Poliglota
```

---
## Autor
Beatriz Almeida de Souza Silva <br/>
Setembro, 2026.