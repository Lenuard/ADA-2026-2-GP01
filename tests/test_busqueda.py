"""
Pruebas de la solución base, sobre el oráculo sintético con semillas fijas.

    python -m pytest tests/ -v
"""

import json
import math
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from busqueda import (  # noqa: E402
    RANURAS,
    OraculoContado,
    PresupuestoAgotado,
    backtracking,
    descenso_coordenadas,
    diagnosticar,
    espacio_reducido,
    reparto_adaptativo,
    reparto_uniforme,
    successive_halving,
    validar_config,
    validar_entrega,
)
from busqueda.sintetico import OraculoSintetico, generar_instancias  # noqa: E402


@pytest.fixture
def oraculo():
    return OraculoSintetico(semilla=0)


@pytest.fixture
def sin_limpia(oraculo):
    """Dos opciones por ranura, ninguna limpia: el óptimo no es trivial."""
    return {r: [o for o in range(8) if o != oraculo._limpia[r]][:2] for r in RANURAS}


def _correr_todos(oraculo, opciones, B=10_000):
    inst = oraculo.datos
    C = espacio_reducido(opciones)
    return {
        "backtracking": backtracking(OraculoContado(oraculo, B), opciones, inst),
        "halving": successive_halving(OraculoContado(oraculo, B), C, inst, n0=3),
        "coordenadas": descenso_coordenadas(OraculoContado(oraculo, B), opciones, inst),
        "uniforme": reparto_uniforme(oraculo, C, inst, B=960),
        "adaptativo": reparto_adaptativo(oraculo, C, inst, B=960),
    }


# ---- la salida respeta las restricciones del problema ----------------

def test_configs_de_los_algoritmos_son_validas(oraculo, sin_limpia):
    for nombre, r in _correr_todos(oraculo, sin_limpia).items():
        c = r["config"]
        assert set(c) == set(RANURAS) | {"temperatura"}, nombre
        assert all(isinstance(c[k], int) and 0 <= c[k] < 8 for k in RANURAS), nombre
        assert c["temperatura"] == 0.0, nombre
        validar_config(c)


@pytest.mark.parametrize("mala", [
    {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "temperatura": 0.0},       # falta cierre
    {"rol": 8, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0},
    {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.5},
    {"rol": "1", "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0},
    {"rol": True, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0},
    {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0, "x": 1},
])
def test_validar_config_rechaza_configs_mal_formadas(mala):
    with pytest.raises(ValueError):
        validar_config(mala)


# ---- presupuesto ------------------------------------------------------

def test_ningun_algoritmo_pasa_de_B(oraculo):
    opciones, _ = diagnosticar(oraculo, oraculo.datos[:30], k=2)
    C = espacio_reducido(opciones)
    for B in (50, 250, 700):
        contadores = [OraculoContado(oraculo, B, n) for n in ("bt", "sh", "cd")]
        backtracking(contadores[0], opciones, oraculo.datos)
        try:
            successive_halving(contadores[1], C, oraculo.datos, n0=3)
        except ValueError:
            pass
        descenso_coordenadas(contadores[2], opciones, oraculo.datos)
        for c in contadores:
            assert c.consultas <= B, (c.algoritmo, B, c.consultas)


def test_presupuesto_agotado_no_consulta(oraculo):
    contado = OraculoContado(oraculo, B=10)
    contado.evaluar({"temperatura": 0.0}, oraculo.datos[:10])
    antes = oraculo.generaciones
    with pytest.raises(PresupuestoAgotado):
        contado.evaluar({"rol": 1, "temperatura": 0.0}, oraculo.datos[:1])
    assert oraculo.generaciones == antes
    assert contado.consultas == 10
    # Lo ya pagado no se vuelve a cobrar.
    contado.evaluar({"temperatura": 0.0}, oraculo.datos[:10])
    assert contado.consultas == 10


# ---- correctitud de los algoritmos ------------------------------------

@pytest.mark.parametrize("semilla", [0, 1, 2, 3])
def test_backtracking_igual_a_fuerza_bruta(semilla):
    o = OraculoSintetico(semilla=semilla)
    opciones = {r: [x for x in range(8) if x != o._limpia[r]][:2] for r in RANURAS}
    fuerza_bruta = max(o.evaluar(c).precision for c in espacio_reducido(opciones))
    r = backtracking(OraculoContado(o, 10**6), opciones, o.datos)
    assert r["precision"] == pytest.approx(fuerza_bruta)
    assert o.evaluar(r["config"]).precision == pytest.approx(fuerza_bruta)


def test_backtracking_encuentra_la_limpia_tras_el_diagnostico(oraculo):
    opciones, _ = diagnosticar(oraculo, oraculo.datos, k=2)
    r = backtracking(OraculoContado(oraculo, 10**6), opciones, oraculo.datos)
    assert r["precision"] == 1.0
    assert {k: r["config"][k] for k in RANURAS} == oraculo._limpia


def test_successive_halving_consume_la_formula(oraculo, sin_limpia):
    C = espacio_reducido(sin_limpia)
    assert len(C) == 32
    n0 = 2
    contado = OraculoContado(oraculo, 10**6)
    r = successive_halving(contado, C, oraculo.datos, n0=n0)
    formula = len(C) * n0 * math.log2(len(C))
    assert r["rondas"] == 5
    assert r["consultas_nominales"] == formula == r["consultas_formula"]
    assert contado.consultas <= r["consultas_nominales"]


def test_successive_halving_pide_demasiadas_instancias(oraculo, sin_limpia):
    with pytest.raises(ValueError):
        successive_halving(oraculo, espacio_reducido(sin_limpia), oraculo.datos[:10], n0=3)


def test_coordenadas_termina_dentro_de_max_iter(oraculo, sin_limpia):
    for max_iter in (1, 3, 10):
        r = descenso_coordenadas(OraculoContado(oraculo, 10**6), sin_limpia, oraculo.datos,
                                 max_iter=max_iter)
        assert 1 <= r["iteraciones"] <= max_iter


def test_sintetico_es_reproducible():
    a, b = OraculoSintetico(semilla=5, ruido=0.2), OraculoSintetico(semilla=5, ruido=0.2)
    c = {"rol": 1, "estrategia": 2, "formato": 3, "estilo": 4, "cierre": 5, "temperatura": 0.0}
    assert a.evaluar(c).precision == b.evaluar(c).precision
    assert generar_instancias(20, semilla=7) == generar_instancias(20, semilla=7)


# ---- entrega.json -----------------------------------------------------

def test_formato_de_entrega_es_valido():
    """Mismo dict que escribe `ayudas.entrega` (no se importa: trae torch).

    La config es la de ejemplo del README del curso, no una respuesta.
    """
    d = {"grupo": "G01",
         "config": {"rol": 2, "estrategia": 7, "formato": 4, "estilo": 1, "cierre": 6, "temperatura": 0.0},
         "semana": 8}
    validar_entrega(json.loads(json.dumps(d)))
    with pytest.raises(ValueError):
        validar_entrega({**d, "semana": "8"})


def test_entrega_json_del_repo():
    ruta = RAIZ / "entrega.json"
    if not ruta.exists():
        pytest.skip("entrega.json todavía no existe: se genera al correr notebooks/busqueda.ipynb en Colab")
    d = json.loads(ruta.read_text(encoding="utf-8"))
    validar_entrega(d)
    assert d["grupo"] == "G01"
