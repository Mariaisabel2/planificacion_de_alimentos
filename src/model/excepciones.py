# excepciones.py


class AplicacionError(Exception):
    """Excepción base para todos los errores de la aplicación."""

    pass


class PreferenciasError(AplicacionError):
    """Excepción para errores relacionados con las preferencias del usuario."""

    pass


class APIRecetasError(AplicacionError):
    """Excepción para errores relacionados con la API de recetas."""

    pass


class ListaComprasError(AplicacionError):
    """Excepción para errores en la generación de la lista de compras."""

    pass


class InventarioError(AplicacionError):
    """Excepción para errores relacionados con el inventario."""

    pass


class NutricionAPIError(AplicacionError):
    """Excepción para errores relacionados con la API de nutrición."""

    pass
