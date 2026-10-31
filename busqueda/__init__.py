"""
busqueda — algoritmos de búsqueda de configuraciones para el Proyecto Oráculo.

Python puro, sin torch: funciona con cualquier objeto que tenga
``evaluar(config, instancias, semilla)`` y devuelva algo con ``precision``,
``trazas`` y ``n``. En Colab es `oraculo.Oraculo`; en local, el
`OraculoSintetico` de `busqueda.sintetico`.

    from busqueda import diagnosticar, espacio_reducido, backtracking
    opciones, tabla = diagnosticar(oraculo, instancias, k=2)
    r = backtracking(OraculoContado(oraculo, B=2000), opciones, instancias)
"""

from .backtracking import backtracking
from .coordenadas import descenso_coordenadas
from .espacio import (
    N_OPCIONES,
    RANURAS,
    TEMPERATURA,
    TEMPERATURAS,
    completa,
    config_vacia,
    espacio_reducido,
    ordenar,
    validar_config,
    validar_entrega,
    vecinos,
)
from .halving import rondas, successive_halving
from .presupuesto import OraculoContado, PresupuestoAgotado
from .reparto import comparar_repartos, n0_adaptativo, reparto_adaptativo, reparto_uniforme
from .trazas import diagnosticar
