from curses import meta
from base.logger import log
from base.services import get_chroma
from base.services import get_ollama
from base.services import get_ollama_embedding_fn

def test_chroma(query: str):
  chroma_client = get_chroma()
  # ollama_client = get_ollama()
  # ollama_client("Hola, soy un bot de prueba. ¿En qué puedo ayudarte hoy?")
  embed_fn = get_ollama_embedding_fn()
  # chroma_client.delete_collection("news")
  chroma_client.reset()
  collection = chroma_client.create_collection(
    "news",
    embedding_function=embed_fn,
    # metadata={"hnsw:space": "ip"} # l2 is the default
  )
  # # log(embed_fn(["Hola, soy un bot de prueba. ¿En qué puedo ayudarte hoy?"]))

  collection.upsert(
    documents=[
      """
      Habitantes de Santa María manifiesta su respaldo a Carlos Torres Piña
  Morelia, Michoacán.-Cientos de habitantes de la tenencia de Santa María le manifestaron su respaldo al candidato a la presidencia de Morelia por la coalición Sigamos Haciendo Historia, Carlos Torres Piña, quien se perfila como el aspirante a la alcaldía capitalina con mayores posibilidades de triunfo, de acuerdo con ocho encuestas. "¡Torres Piña!, ¡Torres Piña!, ¡Torres Piña!", retumbó en el corazón de la plaza principal de Santa María, cuya estructura de cantera se pintó de los colores de Morena, el Partido del Trabajo y Verde Ecologista de México. Con banderas y entre diferentes consignas, los cientos de simpatizantes de la 4T presentes en Santa María ratificaron su respaldo a Carlos Torres Piña, así como a la candidata a diputada local por el Distrito 17, Nalleli Pedraza, la candidata a diputada federal por el Distrito 10, Carolina Rangel, y el candidato al Senado de la República por la misma coalición, Raúl Morón, quienes también estuvieron presentes en el evento. Desde ahí, Carlos Torres Piña afirmó que, con el respaldo del pueblo moreliano, la 4T afianzará el triunfo en la presidencia de la República, con la doctora Claudia Sheinbaum, en las diputaciones, tanto locales como federales, en el Senado de la República, y en la presidencia de Morelia. "Vamos por carro completo, la 4T se impondrá de manera contundente en Morelia, y juntas y juntos, recuperaremos la dignidad del pueblo moreliano", subrayó.
      """,
      """
      Invitan a egresados de la UMSNH a tramitar su e.firma
  Morelia, Michoacán.- La Universidad Michoacana de San Nicolás de Hidalgo (UMSNH) invitó a estudiantes y egresados a tramitar su e.firma para sacar su título, carta de pasante, certificado, constancia y memorándum con un solo click. Para los trámites, la Universidad instalará una oficina móvil en el edificio N ubicado en la entrada principal de Ciudad Universitaria del 20 al 24 de mayo de 9:00 a 17:00 horas. Te podría interesar: ¿Sabes dibujar? UMSNH abre primer concurso de manga, conoce los requisitos Con esta iniciativa, la UMSNH planea acelerar los procesos de emisión de documentos a través del Sistema Integral de Información Administrativa (SIIA). La e.firma garantiza que únicamente los alumnos puedan acceder a su cuenta y en tan solo unos minutos realicen el trámite oficial de la documentación que requieran desde casa, sin filas, sin costos de traslado y de forma rápida, segura y flexible. La Universidad Michoacana ve esta tecnología como un avance a la modernidad, así como en la mejora de los niveles de calidad en el servicio que brinda a la comunidad estudiantil, debido a que constantemente se requieren trámites de documentación que genera la base para desenvolverse exitosamente en sus áreas de desempeño profesional.
      """,
      """
      INE le invierte 3.5 mdp más al último debate para evitar errores previos
  El Instituto Nacional Electoral (INE) aprobó invertir 3 millones 500 mil pesos más en el último debate presidencial, programado para el 19 de mayo en el Centro Cultural Tlatelolco de la UNAM, con el fin de cumplir con los requerimientos técnicos, logísticos y de seguridad que han fallado en los primeros dos ejercicios. Este día, la Junta General Ejecutiva del INE aprobó a la Coordinación Nacional de Comunicación Social la ampliación de recursos para el tercer debate presidencial, por lo que el costo final de la producción, logística y seguridad de los tres debates ascenderá a 30 millones 987 mil 497 pesos. El Sol de México informó el 9 de marzo que el INE firmó un contrato por 11 millones de pesos con la empresa Turismo y Convenciones S.A. de C.V. para garantizar la seguridad de los tres candidatos presidenciales, así como la adecuada logística de los ejercicios; el Instituto informó también que la producción y transmisión de los debates estaría a cargo de las empresas Full Circe Media y MVS NET, servicio por el cual cobraron 16 millones 487 mil 497 pesos. El último encuentro entre Claudia Sheinbaum, candidata de la coalición Sigamos Haciendo Historia (Morena-PT-PVEM-); Xóchitl Gálvez, de la coalición Fuerza y Corazón por México (PAN-PRI-PRD), y Jorge Álvarez Máynez, de Movimiento Ciudadano, será moderado por Javier Solórzano, Luisa Cantú y Elena Arcila. El debate programado a las 20:00 horas versará sobre política social, inseguridad y crimen organizado, migración y política exterior y democracia, pluralismo y división de poderes.
      """,
      """
      Atacan a balazos a tres hombres en Lomas de Guayangareo en Morelia
  Morelia, Michoacán.- Asesinan a balazos a dos hombres en la colonia Lomas de Guayangareo, a unas cuadras de la avenida Bucareli en Morelia. Los hechos se registraron en la calle Charapan en la colonia Lomas de Guayangareo, cuando tres hombres fueron atacados a balazos. Elementos de seguridad pública se dirigieron de inmediato al lugar de los hechos, donde encontraron a dos hombres con heridas de bala, los cuales ya no contaban con signos vitales. Mientras que un tercer hombre fue localizado a unas cuadras, el cual presentaba heridas de bala por lo que fue trasladado a un hospital para atender sus heridas. Hasta el momento se desconoce la identidad de las víctimas. En el sitio ya se encuentran elementos de la Guardia Nacional, Guardia Civil, Policía Morelia, así como personal de la Unidad de Servicios Periciales y Escena del Crimen (USPEC), por lo que el área se encuentra acordonada.
      """,
      """
      Brigadistas continúan combatiendo el incendio en Pátzcuaro
  Morelia, Michoacán.- Continúan con labores para controlar incendio forestal en el cerro Burro del municipio de Pátzcuaro, así lo dio a conocer la Comisión Forestal de Michoacán (Cofom). El incendio forestal se registró desde el pasado 9 de mayo, el cual ha afectado árboles de pino y encino, y se ha intensificado debido a los fuertes vientos. Las brigadas que combaten el incendio son la Cofom, Conafor, Sembrando Vida, AgroSano, Sedena, Protección Civil, comuneros y más de 20 voluntarios. Las autoridades ambientales exhortan a que los ciudadanos eviten realizar quemas en zonas forestales, y en caso de observar un incendio forestal puede reportarse a los números telefónicos 443 847 6418, 44 33 08 2135 o 911. Hasta el momento en Michoacán se atienden cuatro incendios en los municipios de Aquila, Turicato y Coeneo.
      """
    ],
    metadatas=[
      { "location": "Morelia, Michoacán", "tag_1": "elecciones", "tag_2": "presidenciales", "tag_3": "Morelia" },
      { "location": "Morelia, Michoacán", "tag_1": "egresados", "tag_2": "UMSNH", "tag_3": "e.firma" },
      { "location": "CDMX", "tag_1": "debate", "tag_2": "presidencial", "tag_3": "INE" },
      { "location": "Morelia, Michoacán", "tag_1": "balazos", "tag_2": "Lomas de Guayangareo", "tag_3": "hombres" },
      { "location": "Pátzcuaro, Michoacán", "tag_1": "incendio", "tag_2": "forestal", "tag_3": "brigadistas" }
    ],
    ids=['id1', 'id2', 'id3', 'id4', 'id5'],
  )

  return collection.query(query_texts=[query], n_results=2)