"""
coordenadas.py — Algoritmo 3: descenso (ascenso) por coordenadas.

Se parte de una config completa y, ranura por ranura, se prueban todas sus
opciones con las otras cuatro fijas; se queda la mejor si mejora
**estrictamente**. Una iteración recorre las cinco ranuras. Para cuando una
iteración entera no cambia nada (óptimo local por coordenadas) o al llegar a
`max_iter`.

Costo: cada iteración evalúa a lo sumo Σ_r |opciones[r]| ≤ 5·k_max configs
con n0 instancias, es decir T = O(I·k_max·n0) con I iteraciones (el 5 es
constante). El caché hace que repetir la config actual no cueste.

Riesgo: el óptimo es local. Si dos ranuras solo mejoran cambiando **juntas**
(una opción de `formato` que solo deja de fallar con otro `estilo`), ningún
paso de una coordenada lo ve y el algoritmo se queda ahí. El backtracking no
tiene ese problema; por eso se comparan.
"""

from .espacio import RANURAS, TEMPERATURA, vecinos
from .presupuesto import PresupuestoAgotado


def descenso_coordenadas(oraculo, opciones, instancias, inicio=None, max_iter=10, semilla=1):
    """Mejora una ranura a la vez hasta converger o agotar `max_iter`.

    `inicio` por defecto es la primera opción conservada de cada ranura (la
    mejor del diagnóstico).

    Returns
    -------
    dict
        config, precision, iteraciones, convergio (True si paró por no haber
        cambios) y agotado.
    """
    if inicio is None:
        inicio = {r: int(opciones[r][0]) for r in RANURAS}
        inicio["temperatura"] = TEMPERATURA
    actual = dict(inicio)
    salida = {"config": actual, "precision": None, "iteraciones": 0,
              "convergio": False, "agotado": False}
    try:
        mejor = oraculo.evaluar(actual, instancias, semilla=semilla).precision
        salida["precision"] = mejor
        for it in range(1, max_iter + 1):
            salida["iteraciones"] = it
            cambio = False
            for ranura in RANURAS:
                for cand in vecinos(actual, ranura, opciones):
                    if cand[ranura] == actual[ranura]:
                        continue
                    p = oraculo.evaluar(cand, instancias, semilla=semilla).precision
                    if p > mejor:
                        actual, mejor, cambio = cand, p, True
                        salida["config"], salida["precision"] = actual, mejor
            if not cambio:
                salida["convergio"] = True
                break
    except PresupuestoAgotado:
        salida["agotado"] = True
    return salida
