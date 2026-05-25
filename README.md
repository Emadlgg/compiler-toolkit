# Generador de Analizadores Léxicos y Sintácticos — YALex + YAPar

Implementación completa de un ecosistema de análisis léxico y sintáctico inspirado en las herramientas clásicas **Lex/Yacc**, utilizando los formatos **YALex** y **YAPar**.

El proyecto permite:

* Generar analizadores léxicos desde especificaciones `.yal`
* Generar analizadores sintácticos desde gramáticas `.yapar`
* Construir automáticamente:

  * AFNs
  * AFDs
  * Autómatas LR(0)
  * Tablas LL(1)
  * Tablas SLR(1)
  * Tablas LALR
* Analizar archivos de entrada
* Visualizar resultados mediante una interfaz gráfica tipo IDE

---

# Características

## YALex

* Parser de expresiones regulares
* Construcción de Thompson
* Construcción de subconjuntos
* Longest match
* Prioridad por orden de definición
* Generación automática de lexers en Python
* Visualización de árboles y AFD

## YAPar

* Parser de gramáticas `.yapar`
* Cálculo de FIRST y FOLLOW
* Construcción de autómatas LR(0)
* Generación de tablas:

  * LL(1)
  * SLR(1)
  * LALR
* Motores de parsing:

  * Predictivo LL(1)
  * Shift-Reduce LR
* Manejo y recuperación básica de errores sintácticos

## GUI IDE

* Editor integrado
* Carga de archivos `.yal`, `.yapar` y `.txt`
* Visualización de:

  * Tokens
  * FIRST/FOLLOW
  * LR(0)
  * Tablas SLR/LALR/LL(1)
* Ejecución simultánea de parsers
* Resultados ACCEPT/REJECT
* Estadísticas del parser

---

# Pipeline General

```text
archivo.yal + archivo.yapar + archivo de entrada
        ↓
    YALex genera tokens
        ↓
    YAPar construye el parser
        ↓
    FIRST / FOLLOW
        ↓
    Autómata LR(0)
        ↓
    Tablas LL(1) / SLR / LALR
        ↓
    Análisis sintáctico
        ↓
    ACCEPT / ERROR
```

---

# Estructura del Proyecto

```text
proyecto/
├── automata/
│   ├── afn.py
│   ├── afd.py
│   ├── thompson.py
│   ├── subset.py
│   └── lr0.py
│
├── regex/
│   ├── regex_node.py
│   └── regex_parser.py
│
├── yalex/
│   ├── yalex_parser.py
│   ├── lexer_builder.py
│   ├── generator.py
│   ├── visualizer.py
│   └── yalex_reader.py
│
├── yapar/
│   ├── yapar_parser.py
│   ├── first_follow.py
│   ├── slr_table.py
│   ├── lalr_table.py
│   ├── ll1_table.py
│   └── parser_engine.py
│
├── gui/
│   ├── __init__.py
│   └── app.py
│
├── java.yal
├── java_grammar.yapar
├── input_java.txt
├── ejemplo_correcto.txt
├── ejemplo_errores.txt
├── yalex.py
├── yapar.py
└── README.md
```

---

# Instalación

## Requisitos

* Python 3.8+
* Graphviz

## Instalar dependencias

### Python

```bash
pip install graphviz
```

### Ubuntu / Debian

```bash
sudo apt install graphviz
```

### macOS

```bash
brew install graphviz
```

---

# Uso — YALex

## Generar lexer

```bash
python yalex.py java.yal -o java_lexer.py
```

## Ejecutar lexer

```bash
python java_lexer.py archivo.txt
```

## Ejecutar en modo verbose

```bash
python java_lexer.py archivo.txt --verbose
```

## Generar visualizaciones

```bash
python yalex.py java.yal -o java_lexer.py --all
```

Flags disponibles:

```text
--tree    Árboles de expresiones regulares
--afd     Grafo del AFD
--all     Todo junto
```

---

# Uso — YAPar

## Ejecutar parser SLR

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt
```

## Ejecutar parser LALR

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --method lalr
```

## Ejecutar parser LL(1)

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --method ll1
```

## Ejecutar los tres métodos

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --all
```

## Mostrar pasos del parsing

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --steps
```

## Mostrar tablas de parseo

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --tables
```

## Mostrar autómata LR(0)

```bash
python yapar.py java_grammar.yapar -l java.yal -i input_java.txt --lr0
```

---

# Interfaz Gráfica

Ejecutar la IDE:

```bash
python gui/app.py
```

La interfaz permite:

* editar archivos,
* ejecutar parsers,
* visualizar tablas,
* visualizar LR(0),
* observar tokens,
* comparar métodos,
* mostrar errores sintácticos.

---

# Resultados Obtenidos

Usando la gramática Java incluida:

```text
Estados LR(0):      230
Transiciones:       1166
Tokens generados:   153

Conflictos:
  SLR(1):   9
  LALR:     5
  LL(1):    342
```

Resultados del análisis:

| Método | Resultado |
| ------ | --------- |
| SLR(1) | ACEPTADA  |
| LALR   | ACEPTADA  |
| LL(1)  | RECHAZADA |

---

# Gramática Java

La gramática implementada soporta:

* clases,
* métodos,
* declaraciones,
* expresiones,
* if/else,
* while,
* for,
* return,
* arreglos,
* llamadas a métodos,
* creación de objetos.

La gramática incluye recursión izquierda:

```text
expr:
    expr OP_PLUS term
```

Por esta razón:

* LL(1) presenta muchos conflictos,
* mientras que SLR y LALR pueden procesarla correctamente.

---
# Video de Demostración

[Link del Video de demostración](https://youtu.be/i4ffWxEBaM0)

# Autores

* Osman Emanuel de León García — 23428

---

# Curso

Diseño de Lenguajes de Programación
Universidad del Valle de Guatemala
2026
