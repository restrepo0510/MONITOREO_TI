"""
Utilidades de estaciones para la linea visual del dashboard.

Este modulo define el orden de estaciones y helpers para obtener
la tripleta:
- estacion anterior
- estacion actual
- estacion siguiente
"""

from typing import Dict, List


# Orden oficial para el recorrido visual del MVP.
# Al llegar al final, vuelve a iniciar en la primera estacion.
LINE_STATIONS: List[str] = [
    "Estadio do Dragao",
    "Campanha",
    "Heroismo",
    "24 de Agosto",
    "Bolhao",
    "Trindade",
    "Lapa",
    "Carolina Michaelis",
    "Casa da Musica",
    "Francos",
    "Ramalde",
    "Viso",
    "NorteShopping",
    "Sete Bicas",
    "Senhora da Hora",
    "Vasco da Gama",
    "Estadio do Mar",
    "Pedro Hispano",
    "Parque de Real",
    "Camara de Matosinhos",
    "Matosinhos Sul",
    "Brito Capelo",
    "Mercado",
    "Senhor de Matosinhos",
]


def get_station_triplet(index: int) -> Dict[str, str]:
    """
    Retorna estacion anterior/actual/siguiente para un indice dado.
    Usa aritmetica modular para reiniciar automaticamente al final.
    """
    if not LINE_STATIONS:
        return {"previous": "-", "current": "-", "next": "-"}

    n = len(LINE_STATIONS)
    i = index % n
    return {
        "previous": LINE_STATIONS[(i - 1) % n],
        "current": LINE_STATIONS[i],
        "next": LINE_STATIONS[(i + 1) % n],
    }
