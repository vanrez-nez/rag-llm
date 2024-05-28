from string import Template
def build_prompt(title, content):
  t = Template("""Del articulo abajo:
                Si el articulo es de Mexico:
                - Extrae la ubicacion geografica de ciudad y estado que se mencionan.
                - Si se mencionan ubicaciones diferentes crea una entrada por cada ubicacion.
                - NO agregues informacion adicional como notas o comentarios.

                Articulo:
                ```
                Titulo: $title
                Contenido: $content
                ```

                Ejemplo de respuesta:
                ```
                [
                  { "ciudad": "Morelia", "estado": "Michoacan" },
                  { "ciudad": "Tarimbaro", "estado": "Michoacan" }
                  { "ciudad": "", "estado": "Coahuila" },
                ]
                ```""")
  return t.substitute(title=title, content=content)
