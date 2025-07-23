# utils.py - Funciones utilitarias compartidas

import os

def crear_carpeta(nombre):
    """Crea una carpeta si no existe"""
    if not os.path.exists(nombre):
        os.makedirs(nombre)

def limpiar_nombre(nombre):
    """Limpia el nombre del archivo para ser compatible con Windows/Mac/Linux"""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in nombre)
