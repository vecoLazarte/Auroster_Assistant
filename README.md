# Chatbot---violencia-de-género
Repositorio con fines para una aplicación de IA generativa sobre noticias de violencia de género.
🧠 Agente Conversacional sobre Violencia de Género en el Perú
📌 Problemática
La violencia basada en género representa una de las formas más persistentes y sistemáticas de violación a los derechos humanos. Según el Ministerio de la Mujer y Poblaciones Vulnerables (MIMP), se trata de cualquier acción o conducta basada en el género que cause daño físico, sexual o psicológico, tanto en el ámbito público como privado.

En Perú, 7 de cada 10 mujeres han sido víctimas de algún tipo de violencia de género (Contreras, Granados & Levano, 2021), lo cual refleja una estructura social desigual profundamente arraigada.

A pesar de los esfuerzos de diversos actores (Estado, sociedad civil, medios de comunicación, instituciones educativas), los enfoques tradicionales enfrentan limitaciones importantes:

Falta de información sistematizada.

Atención inadecuada a las víctimas.

Escasa efectividad en las estrategias de prevención.

💡 Solución Propuesta
Este proyecto plantea el desarrollo de un agente conversacional que facilita el acceso a información contextualizada y actualizada sobre violencia de género en el Perú, a partir de noticias digitales obtenidas mediante técnicas de web scraping.

El agente está diseñado para:

Recuperar noticias relacionadas con violencia de género en Lima.

Procesarlas y almacenarlas usando herramientas de NLP y bases de datos vectoriales.

Proporcionar respuestas fundamentadas, precisas y adaptadas a las consultas del usuario.

📄 Datos procesados:
Noticias sobre feminicidios y otros tipos de violencia (por distrito, medio, fecha, tipo de violencia, etc.).

Fragmentación y vectorización de texto para facilitar la recuperación semántica.

Almacenamiento eficiente en una base vectorial (Elasticsearch) y base relacional (PostgreSQL).

⚙️ Tecnologías Utilizadas
Web Scraping: Extracción de noticias de medios peruanos (El Comercio, RPP, Expreso, etc.).

Fragmentación: División de textos en fragmentos pequeños y manejables.

Embeddings: text-embedding-ada-002 de OpenAI para vectorizar los textos.

Elasticsearch: Para almacenamiento y búsqueda semántica de documentos.

PostgreSQL (Cloud SQL): Para almacenar el historial de interacciones por sesión.

LangGraph: Para gestionar el flujo conversacional del sistema.

Vercel: Despliegue del frontend del agente conversacional.

Google Cloud Platform (GCP): Infraestructura para desplegar servicios como Cloud Run, Compute Engine y Cloud SQL.
