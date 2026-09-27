# Geolog Integrator
Trabalho da unidade 1 da disciplina Implementação e Gerenciamento de Bancos de Dados NoSQL, Ciência da Computação, 2026.2.

<br/>

---

## Como executar

1. Pré-requisitos

É necessário ter instalado:

- Python 3.10+
- MongoDB
Git
2. Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
3. Criar e ativar o ambiente virtual

No Windows:

python -m venv venv
venv\Scripts\activate
4. Instalar as dependências
pip install -r requirements.txt
5. Iniciar o MongoDB

Certifique-se de que o serviço do MongoDB esteja em execução na porta padrão 27017.

A aplicação utiliza:

mongodb://localhost:27017/

O banco geolog_db, a coleção telemetria e o índice geoespacial 2dsphere são inicializados automaticamente pela aplicação.

O banco SQLite também é criado e populado automaticamente na primeira execução.

6. Executar a aplicação
streamlit run app.py

Após a execução, o Streamlit disponibilizará a aplicação no navegador.

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