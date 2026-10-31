"""
halving.py — Algoritmo 2: Successive Halving.

Ronda r = 0, 1, …, R−1 con R = ⌈log₂|C|⌉: cada sobreviviente se mide con
n_r = n0·2^r instancias, y pasa la mejor mitad (redondeando hacia arriba). Las
configs malas se descartan con pocas instancias y el presupuesto se gasta en
distinguir a las buenas, que es donde el todo-o-nada necesita muestra.

Las instancias de cada ronda son un **prefijo** de las de la siguiente: los
sobrevivientes se comparan siempre sobre el mismo lote. Por eso hay dos cuentas:

- nominal: Σ_r |S_r|·n_r. Si |C| es potencia de 2, es exactamente
  |C|·n0·log₂|C|, porque cada ronda cuesta |S_r|·n_r = (|C|/2^r)·n0·2^r = |C|·n0.
- real: lo que cobra `OraculoContado`. Es menor, porque las primeras n_{r−1}
  instancias de un sobreviviente ya estaban pagadas.
"""

import math

from .presupuesto import PresupuestoAgotado


def rondas(n_configs):
    """R = ⌈log₂|C|⌉; 0 si hay una sola config."""
    return math.ceil(math.log2(n_configs)) if n_configs > 1 else 0


def successive_halving(oraculo, configs, instancias, n0, semilla=1):
    """Devuelve la sobreviviente y las cuentas para contrastar con la fórmula.

    Returns
    -------
    dict
        config, precision (de la ganadora en su última ronda), rondas,
        consultas_nominales, consultas_formula (|C|·n0·log₂|C|), historia
        (sobrevivientes y n por ronda) y agotado.
    """
    vivos = [dict(c) for c in configs]
    R = rondas(len(vivos))
    n_max = n0 * 2 ** (R - 1) if R else n0
    if n_max > len(instancias):
        raise ValueError(
            f"la última ronda pide {n_max} instancias y hay {len(instancias)}: baje n0"
        )

    salida = {
        "config": vivos[0] if len(vivos) == 1 else None,
        "precision": None,
        "rondas": R,
        "consultas_nominales": 0,
        "consultas_formula": len(configs) * n0 * math.log2(len(configs)) if configs else 0,
        "historia": [],
        "agotado": False,
    }
    try:
        for r in range(R):
            n_r = n0 * 2 ** r
            lote = instancias[:n_r]
            puntajes = [
                (oraculo.evaluar(c, lote, semilla=semilla).precision, c) for c in vivos
            ]
            salida["consultas_nominales"] += len(vivos) * n_r
            # sort estable: a igual precisión pasa la que venía antes.
            puntajes.sort(key=lambda par: -par[0])
            vivos = [c for _, c in puntajes[: math.ceil(len(vivos) / 2)]]
            salida["historia"].append({"ronda": r, "n": n_r, "evaluadas": len(puntajes)})
            salida["config"], salida["precision"] = puntajes[0][1], puntajes[0][0]
    except PresupuestoAgotado:
        salida["agotado"] = True
    return salida
