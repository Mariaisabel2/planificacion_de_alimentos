import requests
import json
import urllib3
from model.excepciones import (
    PreferenciasError,
    APIRecetasError,
    ListaComprasError,
    InventarioError,
    NutricionAPIError,
)

urllib3.disable_warnings()


class PreferenciasUsuario:
    """Clase para gestionar las preferencias y restricciones alimenticias del usuario."""

    def __init__(self, preferencias=None, restricciones=None):
        self.preferencias = preferencias or []
        self.restricciones = restricciones or []

    def agregar_preferencia(self, preferencia):
        self.preferencias.append(preferencia)

    def agregar_restriccion(self, restriccion):
        self.restricciones.append(restriccion)

    def guardar_preferencias(self):
        try:
            with open("data/preferencias.json", "w") as file:
                json.dump(
                    {
                        "preferencias": self.preferencias,
                        "restricciones": self.restricciones,
                    },
                    file,
                )
        except IOError:
            raise PreferenciasError("Error al guardar las preferencias del usuario.")

    def cargar_preferencias(self):
        try:
            with open("data/preferencias.json", "r") as file:
                data = json.load(file)
                self.preferencias = data.get("preferencias", [])
                self.restricciones = data.get("restricciones", [])
        except FileNotFoundError:
            raise PreferenciasError("No se encontraron preferencias guardadas.")
        except IOError:
            raise PreferenciasError("Error al cargar las preferencias del usuario.")


class APIRecetas:
    """Clase para interactuar con la API de recetas y obtener información de las mismas."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.spoonacular.com/recipes/complexSearch"

    def obtener_recetas(self, preferencias, restricciones):
        """Obtiene una lista de recetas basadas en preferencias y restricciones."""
        params = {
            "diet": ",".join(preferencias),  # Preferencias de dieta
            "intolerances": ",".join(restricciones),  # Restricciones de intolerancia
            "apiKey": self.api_key,  # Clave API
            "number": 7,  # Número de recetas a obtener
        }
        try:
            response = requests.get(self.url, params=params, verify=False)
            response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx
            return response.json().get("results", [])  # Devuelve solo los resultados
        except requests.exceptions.RequestException as e:
            raise APIRecetasError(f"Error al conectar con la API de recetas: {e}")

    def obtener_detalles_receta(self, recipe_id):
        """Obtiene los detalles completos de una receta, incluidos los ingredientes."""
        url_detalles = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        try:
            response = requests.get(
                url_detalles, params={"apiKey": self.api_key}, verify=False
            )
            response.raise_for_status()
            return response.json()  # Devuelve los detalles de la receta
        except requests.exceptions.RequestException as e:
            raise APIRecetasError(f"Error al conectar con la API de recetas: {e}")


class GeneradorMenu:
    """Genera un menú semanal basado en preferencias y restricciones."""

    def __init__(self, preferencias, restricciones, api_recetas):
        self.api_recetas = api_recetas
        self.preferencias = preferencias
        self.restricciones = restricciones
        self.menu = {}

    def generar_menu_semanal(self):
        recetas = self.api_recetas.obtener_recetas(
            self.preferencias, self.restricciones
        )
        for i, receta in enumerate(recetas):
            if "title" in receta and "id" in receta:
                self.menu[str(i + 1)] = {  # Cambiado a str para la clave
                    "title": receta["title"],
                    "id": receta["id"],
                }
            else:
                raise APIRecetasError(f"Receta inválida en Día {i + 1}: {receta}")
        return self.menu


class ListaCompras:
    """Genera y muestra una lista de compras basada en el menú semanal."""

    def __init__(self):
        self.lista = {}

    def generar_lista_compras(self, menu, api_recetas):
        for dia, receta in menu.items():
            ingredientes = []
            detalles_receta = api_recetas.obtener_detalles_receta(receta["id"])
            if detalles_receta:
                for ing in detalles_receta.get("extendedIngredients", []):
                    ingredientes.append((ing["name"], ing["amount"], ing["unit"]))
            else:
                raise ListaComprasError(
                    f"No se pudo obtener detalles para la receta {receta['id']}."
                )
            self.lista[dia] = ingredientes
        return self.lista

    def obtener_ingredientes_por_dia(self, dia):
        """Devuelve la lista de ingredientes para un día específico."""
        return self.lista.get(dia, [])


class Inventario:
    """Clase para gestionar el inventario de ingredientes del usuario."""

    def __init__(self):
        self.ingredientes = {}

    def agregar_ingrediente(self, nombre, cantidad):
        if nombre in self.ingredientes:
            self.ingredientes[nombre] += cantidad
        else:
            self.ingredientes[nombre] = cantidad

    def usar_ingrediente(self, nombre, cantidad):
        if nombre not in self.ingredientes:
            raise InventarioError("Ingrediente no encontrado en inventario.")
        if self.ingredientes[nombre] < cantidad:
            raise InventarioError("No hay suficiente cantidad en el inventario.")
        self.ingredientes[nombre] -= cantidad

    def obtener_inventario(self):
        """Devuelve el inventario actual de ingredientes y sus cantidades."""
        return self.ingredientes


class API_Nutricion:
    """Obtiene información nutricional de una receta específica."""

    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.spoonacular.com/recipes/{id}/nutritionWidget.json"

    def obtener_nutricion(self, recipe_id):
        try:
            response = requests.get(
                self.url.format(id=recipe_id),
                params={"apiKey": self.api_key},
                verify=False,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise NutricionAPIError(f"Error al conectar con la API de nutrición: {e}")


class VisualizadorNutricion:
    """Visualiza el desglose nutricional de una receta específica en el menú."""

    def __init__(self, api_nutricion):
        self.api_nutricion = api_nutricion

    def obtener_nutricion(self, menu, dia):  # Convertimos el día a cadena
        if dia in menu:
            receta_id = menu[dia]["id"]
            return self.api_nutricion.obtener_nutricion(receta_id)
        return None


class AplicacionPlanificacionComidas:
    """Clase principal que gestiona el flujo de la aplicación de planificación de comidas."""

    def __init__(self, api_key):
        self.preferencias_usuario = PreferenciasUsuario()
        self.api_recetas = APIRecetas(api_key)
        self.generador_menu = None
        self.lista_compras = ListaCompras()
        self.inventario = Inventario()
        self.api_nutricion = API_Nutricion(api_key)
        self.visualizador_nutricion = VisualizadorNutricion(self.api_nutricion)

    def configurar_preferencias(self, preferencias, restricciones):
        self.preferencias_usuario.preferencias = preferencias
        self.preferencias_usuario.restricciones = restricciones
        self.preferencias_usuario.guardar_preferencias()

    def generar_menu(self):
        self.generador_menu = GeneradorMenu(
            self.preferencias_usuario.preferencias,
            self.preferencias_usuario.restricciones,
            self.api_recetas,
        )
        return self.generador_menu.generar_menu_semanal()

    def crear_lista_compras(self, menu):
        return self.lista_compras.generar_lista_compras(menu, self.api_recetas)

    def obtener_ingredientes_por_dia(self, dia):
        return self.lista_compras.obtener_ingredientes_por_dia(dia)

    def obtener_inventario(self):
        return self.inventario.obtener_inventario()

    def agregar_ingrediente_inventario(self, nombre, cantidad):
        self.inventario.agregar_ingrediente(nombre, cantidad)

    def usar_ingrediente_inventario(self, nombre, cantidad):
        self.inventario.usar_ingrediente(nombre, cantidad)

    def obtener_nutricion(self, menu, dia):
        return self.visualizador_nutricion.obtener_nutricion(menu, dia)

    def ver_ingredientes(self, dia):
        if dia in self.generador_menu.menu:
            recipe_id = self.generador_menu.menu[dia]["id"]
            return self.api_recetas.obtener_detalles_receta(recipe_id)
        else:
            return None

    def ver_nutricion(self, dia):
        if dia in self.generador_menu.menu:
            recipe_id = self.generador_menu.menu[dia]["id"]
            return self.api_nutricion.obtener_nutricion(recipe_id)
        else:
            return None
