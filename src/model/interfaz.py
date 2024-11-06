from flask import Flask, request, jsonify, render_template
from model.logica import AplicacionPlanificacionComidas


app = Flask(__name__, template_folder="../view/templates")
planificador = AplicacionPlanificacionComidas(
    api_key="3049b9661d644420bb03199ff64b6c9e"
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/configurar_preferencias", methods=["POST"])
def configurar_preferencias():
    preferencias = request.json["preferencias"]
    restricciones = request.json["restricciones"]
    planificador.configurar_preferencias(preferencias, restricciones)
    return jsonify({"message": "Preferencias guardadas correctamente."})


@app.route("/generar_menu", methods=["GET"])
def generar_menu():
    menu = planificador.generar_menu()
    return jsonify(menu)


@app.route("/crear_lista_compras", methods=["POST"])
def crear_lista_compras():
    menu = request.json["menu"]
    lista_compras = planificador.crear_lista_compras(menu)
    return jsonify(lista_compras)


@app.route("/ingredientes_por_dia/<dia>", methods=["GET"])
def ingredientes_por_dia(dia):
    datos = planificador.ver_ingredientes(dia)

    # Extraer solo los ingredientes de extendedIngredients
    ingredientes = [
        {
            "nombre": ingrediente["name"].capitalize(),
            "cantidad": ingrediente["amount"],
            "unidad": ingrediente["unit"].capitalize(),
        }
        for ingrediente in datos.get("extendedIngredients", [])
    ]
    return jsonify(ingredientes)


@app.route("/obtener_nutricion/<dia>", methods=["GET"])
def obtener_nutricion(dia):
    # Obtener los datos de nutrición del planificador
    datos = planificador.ver_nutricion(dia)

    # Extracción de los nutrientes relevantes
    nutrientes = {
        "calorias": datos.get("nutrients", [{}])[0].get("amount", "N/A"),
        "proteinas": datos.get("nutrients", [{}])[9].get("amount", "N/A"),
        "carbohidratos": datos.get("nutrients", [{}])[3].get("amount", "N/A"),
        "grasas": datos.get("nutrients", [{}])[1].get("amount", "N/A"),
        "fibra": datos.get("nutrients", [{}])[10].get("amount", "N/A"),
    }

    # Retornar la respuesta en formato JSON
    return jsonify(nutrientes)


@app.route("/inventario/agregar", methods=["POST"])
def agregar_inventario():
    nombre = request.json["nombre"]
    cantidad = request.json["cantidad"]
    planificador.inventario.agregar_ingrediente(nombre, cantidad)
    return jsonify({"message": f"{cantidad} de {nombre} añadido al inventario."})


@app.route("/inventario", methods=["GET"])
def ver_inventario():
    inventario = planificador.inventario.obtener_inventario()
    return jsonify(inventario)
