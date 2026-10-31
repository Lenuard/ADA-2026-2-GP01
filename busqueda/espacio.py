"""
espacio.py — el espacio de configuraciones, sin importar `oraculo.py`.

`oraculo.py` carga torch y open-instruct al importarse, así que en local no se
puede usar. Acá se copian solo las constantes que la búsqueda necesita; si el
catálogo cambiara de tamaño, `validar_config` lo detectaría al calificar.
"""

import itertools

# Copia de `oraculo.RANURAS`: mismo orden, mismo nombre.
RANURAS = ["rol", "estrategia", "formato", "estilo", "cierre"]

# Opciones por ranura en `oraculo.CATALOGO` (ocho cada una).
N_OPCIONES = 8

# Copia de `oraculo.TEMPERATURAS`. La primera entrega deja la temperatura en 0.0.
TEMPERATURAS = [0.0, 0.3, 0.7]
TEMPERATURA = 0.0


def config_vacia(temperatura=TEMPERATURA):
    """Config sin ninguna ranura: el oráculo no pega texto de catálogo.

    `oraculo._opcion` devuelve "" para una llave ausente, así que esta config
    mide al modelo con la petición sola. Es la base del diagnóstico y la raíz
    del árbol del backtracking. `temperatura` sí es obligatoria.
    """
    return {"temperatura": temperatura}


def completa(config):
    """True si la config trae las cinco ranuras."""
    return all(r in config for r in RANURAS)


def ordenar(config):
    """La misma config con las llaves en el orden de `RANURAS` y la temperatura al final.

    No cambia el valor (el oráculo hashea con `sort_keys`): es para que la
    config se lea igual en las tablas y en `entrega.json`.
    """
    out = {r: int(config[r]) for r in RANURAS if r in config}
    out["temperatura"] = config.get("temperatura", TEMPERATURA)
    return out


def espacio_reducido(opciones, temperatura=TEMPERATURA):
    """Producto cartesiano de `opciones[ranura]` en el orden de `RANURAS`.

    `opciones` es un dict ranura → lista de índices conservados (lo que
    devuelve `trazas.diagnosticar`). Con k opciones por ranura salen k⁵ configs.
    """
    listas = [opciones[r] for r in RANURAS]
    return [
        dict(zip(RANURAS, (int(i) for i in combo)), temperatura=temperatura)
        for combo in itertools.product(*listas)
    ]


def vecinos(config, ranura, opciones):
    """Configs que difieren de `config` solo en `ranura`, una por opción.

    Incluye la propia config si su índice está entre las opciones: el descenso
    por coordenadas la compara contra las demás sin pedirla aparte.
    """
    return [{**config, ranura: int(o)} for o in opciones[ranura]]


def validar_config(config):
    """Lanza ValueError si la config no la acepta la interfaz del oráculo.

    Exige exactamente las cinco ranuras más `temperatura`, índices enteros en
    0..7 y una temperatura de `TEMPERATURAS`. Una config parcial sirve para
    buscar, pero no para entregar: la profesora la califica tal cual.
    """
    if not isinstance(config, dict):
        raise ValueError(f"la config debe ser dict, no {type(config).__name__}")
    esperadas = set(RANURAS) | {"temperatura"}
    if set(config) != esperadas:
        faltan = sorted(esperadas - set(config))
        sobran = sorted(set(config) - esperadas)
        raise ValueError(f"llaves incorrectas: faltan {faltan}, sobran {sobran}")
    for r in RANURAS:
        v = config[r]
        # bool es subclase de int: True pasaría como índice 1.
        if not isinstance(v, int) or isinstance(v, bool):
            raise ValueError(f"{r} debe ser int, no {type(v).__name__}")
        if not 0 <= v < N_OPCIONES:
            raise ValueError(f"{r}={v} fuera de rango 0..{N_OPCIONES - 1}")
    t = config["temperatura"]
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t not in TEMPERATURAS:
        raise ValueError(f"temperatura={t!r} no está en {TEMPERATURAS}")
    return True


def validar_entrega(d):
    """Lanza ValueError si `d` no tiene la forma de `ayudas.entrega`.

    `{"grupo": str, "config": {...}, "semana": int}`, nada más.
    """
    if not isinstance(d, dict):
        raise ValueError("la entrega debe ser un objeto JSON")
    if set(d) != {"grupo", "config", "semana"}:
        raise ValueError(f"llaves de la entrega: {sorted(d)}; se esperan grupo, config, semana")
    if not isinstance(d["grupo"], str) or not d["grupo"]:
        raise ValueError("grupo debe ser un texto no vacío, p. ej. \"G01\"")
    if not isinstance(d["semana"], int) or isinstance(d["semana"], bool) or d["semana"] < 1:
        raise ValueError("semana debe ser un entero positivo")
    validar_config(d["config"])
    return True
