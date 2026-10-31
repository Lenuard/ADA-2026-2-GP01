"""
demo.py — los cuatro algoritmos en CPU, sobre el oráculo sintético.

    python demo.py

No necesita GPU, torch ni red: usa `busqueda.sintetico.OraculoSintetico`
(semilla 3, 10% de ruido) en lugar del LLM. La salida es determinista; la
salida esperada está en el README.
"""

import sys

from busqueda import (
    OraculoContado,
    backtracking,
    comparar_repartos,
    descenso_coordenadas,
    diagnosticar,
    espacio_reducido,
    successive_halving,
)
from busqueda.sintetico import OraculoSintetico

SEMILLA_MUNDO = 3
RUIDO = 0.1
K = 2
N_DIAG = 50
N0 = 3
B = 3200


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # consolas de Windows en cp1252

    oraculo = OraculoSintetico(semilla=SEMILLA_MUNDO, ruido=RUIDO)
    inst = oraculo.datos
    print(f"oráculo sintético: semilla {SEMILLA_MUNDO}, ruido {RUIDO:.0%}, "
          f"{len(inst)} instancias de búsqueda, {len(oraculo.validacion)} de validación\n")

    # (a) diagnóstico por trazas
    opciones, tabla = diagnosticar(oraculo, inst[:N_DIAG], k=K)
    print(f"(a) diagnóstico con {N_DIAG} instancias, k={K}")
    for ranura, ops in opciones.items():
        print(f"    {ranura:10} conserva {ops}")
    descartes = [f for f in tabla if not f["conservada"]]
    print(f"    {len(descartes)} opciones descartadas; ejemplo: "
          f"{descartes[0]['ranura']} {descartes[0]['opcion']} → {descartes[0]['motivo']}")
    C = espacio_reducido(opciones)
    print(f"    espacio: 32768 → {len(C)} configs\n")

    # (b) los algoritmos, cada uno con su contador
    print(f"(b) algoritmos sobre C' con {len(inst)} instancias, B={B} por algoritmo")
    cont = OraculoContado(oraculo, B, "backtracking")
    r = backtracking(cont, opciones, inst)
    print(f"    Alg. 1 backtracking        {r['precision']:6.1%}  consultas {cont.consultas:5}  "
          f"nodos {r['nodos']}, podas {r['podas']}")
    finales = [("backtracking", r["config"])]

    cont = OraculoContado(oraculo, B, "successive_halving")
    r = successive_halving(cont, C, inst, N0)
    print(f"    Alg. 2 successive halving  {r['precision']:6.1%}  consultas {cont.consultas:5}  "
          f"(precisión en {r['historia'][-1]['n']} inst) nominales {r['consultas_nominales']} = |C|·n0·log2|C| = {r['consultas_formula']:.0f}")
    finales.append(("successive_halving", r["config"]))

    cont = OraculoContado(oraculo, B, "coordenadas")
    r = descenso_coordenadas(cont, opciones, inst)
    print(f"    Alg. 3 coordenadas         {r['precision']:6.1%}  consultas {cont.consultas:5}  "
          f"iteraciones {r['iteraciones']}, convergió {r['convergio']}")
    finales.append(("coordenadas", r["config"]))

    print("    Alg. 4 reparto (precisión de la ganadora en las 100 instancias)")
    print("        B     uniforme  adaptativo")
    filas = comparar_repartos(oraculo, C, inst, [160, 480, 960, 1600])
    for B_i in sorted({f["B"] for f in filas}):
        p = {f["metodo"]: f["precision_referencia"] for f in filas if f["B"] == B_i}
        print(f"     {B_i:5}    {p.get('uniforme', float('nan')):6.1%}     {p.get('adaptativo', float('nan')):6.1%}")

    # (c) mejor observada y (d) validación
    medidas = [(n, c, oraculo.evaluar(c, inst).precision) for n, c in finales]
    nombre, mejor, p = max(medidas, key=lambda m: m[2])
    print(f"\n(c) mejor observada ({nombre}): {mejor}  búsqueda {p:.1%}")
    print("(d) ", end="")
    oraculo.validar(mejor, top=3)


if __name__ == "__main__":
    main()
