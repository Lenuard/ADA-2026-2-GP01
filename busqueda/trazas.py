"""
trazas.py — diagnóstico por ranura a partir de las trazas de fallo.

Cada opción se mide **sola**: su ranura con esa opción y las otras cuatro
vacías. Comparada contra la config vacía, la diferencia de precisión y las
familias `violo` que aparecen de más dicen qué superficie de la respuesta
rompe esa opción. Con eso se descartan opciones antes de combinar, y el espacio
pasa de 8⁵ a k⁵ configs.

Es una heurística: mide efectos aislados y no ve interacciones entre ranuras
(dos opciones inofensivas solas pueden chocar juntas). Por eso se conservan
k > 1 opciones por ranura y los algoritmos combinan sobre lo que queda.
"""

from collections import Counter

from .espacio import N_OPCIONES, RANURAS, config_vacia


def _familias(resultado):
    return Counter(t["violo"] for t in resultado.trazas)


def diagnosticar(oraculo, instancias, k=2, semilla=1, n_opciones=N_OPCIONES):
    """Evalúa la base y cada opción sola; conserva las `k` mejores por ranura.

    Orden de mérito: mayor precisión, luego menos fallos de más frente a la
    base, luego índice menor (para que el desempate sea reproducible).

    Costo: (1 + 5·n_opciones) configs × len(instancias) consultas.

    Returns
    -------
    opciones : dict
        ranura → lista de los `k` índices conservados, del mejor al peor.
    tabla : list[dict]
        Una fila por opción: ranura, opcion, precision, delta (contra la base),
        familias_de_mas (las 3 que más subieron), conservada y motivo.
    """
    base = oraculo.evaluar(config_vacia(), instancias, semilla=semilla)
    fam_base = _familias(base)

    opciones, tabla = {}, []
    for ranura in RANURAS:
        filas = []
        for o in range(n_opciones):
            r = oraculo.evaluar({ranura: o, **config_vacia()}, instancias, semilla=semilla)
            de_mas = _familias(r) - fam_base  # Counter descarta los ≤ 0
            filas.append({
                "ranura": ranura,
                "opcion": o,
                "precision": r.precision,
                "delta": r.precision - base.precision,
                "fallos_de_mas": sum(de_mas.values()),
                "familias_de_mas": de_mas.most_common(3),
            })
        filas.sort(key=lambda f: (-f["precision"], f["fallos_de_mas"], f["opcion"]))
        opciones[ranura] = [f["opcion"] for f in filas[:k]]
        corte = filas[k - 1]["precision"] if k <= len(filas) else 0.0
        for i, f in enumerate(filas):
            f["conservada"] = i < k
            f["motivo"] = _motivo(f, corte)
        tabla.extend(sorted(filas, key=lambda f: f["opcion"]))
    return opciones, tabla


def _motivo(fila, corte):
    """Texto corto de por qué se conservó o descartó la opción."""
    fams = ", ".join(f"{fam} (+{n})" for fam, n in fila["familias_de_mas"]) or "ninguna"
    if fila["conservada"]:
        return f"conservada; familias de más: {fams}"
    if fila["precision"] < corte:
        return f"descartada: precisión {fila['precision']:.1%} < corte {corte:.1%}; rompe {fams}"
    return f"descartada por desempate (más fallos de más); rompe {fams}"
