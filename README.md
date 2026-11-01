# Proyecto Oráculo · ADAG1 · Grupo 1

| | |
|---|---|
| Integrante | Lenuard |
| Curso | Análisis y Diseño de Algoritmos 2026-B |
| Subproyecto | ADAG1 · Proyecto Oráculo (búsqueda de configuraciones de prompt) |
| Versión | primera entrega, rama `main`, tag `v0.1-entrega1` (se crea al entregar) |
| Código | https://github.com/Lenuard/ADA-2026-2-GP01 |
| Python | 3.12 en Colab (notebooks), ≥ 3.10 en local (demo y pruebas) |

Esta es la **solución base**. Tiene cuatro algoritmos de búsqueda sobre el oráculo, cada uno con su T(n) en el docstring, un oráculo sintético para correrlos en CPU, pruebas y los dos notebooks de la entrega. Falta medir los tiempos contra T(n) (semanas 9–10) y las variantes del §4.5; ver [docs/manual_tecnico.md](docs/manual_tecnico.md).

| Notebook | Para qué | Colab |
|---|---|---|
| `notebooks/busqueda.ipynb` | Cómo se obtuvo la config: diagnóstico por trazas, los 4 algoritmos, `oraculo.validar` y `entrega.json` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Lenuard/ADA-2026-2-GP01/blob/main/notebooks/busqueda.ipynb) |
| `notebooks/evaluacion.ipynb` | Carga `entrega.json` y la evalúa sobre los datos de prueba, sin editar nada | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Lenuard/ADA-2026-2-GP01/blob/main/notebooks/evaluacion.ipynb) |
| `proyecto_oraculo.ipynb` | Notebook original del curso, sin cambios, como referencia | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Lenuard/ADA-2026-2-GP01/blob/main/proyecto_oraculo.ipynb) |

## Resultado de la primera entrega

| | |
|---|---|
| Config entregada | `rol 5, estrategia 6, formato 0, estilo 6, cierre 3, temperatura 0.0` ([entrega.json](entrega.json)) |
| Modelo | `qwen17b` (Qwen/Qwen3-1.7B) en Colab T4 |
| Precisión en búsqueda | **17,0 %** ± 3,8 (100 instancias) |
| Precisión en validación (`oraculo.validar`) | **20,7 %** ± 4,3 (87 instancias) |
| Método que la encontró | descenso por coordenadas sobre el espacio reducido por trazas (32 configs) |

Es la **mejor observada**, no un óptimo garantizado. El backtracking y Successive Halving llegaron a `2, 6, 0, 6, 3` con 15 %, una diferencia de 2 instancias que está dentro del error de muestreo. El análisis completo (diagnóstico, tabla de configs, trazas y validación) está en `notebooks/busqueda.ipynb`. El registro de las 83 evaluaciones está en [resultados/registro_busqueda.csv](resultados/registro_busqueda.csv).

`entrega.json` va en la raíz del repo. Lo genera la sección (e) de `notebooks/busqueda.ipynb` y lo lee `notebooks/evaluacion.ipynb`, así que las dos usan la misma config.

## Estructura

```
oraculo.py, ayudas.py, datos_visibles.json   base del curso, sin modificar
busqueda/        paquete de búsqueda, Python puro (sin torch)
  espacio.py       ranuras, espacio reducido, validar_config / validar_entrega
  presupuesto.py   OraculoContado: cuenta consultas y corta en B
  trazas.py        diagnóstico por ranura con las trazas de fallo
  backtracking.py  Alg. 1 · backtracking con poda por cota superior
  halving.py       Alg. 2 · Successive Halving
  coordenadas.py   Alg. 3 · descenso por coordenadas
  reparto.py       Alg. 4 · reparto uniforme frente a adaptativo
  sintetico.py     oráculo sintético con la misma interfaz (CPU)
notebooks/       busqueda.ipynb y evaluacion.ipynb (Colab, T4)
tests/           pruebas con pytest sobre el oráculo sintético
docs/            manual técnico
resultados/      registro_busqueda.csv de la corrida en Colab
entrega.json     config entregada
demo.py          los 4 algoritmos en CPU
```

## Ejemplo pequeño en local

`oraculo.py` necesita GPU, torch y open-instruct, así que en local se usa el oráculo sintético:

```
python -m pip install -r requirements.txt
python demo.py
python -m pytest tests/ -v
```

Salida esperada de `python demo.py` (es determinista: semilla 3, 10 % de ruido):

```
oráculo sintético: semilla 3, ruido 10%, 100 instancias de búsqueda, 87 de validación

(a) diagnóstico con 50 instancias, k=2
    rol        conserva [5, 2]
    estrategia conserva [4, 0]
    formato    conserva [6, 3]
    estilo     conserva [1, 5]
    cierre     conserva [2, 0]
    30 opciones descartadas; ejemplo: rol 0 → descartada: precisión 50.0% < corte 84.0%; rompe startend:end_checker (+14), detectable_content:postscript (+6), first_word:first_word_answer (+2)
    espacio: 32768 → 32 configs

(b) algoritmos sobre C' con 100 instancias, B=3200 por algoritmo
    Alg. 1 backtracking         79.0%  consultas  1600  nodos 16, podas 8
    Alg. 2 successive halving   85.4%  consultas   288  (precisión en 48 inst) nominales 480 = |C|·n0·log2|C| = 480
    Alg. 3 coordenadas          81.0%  consultas   800  iteraciones 2, convergió True
    Alg. 4 reparto (precisión de la ganadora en las 100 instancias)
        B     uniforme  adaptativo
       160     79.0%      79.0%
       480     70.0%      79.0%
       960     79.0%      80.0%
      1600     79.0%      80.0%

(c) mejor observada (coordenadas): {'rol': 2, 'estrategia': 4, 'formato': 3, 'estilo': 1, 'cierre': 2, 'temperatura': 0.0}  búsqueda 81.0%
(d) validación: 75.9%  (87 inst)
   13  first_word:first_word_answer
    2  punctuation:no_comma
    2  change_case:english_lowercase
```

En este mundo sintético la config limpia vale 90 %. Con ruido, el diagnóstico de 50 instancias descartó la opción limpia de `rol`, y los algoritmos encontraron lo mejor **dentro** del espacio reducido (81 %). Por eso los notebooks hablan de *mejor observada* y no de óptimo. Las pruebas comprueban que las configs de salida respetan la interfaz (6 llaves, índices 0..7, temperatura válida), que ningún algoritmo pasa de B, que el backtracking da el mismo óptimo que la fuerza bruta y que Successive Halving gasta exactamente |C|·n0·log₂|C| consultas nominales.

## En Colab

1. Abrir `notebooks/busqueda.ipynb` con el badge y elegir **T4 GPU**.
2. Correr la celda 1 (instalación) y luego *Entorno de ejecución ▸ **Reiniciar sesión***.
3. Hacer clic en la celda 2 y usar *Entorno de ejecución ▸ **Ejecutar celdas posteriores*** (Ctrl+F10). Aceptar el permiso de Google Drive: ahí se guarda el caché del oráculo (`MyDrive/oraculo_cache.json`).
4. Si Colab se desconecta, repetir los pasos 2–3. Gracias al caché en Drive no se vuelve a generar lo ya hecho.
5. Al final se descargan `entrega.json` y `registro_busqueda.csv`. `entrega.json` se sube a la raíz del repo.

El notebook del repo es **la corrida real, con sus salidas**. Al abrirlo con el badge se ven los resultados sin volver a ejecutar nada.

`notebooks/evaluacion.ipynb` no necesita pasos manuales: con **Ctrl+F9** la celda 1 instala y reinicia la sesión sola, y con un segundo **Ctrl+F9** evalúa.

---

# Enunciado del curso (README original)

Curso de Análisis y Diseño de Algoritmos. El trabajo es encontrar una buena configuración de prompt consultando un oráculo. Busquen y validen cuantas veces quieran: el caché guarda lo ya generado y las trazas de fallos vienen con cada resultado.

| Notebook | Colab |
|---|---|
| Proyecto | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Lenuard/ADA-2026-2-GP01/blob/main/proyecto_oraculo.ipynb) |

## Cómo se juega

1. Abran el notebook del curso en Colab.
2. Corran las celdas 1–3. En la 1, **reinicien el entorno** cuando lo pida.
3. Escriban su heurística **solo en la celda 4**.
4. Exporten `entrega.json` en la celda 5.

```
r = oraculo.evaluar(config, instancias, semilla)
r_val = oraculo.validar(config, n)

r.precision        # 0.55
r.trazas           # [{id, violo, salida}, ...]
```

Hay **32 768** configuraciones (`espacio()`, temperatura 0.0): un índice de 0 a 7 por ranura entre `rol`, `estrategia`, `formato`, `estilo` y `cierre`, más la temperatura. Cada ranura es un consejo de prompting; algunos combinan mal con las restricciones que mide el verificador, y las trazas dicen cuál falló. El lote de búsqueda del notebook son las 100 instancias de `busqueda`. Medir con cuántas instancias buscar es parte del problema.

**Es un problema de optimización de verdad.** Cada ranura ataca una parte distinta de la respuesta —el prefijo, el largo, la estructura, los caracteres, el sufijo— y los efectos se componen. Una configuración al azar se queda **debajo del 5%**; el techo está cerca del **24%**. Sortear no alcanza: hay **una sola opción limpia entre ocho** en cada ranura, así que acertar cuatro de cinco ranuras al azar pasa 1 vez cada 900. Para pasar de ahí hay que usar la estructura — leer las trazas, ver qué familia rompe cada opción, y buscar con eso (backtracking con poda, ascenso por coordenadas, haz, recocido). Reparar una ranura a la vez sube de a escalones; ninguna opción buena está en el mismo índice en todas las ranuras.

Las particiones vienen **curadas**. `datos_visibles.json` marca como `descartada` a la instancia que pide más texto del que cabe en `max_new_tokens`, a la que ninguna opción puede romper, y a las de una o de cuatro-cinco restricciones. Las primeras son imposibles de acertar; las segundas son puntos que nadie puede perder, y con un tercio del lote así el puntaje casi no dependía de la configuración elegida. Búsqueda y validación quedan con la misma dificultad (2.5 restricciones por instancia), para que validar mida generalización y no un lote más duro.

## Modelos

`cargar_modelo` acepta un alias o un id de Hugging Face:

| Alias | Checkpoint | Notas |
|---|---|---|
| `qwen17b` | `Qwen/Qwen3-1.7B` | el de por defecto; el más rápido |
| `qwen17b4bit` | `unsloth/Qwen3-1.7B-unsloth-bnb-4bit` | el mismo 1.7B en 4-bit |
| `ministral3b` | `mistralai/Ministral-3-3B-Instruct-2512-BF16` | 3.8B en fp16 (~7.7 GB), T4 |
| `llama3b` | `unsloth/Llama-3.2-3B-Instruct` | 3.2B en fp16 (~6.4 GB), T4 |
| `qwen8b` | `unsloth/Qwen3-8B-unsloth-bnb-4bit` | 4-bit, T4 |
| `mistral7b` | `unsloth/mistral-7b-instruct-v0.3-bnb-4bit` | 4-bit, T4 |

```
modelo = cargar_modelo("qwen8b")
```

Los 7-8B son lentos en T4: tengan paciencia con las primeras corridas.

## Búsqueda y validación

`datos_visibles.json` tiene 450 instancias, de las que se usan **100 de búsqueda y 87 de validación** (el resto va marcado `descartada`, ver `dividir`). Son el mismo split que usan [GEPA](https://arxiv.org/abs/2507.19457) y NPO [1] sobre IF-RLVR Train, de donde salen estos datos. No son las filas exactas de los papers —no publican los índices—, sí la fuente, los tamaños y la disyunción.

```
datos = cargar_datos()
busqueda, validacion = dividir(datos)
oraculo = Oraculo(modelo, busqueda, validacion)
```

Las dos particiones salen del mismo pool y comparten distribución: validar mide si la config aguanta **instancias** nuevas, no restricciones de un tipo nuevo. Ese otro salto se mide al calificar, con familias que no están en este archivo.

Busquen solo sobre `busqueda`. `oraculo.validar` mide la config elegida con una muestra fija de `n` instancias (las 300 tardan) e imprime qué restricciones se cayeron más.

```
r_val = oraculo.validar(mejor[1], n=30)
```

### Ojo con el todo-o-nada

Una instancia trae **hasta 5 restricciones** (2.3 en promedio) y se puntúa todo-o-nada: basta que falle una para que valga 0. En las instancias más duras el modelo acierta poco, así que **con pocas instancias muchas configuraciones van a marcar `0.0` y parecer iguales**. Si su búsqueda no logra distinguir nada, suban el número de instancias antes de cambiar de heurística — decidir cuántas medir es parte del problema.

## Archivos

| Archivo | Qué es |
|---|---|
| `proyecto_oraculo.ipynb` | El notebook del curso |
| `oraculo.py` | La caja negra. Se consulta, no se abre |
| `ayudas.py` | Cargar modelo, datos, dividir, ver un prompt, curva, entrega |
| `datos_visibles.json` | 450 instancias: 100 de búsqueda, 87 de validación, 263 descartadas |

## Entrega

Un `entrega.json` con grupo, configuración y semana:

```json
{
 "grupo": "G07",
 "config": {"rol": 2, "estrategia": 7, "formato": 4, "estilo": 1, "cierre": 6, "temperatura": 0.0},
 "semana": 3
}
```

## Referencias

[1] Yuan Chang y Xiaoqi Chen, *Naive Prompt Optimization: Rethinking the Need for Complex Prompt Search*, arXiv:2608.27266, 2026. https://arxiv.org/abs/2608.27266
