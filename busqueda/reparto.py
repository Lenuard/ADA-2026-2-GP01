"""
reparto.py — Algoritmo 4: reparto uniforme frente a adaptativo con el mismo B.

- Uniforme: las |C| configs reciben m = ⌊B/|C|⌋ instancias cada una, y se
  queda la de mayor precisión. B = |C|·m.
- Adaptativo: Successive Halving con el mayor n0 tal que el costo nominal
  |C|·n0·⌈log₂|C|⌉ quepa en B. Gasta poco en las configs que caen pronto y
  mucho en las finalistas.

Con un B chico, el uniforme mide a todas con tan pocas instancias que el
todo-o-nada las empata en 0.0. El adaptativo concentra la muestra donde hace
falta. `comparar_repartos` mide qué tan buena es la ganadora de cada uno sobre
un lote de referencia que **no** se cobra, para ver la diferencia en datos.
"""

from .halving import rondas, successive_halving
from .presupuesto import OraculoContado


def reparto_uniforme(oraculo, configs, instancias, B, semilla=1):
    """Mide cada config con las mismas m = ⌊B/|C|⌋ instancias."""
    m = min(B // len(configs), len(instancias))
    if m == 0:
        raise ValueError(f"B={B} no alcanza para una instancia por config (|C|={len(configs)})")
    contado = OraculoContado(oraculo, B, "uniforme")
    mejor_p, mejor_c = -1.0, None
    for c in configs:
        p = contado.evaluar(c, instancias[:m], semilla=semilla).precision
        if p > mejor_p:
            mejor_p, mejor_c = p, dict(c)
    return {"metodo": "uniforme", "config": mejor_c, "precision": mejor_p,
            "m": m, "consultas": contado.consultas, "contador": contado}


def n0_adaptativo(n_configs, n_instancias, B):
    """Mayor n0 cuyo costo nominal cabe en B y cuya última ronda cabe en el lote."""
    R = max(rondas(n_configs), 1)
    return min(B // (n_configs * R), n_instancias // 2 ** (R - 1))


def reparto_adaptativo(oraculo, configs, instancias, B, semilla=1):
    """Successive Halving con el n0 más grande que permite B."""
    n0 = n0_adaptativo(len(configs), len(instancias), B)
    if n0 == 0:
        raise ValueError(f"B={B} no alcanza para Successive Halving con |C|={len(configs)}")
    contado = OraculoContado(oraculo, B, "adaptativo")
    r = successive_halving(contado, configs, instancias, n0, semilla=semilla)
    return {"metodo": "adaptativo", "config": r["config"], "precision": r["precision"],
            "n0": n0, "consultas": contado.consultas, "contador": contado}


def comparar_repartos(oraculo, configs, instancias, Bs, referencia=None, semilla=1):
    """Corre los dos repartos para cada B y mide a la ganadora en `referencia`.

    `referencia` por defecto es `instancias` completo. Se consulta sobre el
    oráculo sin contar, porque es la vara de medir y no parte de la búsqueda.

    Returns
    -------
    list[dict]
        Una fila por (B, método): B, metodo, config, precision_busqueda,
        precision_referencia, consultas.
    """
    referencia = instancias if referencia is None else referencia
    filas = []
    for B in Bs:
        for correr in (reparto_uniforme, reparto_adaptativo):
            try:
                r = correr(oraculo, configs, instancias, B, semilla=semilla)
            except ValueError:
                continue  # B demasiado chico para este método
            ref = oraculo.evaluar(r["config"], referencia, semilla=semilla).precision
            filas.append({"B": B, "metodo": r["metodo"], "config": r["config"],
                          "precision_busqueda": r["precision"],
                          "precision_referencia": ref, "consultas": r["consultas"]})
    return filas
