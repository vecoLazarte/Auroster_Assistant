# 🟣 Agente especializado en el análisis exploratorio de  violencia de género en el Perú

## 📌 Problemática

La violencia basada en género representa una de las manifestaciones más persistentes y sistemáticas de violación a los derechos humanos. Según el Ministerio de la Mujer y Poblaciones Vulnerables (MIMP), esta se define como cualquier acción o conducta, basada en el género, que cause daño físico, sexual o psicológico, tanto en el ámbito público como privado. No se trata de hechos aislados, sino de expresiones de una estructura social profundamente arraigada que reproduce la desigualdad y la subordinación de las mujeres (MIMP, 2016).

A nivel global, la situación es alarmante: según la Organización Mundial de la Salud, una de cada tres mujeres ha experimentado violencia física y/o sexual en algún momento de su vida (Organización Mundial de la Salud [OMS], 2021). En el contexto peruano, el panorama es especialmente alarmante: siete de cada diez mujeres han sido víctimas de algún tipo de violencia de género, situando al país entre los más afectados a nivel mundial (Contreras, Granados & Levano, 2021).

Esta situación pone en evidencia una urgencia social y política que requiere mecanismos efectivos para visibilizar, comprender y actuar frente a este problema.

Diversos actores están involucrados en la lucha contra la violencia de género: el Estado (a través de ministerios como el MIMP), las organizaciones de la sociedad civil, los medios de comunicación, las instituciones educativas y la ciudadanía en general. Sin embargo, los enfoques tradicionales enfrentan serias limitaciones, como la falta de información sistematizada, la atención inadecuada a las víctimas, falta de acceso ágil a datos relevantes y la dificultad para interpretar datos complejos.

En este contexto, los medios de comunicación, especialmente los digitales, cumplen un rol clave en la construcción del discurso público sobre la violencia de género. La forma en que reportan estos hechos no solo contribuye a visibilizar el problema, sino también a sensibilizar a la sociedad. Sin embargo, a pesar de su importancia, la información que publican rara vez es organizada o utilizada de manera sistemática para el análisis o la toma de decisiones.

Por ello, resulta fundamental complementar estas noticias con datos estructurados provenientes de fuentes oficiales como el INEI, que permiten cuantificar con precisión los casos reportados, identificar tendencias a lo largo del tiempo y segmentar la información por región, tipo de violencia o características sociodemográficas. La combinación de ambos tipos de fuentes —noticias y datos estadísticos oficiales— permite un análisis más completo: las noticias aportan inmediatez, contexto narrativo y cobertura local, mientras que los registros del INEI y otras entidades públicas brindan rigor, trazabilidad y validez estadística. Esta integración favorece una comprensión más profunda y útil para la formulación de políticas públicas, intervenciones focalizadas y estrategias de prevención efectivas.

## 💡 Solución

Este proyecto propone el desarrollo de un **agente conversacional inteligente** orientado al análisis de la **violencia de género en el Perú**. El agente facilita el acceso a información **actualizada y contextualizada**, integrando dos fuentes principales:

- **Noticias digitales** recopiladas mediante técnicas de *web scraping*.
- **Datos estructurados** provenientes del **Instituto Nacional de Estadística e Informática (INEI)**.

Aunque el agente no realiza directamente la recolección de datos, se alimenta de una **base de conocimiento combinada** que se construyó a través de los siguientes pasos:

### 📌 Proceso de Construcción de la Base de Conocimiento

- 🔎 **Recolección de noticias** digitales sobre feminicidios y otras formas de violencia en los distritos de Lima y departamentos del Perú.
- 📊 **Incorporación de datos del INEI**, incluyendo estadísticas oficiales sobre denuncias, tipos de violencia y distribución geográfica.
- 🗂️ **Definición de metadatos clave**: título, periódico, fecha de publicación, distrito, contenido textual, departamento, palabras clave. 
- ✂️ **Fragmentación optimizada** de los textos para mejorar la comprensión semántica.
- 🔍 **Vectorización** de los fragmentos y carga en una base de datos vectorial.

### ☁️ Infraestructura en la Nube

- 🧠 Se utilizó **Google Cloud Platform (GCP)** para desplegar dos servicios principales:
  - **Elasticsearch**: almacena los vectores generados para realizar consultas semánticas.
  - **PostgreSQL**: almacena el historial de interacciones y los registros estructurados del INEI.

Esta arquitectura permite realizar consultas conversacionales que combinan datos **cualitativos** (narrativas de noticias) y **cuantitativos** (registros oficiales), generando respuestas más completas, visualizaciones dinámicas y análisis más profundos sobre la violencia de género en el país.

### ⚙️ Arquitectura 

#### 🔗 Integración LangGraph con GCP

La arquitectura del sistema combina herramientas de procesamiento de lenguaje natural, almacenamiento en la nube y servicios de despliegue para brindar un **agente conversacional inteligente en tiempo real** que analiza casos de violencia de género en el Perú.

![Arquitectura del sistema](Imagenes%20arquitectura/Stack.png)

### 🧩 Componentes y Flujo

#### 👤 Cliente
- El usuario final accede mediante autenticación con **Google OAuth**.
- Interactúa con la aplicación desplegada en **Vercel**, que sirve como capa de presentación.

#### ☁️ Aplicación principal
- **App-Violencia (Cloud Run)**: Microservicio que recibe las consultas del usuario, coordina las herramientas del backend y entrega respuestas.
- Desplegado en Google Cloud, permite escalabilidad automática y ejecución segura.

#### 🧠 Asistente conversacional
- **ChatGPT** y **LangSmith** gestionan el flujo de conversación usando **LangGraph**, manteniendo una memoria de corto plazo por sesión (short-memory).
- Se ejecutan evaluaciones, seguimiento del estado del diálogo y enrutamiento de herramientas según el tipo de pregunta.

#### 🛠️ Herramientas conectadas

- 🔎 **RAG (ElasticSearch)**: Base de datos vectorial que permite búsquedas semánticas en noticias sobre violencia de género.
- 📊 **ReportesPostgreSQL (Cloud SQL)**: Contiene los registros estructurados provenientes del INEI y otras fuentes oficiales.
- 📈 **GraficosEstadisticos (Cloud Storage)**: Servicio que genera y almacena gráficos dinámicos en tiempo real, los cuales son devueltos al usuario según su consulta.

Esta integración permite que cada sesión de usuario se ejecute en tiempo real, combinando procesamiento de lenguaje, recuperación aumentada (RAG), consulta estructurada con SQL y generación visual, todo en una arquitectura serverless sobre Google Cloud Platform.

## 1. Carga de Datos Estructurados desde el INEI

![Flujo de creación de ReportesPostgreSQL](Imagenes%20arquitectura/POSTGREST1.png)

Se parte de un archivo Excel que contiene datos estadísticos oficiales del **INEI** sobre feminicidios contra la mujer en el Perú entre **2015 y 2023**. Este archivo se procesa para:

- Crear las tablas necesarias en PostgreSQL.
- Almacenar la información estructurada en una instancia de **Cloud SQL** en **Google Cloud Platform (GCP)**.

Esto permite realizar consultas SQL eficientes y tener una fuente confiable y cuantificable de datos.

## 2. Construcción del sistema RAG con noticias digitales

En paralelo, se implementó un pipeline basado en **web scraping** para extraer noticias de medios como *Perú21, El Comercio, Correo* y *Exitosa*, enfocadas en violencia de género.

![Flujo de creación del sistema RAG](Imagenes%20arquitectura/RAG.png)

El proceso incluye:

- Extracción de noticias y metadatos (título, texto, fecha, distrito, departamento).
- Fragmentación semántica del contenido.
- Vectorización con OpenAI (`text-embedding-ada-002`).
- Enriquecimiento con palabras clave mediante técnicas de **stopwords** y **stemming**.
- Almacenamiento en una base **vectorial Elasticsearch** en GCP.

Este flujo permite consultas semánticas para responder preguntas complejas basadas en contexto textual.

