"""
backtracking.py — Algoritmo 1: backtracking con poda por cota superior.

El árbol fija una ranura por nivel, en el orden de `RANURAS`. Un nodo es una
config parcial; las ranuras sin fijar quedan **vacías** (el oráculo no pega su
texto). La cota de un nodo es la precisión de esa config parcial:

- En el oráculo sintético es exacta. Agregar una ranura solo puede romper más
  familias, nunca arreglar, así que ninguna completación supera a su prefijo.
  El backtracking devuelve entonces el óptimo de `espacio_reducido(opciones)`.
- En el oráculo real es **heurística**. Una ranura puede arreglar algo (la
  opción limpia de `cierre` repite las restricciones) y la cota puede quedar
  corta. Lo que devuelve es la mejor observada, no un óptimo garantizado.

Se poda si `cota <= mejor`: ese subárbol no puede mejorar estrictamente a la
mejor hoja vista. Los hijos se visitan de mayor a menor cota para hallar pronto
una hoja buena y podar más.

Costo: cada nodo visitado cuesta n consultas. En el peor caso (sin poda) se
visitan Σ_{d=1..5} k^d = O(k⁵) = O(|C|) nodos, es decir T = O(|C|·n).
"""

from .espacio import RANURAS, config_vacia, ordenar
from .presupuesto import PresupuestoAgotado


def backtracking(oraculo, opciones, instancias, semilla=1):
    """Explora `espacio_reducido(opciones)` con poda por la cota parcial.

    Returns
    -------
    dict
        config, precision, nodos (evaluados), podas, agotado (True si el
        presupuesto cortó la búsqueda antes de terminar).
    """
    estado = {"config": None, "precision": -1.0, "nodos": 0, "podas": 0, "agotado": False}

    def medir(config):
        estado["nodos"] += 1
        return oraculo.evaluar(config, instancias, semilla=semilla).precision

    def visitar(parcial, nivel):
        if nivel == len(RANURAS):
            return
        ranura = RANURAS[nivel]
        hijos = []
        for o in opciones[ranura]:
            hijo = {**parcial, ranura: int(o)}
            hijos.append((medir(hijo), hijo))
        hijos.sort(key=lambda par: -par[0])  # sort estable: empata por orden de opciones
        for cota, hijo in hijos:
            if cota <= estado["precision"]:
                estado["podas"] += 1
                continue
            if nivel == len(RANURAS) - 1:
                estado["config"], estado["precision"] = ordenar(hijo), cota
            else:
                visitar(hijo, nivel + 1)

    # La raíz no se mide: su cota no poda nada mientras no haya una hoja.
    try:
        visitar(config_vacia(), 0)
    except PresupuestoAgotado:
        estado["agotado"] = True
    return estado
