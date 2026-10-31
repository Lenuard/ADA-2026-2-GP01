"""
presupuesto.py — contador de consultas con tope B.

La unidad de costo es lo que cobra la GPU: una generación por cada par
(config, instancia, semilla) que no se había pedido antes. El oráculo real
ya no regenera lo cacheado, pero su caché es compartido entre algoritmos;
para compararlos en igualdad de condiciones cada uno lleva su propio contador.
"""

import hashlib
import json


class PresupuestoAgotado(Exception):
    """La consulta pedida haría pasar el contador de B. No se hizo."""


def huella(config):
    """md5 de la config con `sort_keys`, igual que `oraculo._id_config`.

    Dos dicts con las mismas llaves en otro orden cuentan como la misma
    config, como en el caché del oráculo.
    """
    return hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()


class OraculoContado:
    """Envoltorio de cualquier objeto con `evaluar(config, instancias, semilla)`.

    `consultas` cuenta los pares nuevos pagados hasta ahora. Antes de consultar
    se calculan los pares nuevos y, si no caben en `B`, se lanza
    `PresupuestoAgotado` **sin** consultar: así B nunca se pasa.

    `registro` guarda cada evaluación (algoritmo, config, n, precisión) para la
    tabla del notebook; `historial` solo las precisiones, para `ayudas.curva`.
    """

    def __init__(self, oraculo, B, algoritmo=""):
        self.oraculo = oraculo
        self.B = B
        self.algoritmo = algoritmo
        self.pagados = set()
        self.registro = []
        self.historial = []

    @property
    def consultas(self):
        return len(self.pagados)

    @property
    def restantes(self):
        return self.B - self.consultas

    def costo(self, config, instancias, semilla=1):
        """Pares nuevos que costaría esta evaluación, sin hacerla."""
        h = huella(config)
        return len({(h, x["id"], semilla) for x in instancias} - self.pagados)

    def evaluar(self, config, instancias=None, semilla=1):
        if instancias is None:
            instancias = self.oraculo.datos
        h = huella(config)
        pares = {(h, x["id"], semilla) for x in instancias}
        nuevos = pares - self.pagados
        if self.consultas + len(nuevos) > self.B:
            raise PresupuestoAgotado(
                f"{self.algoritmo or 'búsqueda'}: {self.consultas} usadas + "
                f"{len(nuevos)} nuevas > B={self.B}"
            )
        r = self.oraculo.evaluar(config, instancias, semilla=semilla)
        self.pagados |= nuevos
        self.registro.append({
            "algoritmo": self.algoritmo,
            "config": dict(config),
            "n": r.n,
            "precision": r.precision,
        })
        self.historial.append(r.precision)
        return r
