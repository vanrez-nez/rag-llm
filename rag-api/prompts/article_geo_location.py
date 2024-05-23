from string import Template
def build_prompt(title, content):
  t = Template("""Del articulo abajo:
                - Extrae la ubicacion geografica al que pertenece el contenido.
                - Deja en blanco los campos que no puedan ser extraidos.
                - Cada valor debe referirse a una ubicacion singular.
                - No agregues informacion adicional.
                - Usa solo los campos: pais, estado, ciudad, municipio, colonia, calle, numero y lugar.

                Articulo:
                ```
                Titulo: $title
                Contenido: $content
                ```

                Estructura de respuesta:
                ```
                {
                  "pais": "Pais"
                  "estado": "Estado"
                  "ciudad": "Ciudad",
                  "municipio": "Municipio",
                  "colonia": "Colonia",
                  "calle": "Calle",
                  "numero": "Numero",
                  "lugar": "El nombre del lugar del que se habla, nombre de edificio, parque, etc."
                }
                ```""")
  return t.substitute(title=title, content=content)
