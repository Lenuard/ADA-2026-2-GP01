# Manual técnico · Proyecto Oráculo (ADAG1, Grupo 1) · solución base

Lenuard · Análisis y Diseño de Algoritmos 2026-B · primera entrega (`v0.1-entrega1`)

Este manual explica cómo está construida la solución base y cómo reproducir su ejecución. Sigue las secciones de la guía de primera entrega (§6).

---

## 1. Entorno

| | Local (demo y pruebas) | Colab (notebooks) |
|---|---|---|
| Lenguaje | Python ≥ 3.10 (probado con 3.14.4) | Python 3.12 (el de Colab) |
| Sistema | Windows, Linux o macOS; solo CPU | Google Colab con GPU **T4** |
| Dependencias | `pytest` (`requirements.txt`) | `bitsandbytes>=0.46.1`, `transformers`, `accelerate`, `nltk`, `spacy` + `en_core_web_sm`, `emoji`, `langdetect`, `immutabledict`; `torch`, `pandas` y `matplotlib` ya vienen en Colab |
| Datos externos | ninguno | `allenai/open-instruct` clonado en `/content/open-instruct` (verificadores IFEvalG) y datos de nltk |
| Modelo | — | `qwen17b` → `Qwen/Qwen3-1.7B`, desde Hugging Face, sin login |

La celda 1 de cada notebook instala todo eso y clona este repo en `/content/ADA-2026-2-GP01`.

`oraculo.py` importa `torch` y open-instruct al cargarse, así que **no se puede importar en local**. `ayudas.py` tampoco, porque importa `oraculo`. Por eso el paquete `busqueda/` es Python puro y no los importa: trabaja con cualquier objeto que tenga el método `evaluar`.

## 2. Arquitectura

```
ADA-2026-2-GP01/
├── oraculo.py            caja negra del curso (no se modifica)
├── ayudas.py             cargar_modelo, cargar_datos, dividir, curva, entrega (no se modifica)
├── datos_visibles.json   450 instancias: 100 búsqueda, 87 validación, 263 descartadas
├── proyecto_oraculo.ipynb  notebook original del curso, como referencia
├── busqueda/             solución base (Python puro)
│   ├── espacio.py        RANURAS, config_vacia, espacio_reducido, vecinos, ordenar,
│   │                     validar_config, validar_entrega
│   ├── presupuesto.py    OraculoContado (contador con tope B), PresupuestoAgotado
│   ├── trazas.py         diagnosticar: efecto aislado de cada opción, k mejores por ranura
│   ├── backtracking.py   Alg. 1
│   ├── halving.py        Alg. 2
│   ├── coordenadas.py    Alg. 3
│   ├── reparto.py        Alg. 4
│   └── sintetico.py      OraculoSintetico y generar_instancias
├── notebooks/
│   ├── busqueda.ipynb    proceso de búsqueda documentado → entrega.json
│   └── evaluacion.ipynb  evalúa entrega.json sobre los datos de prueba
├── tests/test_busqueda.py
├── demo.py               los 4 algoritmos sobre el oráculo sintético, en CPU
├── entrega.json          config entregada (la genera busqueda.ipynb)
└── docs/manual_tecnico.md
```

**Interfaz común (duck typing).** Todo el paquete usa un único método:

```
oraculo.evaluar(config, instancias, semilla) → objeto con .precision, .trazas, .n
```

Lo cumplen `oraculo.Oraculo` (el LLM real), `busqueda.sintetico.OraculoSintetico` (CPU) y `busqueda.presupuesto.OraculoContado` (el envoltorio que cuenta consultas). Por eso el mismo código de los algoritmos corre en las pruebas, en la demo y en Colab.

## 3. Funcionamiento

### 3.1 Problema y unidad de costo

Una **config** es un dict `{rol, estrategia, formato, estilo, cierre, temperatura}`, con un índice de 0 a 7 por ranura. El espacio completo tiene |C| = 8⁵ = 32 768 configs con temperatura 0.0. La precisión de una config es la fracción de instancias en las que el modelo cumple **todas** las restricciones (todo-o-nada).

La unidad de costo es la **consulta**: un par (config, instancia, semilla) que el LLM tiene que generar. `OraculoContado` cuenta solo los pares nuevos, porque los repetidos salen del caché del oráculo.

### 3.2 Flujo del notebook de búsqueda

1. **Diagnóstico por trazas** (`trazas.diagnosticar`). Mide la config vacía y cada una de las 40 opciones **sola**. Para cada opción calcula la precisión, el delta frente a la base y las familias `violo` que aparecen de más. Conserva las `k` mejores por ranura y deja registrado el motivo de cada descarte. Costo: (1 + 5·8)·n_diag consultas. Resultado: un espacio reducido C' con k⁵ configs (32 con k = 2).
2. **Búsqueda en C'** con los cuatro algoritmos. Cada uno tiene su propio `OraculoContado(oraculo, B)`.
3. **Selección.** La ganadora de cada algoritmo se vuelve a medir sobre las mismas 100 instancias y se queda la de mayor precisión: la *mejor observada*.
4. **Validación.** `oraculo.validar(mejor, n=87)` mide sobre la partición de validación.
5. **Entrega.** `ayudas.entrega("G01", mejor, 8)` escribe `entrega.json`.

### 3.3 Algoritmos

| Alg. | Archivo | Idea | Parada | T(n) |
|---|---|---|---|---|
| 1 · Backtracking con poda | `backtracking.py` | DFS que fija una ranura por nivel. La cota de un nodo es la precisión de la config parcial (las ranuras sin fijar quedan vacías). Poda si cota ≤ mejor. Los hijos se visitan de mayor a menor cota. | árbol agotado o B | O(\|C\|·n) en el peor caso, porque hay Σ_{d=1..5} k^d = O(k⁵) nodos, cada uno con n consultas |
| 2 · Successive Halving | `halving.py` | R = ⌈log₂\|C\|⌉ rondas con n_r = n0·2^r instancias (prefijos anidados); pasa la mejor mitad. | queda 1 config | nominal \|C\|·n0·log₂\|C\| (exacto si \|C\| es potencia de 2); el real es menor por el caché |
| 3 · Descenso por coordenadas | `coordenadas.py` | Desde la mejor opción de cada ranura, prueba las opciones de una ranura con las demás fijas y cambia solo si mejora estrictamente. | una iteración sin cambios o `max_iter` | O(I·k_max·n0) |
| 4 · Reparto de presupuesto | `reparto.py` | Uniforme: m = ⌊B/\|C\|⌋ instancias por config. Adaptativo: Successive Halving con el mayor n0 que cabe en B. Se compara la calidad de la ganadora con el mismo B. | fin de cada método | B consultas como máximo |

**Exactitud de la cota del backtracking.** En el oráculo sintético sin ruido, agregar una ranura solo puede romper más familias, así que la cota es exacta y el backtracking devuelve el óptimo de C'. La prueba `test_backtracking_igual_a_fuerza_bruta` lo verifica. Con el LLM la cota es **heurística**: una ranura puede arreglar fallos de otra (la opción de `cierre` que repite las restricciones), y la poda puede cortar ramas buenas.

**Óptimos locales del descenso por coordenadas.** Si dos ranuras solo mejoran cambiando juntas, ningún paso de una sola coordenada lo ve. La demo lo muestra: con ruido, el backtracking y el descenso por coordenadas terminan en configs distintas.

### 3.4 Estructuras de datos

- **Instancia**: dict con `id`, `prompt`, `ids` (familias de restricción), `kwargs` (argumentos de cada verificador), `restriccion` y `split`. Es el formato de `datos_visibles.json`. El sintético usa el mismo, sin `restriccion`.
- **Resultado**: `precision` (float), `trazas` (lista de `{id, violo, salida}`, solo de los fallos) y `n`.
- **Opciones conservadas**: dict ranura → lista de índices, del mejor al peor.
- **Contador**: `OraculoContado.pagados` es un set de `(md5 de la config, id, semilla)`. `registro` es una lista de `{algoritmo, config, n, precision}` y `historial` una lista de precisiones (para `ayudas.curva`).
- **Oráculo sintético**: `rompe[ranura][opcion]` es el set de familias que esa opción rompe. Hay una opción limpia por ranura (set vacío), en índices distintos por ranura.

### 3.5 Condiciones de parada y presupuesto

Los tres algoritmos de búsqueda capturan `PresupuestoAgotado`, devuelven la mejor config vista hasta ese momento y marcan `agotado = True`. `OraculoContado` lanza la excepción **antes** de consultar, así que ningún algoritmo gasta más de B (lo verifica `test_ningun_algoritmo_pasa_de_B`).

## 4. Uso

### 4.1 Local

```
python -m pip install -r requirements.txt
python demo.py              # los 4 algoritmos sobre el oráculo sintético
python -m pytest tests/ -v  # pruebas
```

La salida esperada de `demo.py` está en el README. Cómo leerla:

- **(a)**: las opciones conservadas por ranura y el motivo de un descarte (precisión frente al corte y familias que rompe).
- **(b)**: la precisión de la ganadora de cada algoritmo y las consultas que gastó. En Successive Halving, las nominales coinciden con la fórmula. La tabla del Alg. 4 compara qué tan buena es la ganadora de cada reparto con el mismo B.
- **(c)**: la mejor observada.
- **(d)**: su validación, con las familias que más fallan.

Uso programático:

```python
from busqueda import diagnosticar, espacio_reducido, OraculoContado, backtracking
from busqueda.sintetico import OraculoSintetico

o = OraculoSintetico(semilla=0)
opciones, tabla = diagnosticar(o, o.datos[:50], k=2)
r = backtracking(OraculoContado(o, B=3200), opciones, o.datos)
print(r["config"], r["precision"])
```

### 4.2 Colab

1. Abrir `notebooks/busqueda.ipynb` desde el badge del README y elegir *Entorno de ejecución ▸ T4 GPU*.
2. Pulsar **Ctrl+F9** (*Ejecutar todas*). La celda 1 instala y reinicia la sesión sola, porque `transformers` queda a medias si no se reinicia; Colab puede avisar que la sesión falló, y es lo esperado. Luego pulsar **Ctrl+F9 otra vez**: la celda 1 ve la marca `/content/.instalado` y no reinstala. Hay que aceptar el permiso de Google Drive, y desde ahí todo corre sin intervención.
   - Si Colab se desconecta (inactividad, límite de la sesión gratuita), se repite el paso 2. El caché del oráculo está en `MyDrive/oraculo_cache.json`, así que lo ya generado no se vuelve a pagar.
3. Los parámetros (`K`, `N_DIAG`, `N0`, `B`, `MAX_ITER`) están en la sección 3 del notebook, con su justificación. En el peor caso, la unión de consultas al LLM es de unas 2 050 (diagnóstico) + 3 200 (C' completo con 100 instancias) + 87 (validación).
4. La sección (e) descarga `entrega.json` y `registro_busqueda.csv` y los copia en `MyDrive/oraculo_resultados/`. `entrega.json` se sube a la raíz del repo.
5. `notebooks/evaluacion.ipynb` se corre igual (Ctrl+F9 dos veces, sin Drive) y no hay que editar nada. Lee `entrega.json` del repo y los datos de `/content/datos_prueba.json`; si no están, los pide con `files.upload()`. Imprime la precisión en prueba.

**Formato de `entrega.json`**:

```json
{"grupo": "G01", "config": {"rol": 0, "estrategia": 0, "formato": 0, "estilo": 0, "cierre": 0, "temperatura": 0.0}, "semana": 8}
```

Los índices van de 0 a 7 y la temperatura es uno de 0.0, 0.3 o 0.7. `busqueda.validar_entrega` lo comprueba.

## 5. Validación y límites

### 5.1 Pruebas disponibles (`tests/test_busqueda.py`)

| Prueba | Qué verifica |
|---|---|
| `test_configs_de_los_algoritmos_son_validas` | Las salidas de los 4 algoritmos traen exactamente las 6 llaves, con índices en rango y temperatura 0.0. |
| `test_validar_config_rechaza_configs_mal_formadas` | Rechaza llaves faltantes o sobrantes, índices fuera de rango, tipos incorrectos y temperaturas inválidas. |
| `test_ningun_algoritmo_pasa_de_B` | Con B = 50, 250 y 700, ningún contador pasa de B. |
| `test_presupuesto_agotado_no_consulta` | La excepción salta antes de generar, y lo ya pagado no se vuelve a cobrar. |
| `test_backtracking_igual_a_fuerza_bruta` | Con 4 semillas, en \|C'\| = 32, el backtracking da el mismo óptimo que la fuerza bruta. |
| `test_backtracking_encuentra_la_limpia_tras_el_diagnostico` | Diagnóstico + backtracking recuperan la config limpia del sintético sin ruido. |
| `test_successive_halving_consume_la_formula` | Con \|C\| = 32 y n0 = 2, las consultas nominales son exactamente \|C\|·n0·log₂\|C\| = 320, y las reales son ≤. |
| `test_coordenadas_termina_dentro_de_max_iter` | El descenso por coordenadas respeta `max_iter`. |
| `test_formato_de_entrega_es_valido` / `test_entrega_json_del_repo` | El formato de `ayudas.entrega` es válido. `entrega.json` del repo se valida si existe; si no, la prueba se omite. |

Resultado actual: 19 pruebas pasan y 1 se omite, porque `entrega.json` todavía no se generó.

### 5.2 Supuestos

- La temperatura queda fija en 0.0, con decodificación greedy. Así cada consulta es determinista y el caché la reusa.
- La cota del backtracking supone que agregar ranuras no mejora la precisión. Es exacto en el sintético y heurístico en el LLM.
- El diagnóstico supone que el efecto aislado de una opción predice su efecto en combinación. No ve interacciones, y por eso se conservan k = 2 opciones por ranura y no 1.
- Las particiones de búsqueda y validación tienen la misma distribución (`ayudas.dividir`).

### 5.3 Errores y limitaciones conocidos

- **La config entregada es la mejor observada, no un óptimo garantizado.** Hay tres fuentes de error: el diagnóstico (que en la demo descarta la opción limpia de `rol` por ruido y deja la búsqueda en 81 % cuando el óptimo es 90 %), la cota heurística y el error de muestreo. Con 100 instancias todo-o-nada, el error estándar de la precisión es de unos ±4 puntos.
- Si los datos privados traen familias de restricción que no están en IFEvalG, `Oraculo` lanza `KeyError` ("ningún registro conoce …"). Para esos casos el oráculo acepta registros extra (`registros=`), pero el notebook de evaluación no los carga porque no conoce esas familias.
- En Colab, si la sesión no se reinicia después de instalar, `cargar_modelo` puede fallar con un error opaco. La celda 1 reinicia sola matando el proceso; si una versión futura de Colab no reinicia así, hay que usar *Entorno de ejecución ▸ Reiniciar sesión* a mano.
- Colab gratis corta las sesiones por inactividad y tiene un tope de horas y de cuota de GPU. El caché en Drive hace que reanudar no repita generaciones, pero no evita el corte. Si la VRAM se queda corta, el oráculo reintenta de a un prompt (más lento).
- `OraculoContado` cuenta consultas por algoritmo. El costo real en la GPU es la unión, que es menor porque el caché es compartido.

### 5.4 Componentes aún no desarrollados

- **Mediciones de tiempo contra T(n)** con al menos 5 tamaños de n (semanas 9–10). El oráculo sintético ya está listo para eso.
- **Variantes del §4.5**: temperatura con 3 niveles, UCB1, recocido simulado o algoritmo genético.
- **Búsqueda sobre la temperatura**: `espacio.TEMPERATURAS` y `validar_config` la admiten, pero los algoritmos la dejan fija en 0.0.
- **Números reales del LLM**: README y manual se actualizan con la config, la precisión de búsqueda y la de validación cuando se corra `busqueda.ipynb` en Colab.

### 5.5 Diferencias entre documentos

El enunciado (docx), la guía y el repo base no coinciden en algunos datos. Esta solución sigue al **repo y al oráculo**, porque la calificación corre `entrega.json` sobre ese oráculo, y trata \|C\| y n como parámetros generales.

| Tema | Enunciado (docx) | Guía | Repo / oráculo (lo que se usa) |
|---|---|---|---|
| Reducción NP-dura | desde Cobertura Máxima | desde 3-SAT | — |
| Categorías | rol, estrategia, formato, verificación, recordatorio | rol, estrategia, formato, estilo, cierre + temperatura | igual que la guía; `cierre` funde verificación y recordatorio |
| \|C\| | 3 840 (en otro lugar 144; 432 con temperatura) | — | 8⁵ = 32 768 (×3 con temperaturas) |
| n de búsqueda | 150 | — | 100 de búsqueda + 87 de validación |
| k_max | 4 | — | 8 opciones por ranura |
