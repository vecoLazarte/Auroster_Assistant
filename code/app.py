import os
import re
from typing import TypedDict, List, Optional
from datetime import datetime, timedelta
import nltk
import matplotlib.pyplot as plt
import pandas as pd
import uuid
nltk.data.path = ["/usr/share/nltk_data"]

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import SnowballStemmer

stop_words = set(stopwords.words('spanish'))
stemmer = SnowballStemmer("spanish")
import textwrap
from google.cloud import storage
from llama_index.core.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.schema.runnable import RunnableLambda, RunnableParallel
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities.sql_database import SQLDatabase 
from langchain_community.agent_toolkits import SQLDatabaseToolkit 
from langchain_experimental.tools import PythonREPLTool
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from flask import Flask, jsonify, request, send_from_directory
from llama_index.vector_stores.elasticsearch import ElasticsearchStore as le
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
memory = MemorySaver()


os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "...."
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "gcpaiagent"
os.environ["OPENAI_API_KEY"] ="...."
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credenciales/credenciales.json"

app = Flask(__name__)

@app.route('/agent', methods=['GET'])
def main():
    #Capturamos variables enviadas
    id_agente = request.args.get('idagente')
    msg = request.args.get('msg')
    #datos de configuracion
    DB_URI = os.environ.get(
        "DB_URI",
        "postgresql://postgres:chester255@..:5432/postgres?sslmode=require"
    )
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }    
    distritos_lima = ["Ancón","Ate","Barranco","Breña","Carabayllo","Chaclacayo","Chorrillos","Cieneguilla","Comas","El Agustino",
    "Independencia","Jesús María","La Molina","La Victoria","Lince","Los Olivos","Lurigancho","Lurín","Magdalena del Mar","Miraflores","Pachacámac","Pucusana","Pueblo Libre","Puente Piedra",
    "Punta Hermosa","Punta Negra","Rímac","San Bartolo","San Borja","San Isidro","San Juan de Lurigancho","San Juan de Miraflores","San Luis","San Martín de Porres","San Miguel","Santa Anita","Santa María del Mar","Santa Rosa",
    "Santiago de Surco","Surquillo","Villa El Salvador","Villa María del Triunfo"]

    distritos_lima = distritos_lima + [distrito.upper() for distrito in distritos_lima]

    departamentos_peru = ["Amazonas","Áncash","Apurímac","Arequipa","Ayacucho","Cajamarca","Callao", "Cusco","Huancavelica","Huánuco","Ica","Junín","La Libertad","Lambayeque","Lima",
    "Loreto","Madre de Dios","Moquegua","Pasco","Piura","Puno","San Martín","Tacna","Tumbes","Ucayali"]

    departamentos_peru = departamentos_peru + [departamento.upper() for departamento in departamentos_peru]

    def buscar_ordenados(texto, lista):
        encontrados = []
        for lugar in lista:
            patron = r'\b' + re.escape(lugar) + r'\b'
            match = re.search(patron, texto)
            if match:
                encontrados.append((lugar, match.start()))
        # Ordenar por posición en el texto
        encontrados.sort(key=lambda x: x[1])
        # Aplicar .title() y eliminar duplicados preservando el orden
        vistos = set()
        resultado = []
        for nombre, _ in encontrados:
            nombre_title = nombre.title()
            if nombre_title not in vistos:
                resultado.append(nombre_title)
                vistos.add(nombre_title)
        return resultado

    llm = ChatOpenAI(temperature=0,model="gpt-4")

    class State(TypedDict):
        question: str
        inicio: Optional[str]
        fin: Optional[str]
        distrito: List[str]
        departamento: List[str]
        context: List[Document]
        keywords: List[str]
        answer: str

    db_data = SQLDatabase.from_uri('postgresql://postgres:chester255@...:5432/postgres?sslmode=disable')

    def get_schema(_):
        return db_data.get_table_info() 

    def run_query(query):
        return db_data.run(query) 

    promptsql = ChatPromptTemplate.from_template("""
    Basandonos en el esquema del conjunto de tablas siguiente, escribe una consulta SQL que responda a la pregunta del usuario:
    {schema}
    Pregunta: {question}
    Sql Query:
    """)

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema) # Usa RunnablePassthrough para agregar el esquema de la base.
        | promptsql # Le pasa el promptsql al modelo de lenguaje (el LLM) para que genere el SQL.
        | llm.bind(stop=["\nSQLResult:"]) # Se detiene cuando encuentre \nSQLResult: para no generar texto demás.
        | StrOutputParser()
    )

    promptsqlquery = ChatPromptTemplate.from_template(
        """
        Basandonos en el esquema de tabla inferior, pregunta, SQL Query y Respuesta, escribe una respuesta en lenguaje natural:
        {schema}
        Pregunta: {question}
        Sql Query: {query}
        SQL Respuesta: {response}
        """)

    full_chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=get_schema,
            response= lambda vars: run_query(vars["query"]),
        )
        | promptsqlquery
        | llm
    )

    tool_sql = full_chain.as_tool(name="busqueda_feminicidios", description="Consulta en la base de datos informacion sobre feminicidios ocurridos en departamentos y provincias del Perú")

    python_executor = PythonREPLTool()


    @tool
    def graficar_desde_texto(data: str, tipo: str = "barras") -> str:
        """
        Genera y ejecuta un gráfico en Python usando matplotlib/pandas a partir de datos en texto.
        Guarda la imagen localmente y la sube a un bucket de GCS. Devuelve la URL pública.
        """

        import_statement = textwrap.dedent("""\
        import pandas as pd
        import matplotlib.pyplot as plt
        from io import StringIO
        """)

        nombre_imagen = f"{uuid.uuid4().hex}.png"
        ruta_salida = f"./{nombre_imagen}"  # Ruta segura en Windows

        instrucciones_guardado = f'plt.savefig("{ruta_salida}")\nplt.close()'

        prompt = f"""
        Eres un generador de código Python. A partir de los siguientes datos en texto:
        {data}
        Genera un bloque de código Python usando pandas y matplotlib para crear un gráfico de tipo '{tipo}'.

        Instrucciones:
        - Usa pandas y io.StringIO para leer los datos.
        - El DataFrame debe llamarse 'df'.
        - Usa matplotlib para graficar.
        - No uses plt.show().
        - No imprimas nada.
        - Al final, guarda el gráfico como '{ruta_salida}' usando plt.savefig y luego plt.close().
        - Devuelve SOLO el código Python puro, sin explicaciones, sin comentarios, sin comillas triples.
        """

        try:
            codigo_python = llm.invoke(prompt).content.strip()

            # Si ya contiene plt.savefig, no lo añadimos
            if "plt.savefig" in codigo_python or "plt.close" in codigo_python:
                codigo_completo = import_statement + codigo_python
            else:
                codigo_completo = import_statement + codigo_python + "\n" + instrucciones_guardado

            python_executor.invoke(codigo_completo)

            if not os.path.exists(ruta_salida):
                return f"El archivo gráfico no fue generado: {ruta_salida}. Código generado:\n\n{codigo_python}"

            # Subir a GCS
            bucket_name = "mujerapp-imagenes"
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(nombre_imagen)
            blob.upload_from_filename(ruta_salida)

            # Construir URL pública
            url_publica = f"https://storage.googleapis.com/{bucket_name}/{nombre_imagen}"
            return url_publica

        except Exception as e:
            import traceback
            return f"Error al generar o subir gráfico:\n{traceback.format_exc()}"

    
    def format_docs(docs):
        return "\n\n".join(doc.get_content() for doc in docs)
    
    prompt_tiempo = ChatPromptTemplate.from_messages([
        ("system",  """Extrae todas las fechas del siguiente texto en formato YYYY/MM/DD.
                    Reglas:
                    - Si se menciona un día, mes y año como "5 de mayo de 2022" debes agregarle un dia mas a la fecha original, devuelve: 2022/05/05, 2022/05/06.
                    - Si se menciona solo un mes y año como "julio de 2022", devuelve: 2022/07/01, 2022/07/31.
                    - Si se menciona solo un año como "2022", devuelve dos fechas: 2022/01/01, 2022/12/31.
                    - Si se menciona un rango como "entre 2020 y 2022", devuelve: 2020/01/01, 2022/12/31.
                    - Si no se menciona ninguna fecha entonces regresa la palabra vacío.

                    Ejemplos:
                    Entrada: "Durante 2022 aumentaron los casos"
                    Salida: 2022/01/01, 2022/12/31

                    Entrada: "Entre 2021 y 2022 hubo más casos"
                    Salida: 2021/01/01, 2022/12/31

                    Entrada: "En mayo de 2022 ocurrieron eventos"
                    Salida: 2022/05/01, 2022/05/31

                    Entrada: "En marzo y julio del 2022"
                    Salida: 2022/03/01, 2022/07/31

                    Entrada: "El 5 de marzo del 2022"
                    Salida: 2022/03/05, 2022/03/06
     
                    Entrada: "No se menciona nada de fechas"
                    Salida: vacío

                    Extrae las fechas del siguiente texto:
                    """),
        ("human", "{input}")
    ])

    chain_tiempo = RunnableLambda(lambda x: {"input": x["question"]}) | prompt_tiempo | llm

    agent_metadata = RunnableParallel({"time": chain_tiempo})


    def extract_metadata(state: State) -> State:
        result = agent_metadata.invoke(state)
        fechas_raw = result["time"].content.strip()

        try:
            if fechas_raw.lower() == "vacío":
                inicio, fin = "", ""
            elif "," in fechas_raw:
                inicio, fin = [f.strip() for f in fechas_raw.split(',')]
            else:
                fecha = datetime.strptime(fechas_raw, "%Y/%m/%d")
                inicio = fecha.strftime("%Y/%m/%d")
                fin = (fecha + timedelta(days=1)).strftime("%Y/%m/%d")
        except Exception:
            inicio, fin = "", ""

        distrito = buscar_ordenados(state['question'], distritos_lima)
        departamento = buscar_ordenados(state['question'], departamentos_peru)

        if inicio and fin:
            state["inicio"] = inicio
            state["fin"] = fin
        if len(distrito)!= 0:
            state["distrito"] = distrito
        if len(departamento)!= 0:
            state['departamento'] = departamento

        palabras = word_tokenize(state['question'].lower())
        palabras_filtradas = [p for p in palabras if p.isalnum() and p not in stop_words]
        keys = [stemmer.stem(palabra) for palabra in palabras_filtradas]
        state['keywords'] = keys
        return state
    
    def retrieve_docs(state: State) -> State:
        must_filters = []
        if state.get("distrito"):
            must_filters.append({"terms": {"metadata.distrito.keyword": state["distrito"]}})
        if state.get("departamento"):
            must_filters.append({"terms": {"metadata.departamento.keyword": state["departamento"]}})
        if state.get("inicio") and state.get("fin"):
            must_filters.append({
                "range": {
                    "metadata.fecha_publicacion": {
                        "gte": datetime.strptime(state["inicio"], "%Y/%m/%d"),
                        "lte": datetime.strptime(state["fin"], "%Y/%m/%d")
                    }
                }
            })

        filtro = {
        "bool": {
            "must": must_filters,
            "should": [
                {"terms": {"metadata.keywords.keyword": state["keywords"]}}
            ],
            "minimum_should_match": 0 
            }
        }

        vector_store = le(
        es_url="http://....:9200",
        es_user="elastic",
        es_password='.....',
        index_name="notices"
        )

        storage_context_read = StorageContext.from_defaults(vector_store=vector_store)

        index_read = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context_read,embed_model=OpenAIEmbedding(model="text-embedding-ada-002")
        )
        retriever = index_read.as_retriever(filter=filtro, k=10)
        results = retriever.retrieve(state["question"])
        return {**state, "context": results}
    

    PROMPT_QA = ChatPromptTemplate.from_template("""
        Eres un asistente para tareas de respuesta a preguntas.
        Usa los siguientes fragmentos de contexto recuperado para responder la pregunta.
        Si no sabes la respuesta, simplemente di que no lo sabes.
        Usa un máximo de tres oraciones y mantén la respuesta concisa.
    
        Pregunta: {question}
        Contexto: {context}
        """)
    
    qa_chain = (
        {
        "context": lambda x: format_docs(x["context"]),
        "question": lambda x: x["question"],
        }
        | PROMPT_QA
        | llm
        | StrOutputParser()
    )

    @tool
    def rag_con_metadata(question: str) -> str:
        """
        Herramienta que responde preguntas sobre violencia de genero.
        """
        initial_state: State = {
            "question": question,
            "inicio": None,
            "fin": None,
            "distrito": [],
            "departamento": [],
            "context": [],
            'keywords': [],
            "answer": ""
        }
        estado_con_metadata = extract_metadata(initial_state) # todo OK ESTA ACA
        estado_con_contexto = retrieve_docs(estado_con_metadata)
        respuesta = qa_chain.invoke(estado_con_contexto)

        estado_con_contexto["answer"] = respuesta
        return respuesta
    

    general_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", f"""Eres un asistente amable y especializado en noticias sobre violencia de género ocurridas en el Perú.
                Tu objetivo es guiar al usuario de forma amigable, breve y conversacional, como si fueras un amigo experto en el tema. Sigue estos lineamientos:
                1. Saludo y contexto: Da un saludo cálido, indícale que eres un agente que cuenta con información de noticias sobre violencia de género ocurridas entre 2019 y 2025. Ademas de que solo puedes consultar en noticias que hayan ocurrido en distritos de Lima y departamentos del Perú. Y pregunta qué desea saber el usuario. 
                2. Estas noticias fueron recopiladas de medios digitales confiables y reconocidos por la ciudadanía como Peru 21, Correo, El Comercio y Exitosa.
                3. Si no sabes la respuesta, dilo con honestidad y ofrece continuar la búsqueda juntos.
                4. Si la pregunta se relaciona con violencia de género, feminicidios, abuso sexual, agresión, hostigamiento, maltrato físico o psicológico, entonces debes usar la herramienta `rag_con_metadata` para responder. 
                5. Solamente si la pregunta dice textualmente 'consulta en la base de datos de feminicidios', entonces usa la herramienta 'tool_sql'
                6. Si la pregunta se relaciona con generar un grafico, usa primero la herramient 'tool_sql' y luego 'graficar_desde_texto'.
                Es muy importante que siempre uses una herramienta.
                """),
         MessagesPlaceholder(variable_name="messages")

        ]
    )

    with ConnectionPool(
            # Example configuration
            conninfo=DB_URI,
            max_size=20,
            kwargs=connection_kwargs,
    ) as pool:
        checkpointer = PostgresSaver(pool)
        modelo = ChatOpenAI(temperature=0)
        tools = [rag_con_metadata,tool_sql,graficar_desde_texto]
        general_prompt = ChatPromptTemplate.from_messages(
            [("system", f"""Eres un asistente amable y especializado en noticias sobre violencia de género ocurridas en el Perú.
                Tu objetivo es guiar al usuario de forma amigable, breve y conversacional, como si fueras un amigo experto en el tema. Sigue estos lineamientos:
                1. Saludo y contexto: Da un saludo cálido, indícale que eres un agente que cuenta con información de noticias sobre violencia de género ocurridas entre 2019 y 2025. Ademas de que solo puedes consultar en noticias que hayan ocurrido en distritos de Lima y departamentos del Perú. Y pregunta qué desea saber el usuario. 
                2. Estas noticias fueron recopiladas de medios digitales confiables y reconocidos por la ciudadanía como Peru 21, Correo, El Comercio y Exitosa.
                3. Si no sabes la respuesta, dilo con honestidad y ofrece continuar la búsqueda juntos.
                4. Si la pregunta se relaciona con violencia de género, feminicidios, abuso sexual, agresión, hostigamiento, maltrato físico o psicológico, entonces debes usar la herramienta `rag_con_metadata` para responder. 
                5. Si la pregunta se relaciona con consultar a una base de datos, entonces usa la herramienta 'tool_sql'
                6. Si la pregunta se relaciona con generar un grafico, usa primero la herramient 'tool_sql' y luego 'graficar_desde_texto'.
                Es muy importante que siempre uses una herramienta.
                """),
            MessagesPlaceholder(variable_name="messages")])
        agent2 = create_react_agent(modelo, tools, checkpointer=checkpointer, prompt=general_prompt)
        config = {"configurable": {"thread_id": id_agente}}
        response = agent2.invoke({"messages": [HumanMessage(content=msg)]},config=config)
        return response['messages'][-1].content

if __name__ == '__main__':
    # La aplicación escucha en el puerto 8080, requerido por Cloud Run
    app.run(host='0.0.0.0', port=8080)
