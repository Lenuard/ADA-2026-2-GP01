"""
sintetico.py — oráculo sintético con la misma interfaz que `oraculo.Oraculo`.

Sirve para correr los algoritmos en CPU, en las pruebas y en la demo, y más
adelante para medir T(n) sin pagar generaciones. Implementa un caso particular
del modelo de reglas del informe, aquel en que las opciones solo hacen fallar
familias (la reducción desde 3-SAT usa el caso opuesto, en que solo ayudan):

- Hay un universo de familias de restricción (las del verificador).
- Cada instancia exige un subconjunto de 1–3 familias.
- Cada opción de cada ranura **rompe** un conjunto de familias; una sola
  opción por ranura no rompe nada (la limpia), y su índice cambia de ranura en
  ranura, como en el catálogo real.
- Una instancia pasa si ninguna opción elegida rompe alguna de sus familias.
  `violo` es la primera familia rota, en el orden en que la instancia las trae.

Sin ruido el oráculo es **monótono**: agregar una ranura a una config parcial
solo puede romper más familias. Por eso la cota del backtracking es exacta acá.
Con `ruido > 0`, una instancia que pasaría falla con esa probabilidad (de
forma determinista por config, instancia y semilla) y la monotonía se pierde,
igual que con el LLM real.
"""

import random
from collections import Counter

from .espacio import N_OPCIONES, RANURAS
from .presupuesto import huella

FAMILIAS = [
    "detectable_format:title",
    "detectable_format:number_bullet_lists",
    "detectable_format:multiple_sections",
    "paragraphs:paragraphs",
    "punctuation:no_comma",
    "change_case:english_lowercase",
    "change_case:capital_word_frequency",
    "first_word:first_word_answer",
    "last_word:last_word_answer",
    "startend:end_checker",
    "detectable_content:postscript",
    "length_constraints:number_words",
]


class Resultado:
    """Misma forma que `oraculo.Resultado`: precision, trazas (solo fallos) y n."""

    def __init__(self, precision, trazas, n):
        self.precision = precision
        self.trazas = trazas
        self.n = n

    def __repr__(self):
        return f"Resultado(precision={self.precision:.1%}, fallos={len(self.trazas)}/{self.n})"


def generar_instancias(n, familias=FAMILIAS, semilla=0, inicio=0):
    """`n` instancias con 1–3 familias cada una, reproducibles por `semilla`.

    `familias` puede ser una lista de nombres o un entero (se generan
    ``fam_00``, ``fam_01``…). `inicio` desplaza los ids, para armar
    particiones disjuntas con el mismo generador.
    """
    if isinstance(familias, int):
        familias = [f"fam_{i:02d}" for i in range(familias)]
    rng = random.Random(semilla)
    instancias = []
    for i in range(inicio, inicio + n):
        ids = rng.sample(familias, rng.randint(1, min(3, len(familias))))
        instancias.append({
            "id": i,
            "prompt": f"instancia sintética {i}",
            "ids": ids,
            "kwargs": [{} for _ in ids],
            "split": "busqueda",
        })
    return instancias


class OraculoSintetico:
    """Caja negra sintética: config + instancias → precisión y trazas.

    Parameters
    ----------
    familias:
        Universo de familias (lista o entero), compartido con `generar_instancias`.
    semilla:
        Fija qué opción es la limpia en cada ranura y qué rompe cada una.
    ruido:
        Probabilidad de que una instancia que pasaría falle igual.
    datos, validacion:
        Instancias por defecto de `evaluar` y partición de `validar`. Si no se
        dan, se generan 100 y 87, como en el repo del curso.
    """

    def __init__(self, familias=FAMILIAS, semilla=0, ruido=0.0, n_opciones=N_OPCIONES,
                 datos=None, validacion=None):
        if isinstance(familias, int):
            familias = [f"fam_{i:02d}" for i in range(familias)]
        self.familias = list(familias)
        self.ruido = ruido
        rng = random.Random(semilla)

        # Una limpia por ranura, en índices distintos: el patrón no se adivina.
        indices = rng.sample(range(n_opciones), len(RANURAS))
        self._limpia = dict(zip(RANURAS, indices))
        self.rompe = {
            r: [
                set() if o == self._limpia[r]
                else set(rng.sample(self.familias, rng.randint(1, min(3, len(self.familias)))))
                for o in range(n_opciones)
            ]
            for r in RANURAS
        }

        self.datos = datos if datos is not None else generar_instancias(100, self.familias, semilla)
        self.validacion = (
            validacion if validacion is not None
            else generar_instancias(87, self.familias, semilla + 1, inicio=len(self.datos))
        )
        # Lo que el caché del oráculo real habría tenido que generar.
        self._generados = set()

    @property
    def generaciones(self):
        return len(self._generados)

    def rotas(self, config):
        """Familias que rompe la config: unión sobre las ranuras presentes."""
        out = set()
        for r in RANURAS:
            if r in config:
                out |= self.rompe[r][config[r]]
        return out

    def evaluar(self, config, instancias=None, semilla=1, **_):
        if instancias is None:
            instancias = self.datos
        h = huella(config)
        rotas = self.rotas(config)
        trazas, aciertos = [], 0
        for x in instancias:
            self._generados.add((h, x["id"], semilla))
            violo = next((f for f in x["ids"] if f in rotas), None)
            if violo is None and self.ruido > 0:
                azar = random.Random(f"{h}|{x['id']}|{semilla}")
                if azar.random() < self.ruido:
                    violo = x["ids"][0]
            if violo is None:
                aciertos += 1
            else:
                trazas.append({"id": x["id"], "violo": violo, "salida": ""})
        return Resultado(aciertos / len(instancias), trazas, len(instancias))

    def validar(self, config, n=None, semilla=1, top=8):
        """Igual que `Oraculo.validar`: muestra fija de la partición de validación."""
        conjunto = self.validacion if n is None else self.validacion[:n]
        r = self.evaluar(config, conjunto, semilla=semilla)
        print(f"validación: {r.precision:.1%}  ({r.n} inst)")
        for fam, veces in Counter(t["violo"] for t in r.trazas).most_common(top):
            print(f"  {veces:3}  {fam}")
        return r
