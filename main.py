"""
main.py
Compara árboles AVL y Red-Black con los mismos datos y las mismas operaciones.

Ejecución:
    python main.py
El programa pregunta cuántas llaves insertar (entre 100.000 y 1.000.000).

Fases: 1) generar datos  2) ejecutar y medir  3) calcular métricas  4) presentar.
"""
import sys

if sys.version_info < (3, 10):
    sys.exit("Se requiere Python 3.10 o superior.")

import gc
import math
import random
from time import perf_counter

from arboles import AVLTree, RBTree

N_MIN, N_MAX = 100_000, 1_000_000
SEMILLA = 42                    # cambia este valor para otra corrida reproducible
N_BORRADOS = 10_000
N_BUSQUEDAS = 100
REPETICIONES_BUSQUEDA = 1_000   # se repite el lote de 100 búsquedas para medir un tiempo estable


# ---------------------------------------------------------------------
# FASE 1: generación de datos (una sola vez; se reutilizan en ambos árboles)
# ---------------------------------------------------------------------
def generar_datos(n, semilla):
    rng = random.Random(semilla)
    claves = rng.sample(range(1, 10 * n + 1), n)     # llaves únicas, en orden aleatorio
    a_borrar = rng.sample(claves, N_BORRADOS)        # 10.000 llaves que sí existen
    a_buscar = rng.sample(claves, N_BUSQUEDAS)       # 100 llaves (algunas pueden haber sido borradas)
    return claves, a_borrar, a_buscar


# ---------------------------------------------------------------------
# FASE 2: ejecución y medición (cada operación se mide por separado)
# ---------------------------------------------------------------------
def medir(funcion):
    """Ejecuta funcion() con el recolector de basura desactivado; devuelve segundos."""
    gc.collect()          # limpia lo que dejó la fase anterior
    gc.disable()          # evita pausas del GC dentro de la medición
    try:
        t0 = perf_counter()
        funcion()
        return perf_counter() - t0
    finally:
        gc.enable()


def ejecutar_insercion(arbol, claves):
    rot0 = arbol.rotations

    def operacion():
        insertar = arbol.insert
        for k in claves:
            insertar(k)

    t = medir(operacion)
    return {"tiempo": t, "rotaciones": arbol.rotations - rot0}


def ejecutar_borrado(arbol, claves):
    rot0 = arbol.rotations

    def operacion():
        borrar = arbol.delete
        for k in claves:
            borrar(k)

    t = medir(operacion)
    return {"tiempo": t, "rotaciones": arbol.rotations - rot0}


def ejecutar_busquedas(arbol, claves):
    # (a) Tiempo: usa search() original, sin contadores, repetido para mayor precisión.
    def operacion():
        buscar = arbol.search
        for _ in range(REPETICIONES_BUSQUEDA):
            for k in claves:
                buscar(k)

    t_lote = medir(operacion) / REPETICIONES_BUSQUEDA

    # (b) Comparaciones: pasada aparte con search_contando(), fuera de la medición de tiempo.
    comps = visitados = 0
    aciertos = []
    for k in claves:
        nodo, c, v = arbol.search_contando(k)
        comps += c
        visitados += v
        aciertos.append(nodo is not None)
    return {"tiempo_lote": t_lote, "comparaciones": comps, "visitados": visitados, "aciertos": aciertos}


# ---------------------------------------------------------------------
# FASE 3: recopilación de métricas y validaciones
# ---------------------------------------------------------------------
def probar_arbol(nombre, arbol, claves, a_borrar, a_buscar):
    n = len(claves)
    print(f"\n[{nombre}] insertando {n:,} llaves ...")
    ins = ejecutar_insercion(arbol, claves)
    assert arbol.validar() == n, f"{nombre}: cantidad de nodos incorrecta tras insertar"
    altura_ins = arbol.altura()

    print(f"[{nombre}] borrando {len(a_borrar):,} llaves ...")
    dele = ejecutar_borrado(arbol, a_borrar)
    assert arbol.validar() == n - len(a_borrar), f"{nombre}: cantidad de nodos incorrecta tras borrar"
    assert all(arbol.search(k) is None for k in a_borrar), f"{nombre}: quedaron llaves borradas"
    altura_fin = arbol.altura()

    print(f"[{nombre}] buscando {len(a_buscar)} llaves (x{REPETICIONES_BUSQUEDA} repeticiones) ...")
    bus = ejecutar_busquedas(arbol, a_buscar)
    borradas = set(a_borrar)
    esperado = [k not in borradas for k in a_buscar]
    assert bus["aciertos"] == esperado, f"{nombre}: resultados de búsqueda inesperados"
    print(f"[{nombre}] validaciones correctas (estructura, tamaño, borrados y búsquedas).")

    return {
        "t_ins": ins["tiempo"], "rot_ins": ins["rotaciones"], "h_ins": altura_ins,
        "t_del": dele["tiempo"], "rot_del": dele["rotaciones"], "h_fin": altura_fin,
        "t_bus": bus["tiempo_lote"], "comps": bus["comparaciones"], "visitados": bus["visitados"],
        "aciertos": bus["aciertos"],
    }


# ---------------------------------------------------------------------
# FASE 4: presentación de resultados
# ---------------------------------------------------------------------
def armar_filas(a, r, n):
    nb, nq = N_BORRADOS, N_BUSQUEDAS
    return [
        ("INSERCIÓN", None, None, None),
        ("Tiempo total (s)", a["t_ins"], r["t_ins"], "{:.3f}"),
        ("Tiempo por inserción (µs)", a["t_ins"] / n * 1e6, r["t_ins"] / n * 1e6, "{:.2f}"),
        ("Rotaciones totales", a["rot_ins"], r["rot_ins"], "{:,}"),
        ("Rotaciones por inserción", a["rot_ins"] / n, r["rot_ins"] / n, "{:.3f}"),
        ("Altura tras insertar", a["h_ins"], r["h_ins"], "{}"),
        ("BORRADO", None, None, None),
        ("Tiempo total (s)", a["t_del"], r["t_del"], "{:.3f}"),
        ("Tiempo por borrado (µs)", a["t_del"] / nb * 1e6, r["t_del"] / nb * 1e6, "{:.2f}"),
        ("Rotaciones totales", a["rot_del"], r["rot_del"], "{:,}"),
        ("Rotaciones por borrado", a["rot_del"] / nb, r["rot_del"] / nb, "{:.3f}"),
        ("Altura tras borrar", a["h_fin"], r["h_fin"], "{}"),
        ("BÚSQUEDA (100 llaves)", None, None, None),
        ("Tiempo del lote de 100 (µs)", a["t_bus"] * 1e6, r["t_bus"] * 1e6, "{:.2f}"),
        ("Tiempo por búsqueda (µs)", a["t_bus"] / nq * 1e6, r["t_bus"] / nq * 1e6, "{:.3f}"),
        ("Comparaciones totales", a["comps"], r["comps"], "{:,}"),
        ("Comparaciones por búsqueda", a["comps"] / nq, r["comps"] / nq, "{:.2f}"),
        ("Nodos visitados por búsqueda", a["visitados"] / nq, r["visitados"] / nq, "{:.2f}"),
        ("Aciertos / fallos", f"{sum(a['aciertos'])}/{nq - sum(a['aciertos'])}",
         f"{sum(r['aciertos'])}/{nq - sum(r['aciertos'])}", "{}"),
    ]


def imprimir_tabla(a, r, n, semilla):
    filas = armar_filas(a, r, n)
    ancho = 34 + 3 * 16
    print("\n" + "=" * ancho)
    print(f"COMPARACIÓN AVL vs RED-BLACK   (n = {n:,} llaves, semilla = {semilla})")
    print("=" * ancho)
    print(f"{'Métrica':<34}{'AVL':>16}{'Red-Black':>16}{'RB / AVL':>16}")
    print("-" * ancho)
    for etiqueta, va, vr, fmt in filas:
        if fmt is None:
            print(f"\n{etiqueta}")
            continue
        sa, sr = fmt.format(va), fmt.format(vr)
        if isinstance(va, (int, float)) and va > 0:
            razon = f"{vr / va:.2f}x"
        else:
            razon = "-"
        print(f"  {etiqueta:<32}{sa:>16}{sr:>16}{razon:>16}")
    print("=" * ancho)
    lg = math.log2(n)
    print(f"Referencia teórica: log2(n) = {lg:.1f} | cota de altura AVL ~ {1.44 * lg:.1f} | "
          f"cota de altura RB <= {2 * math.log2(n + 1):.1f}")


# ---------------------------------------------------------------------
def pedir_cantidad_llaves():
    """Pregunta por consola la cantidad de llaves hasta recibir un valor válido."""
    while True:
        texto = input(f"Cantidad de llaves a insertar ({N_MIN:,} a {N_MAX:,}) [Enter = {N_MIN:,}]: ")
        texto = texto.strip().replace(".", "").replace(",", "").replace("_", "")
        if texto == "":
            return N_MIN
        if texto.isdigit() and N_MIN <= int(texto) <= N_MAX:
            return int(texto)
        print(f"  Valor inválido: escribe un entero entre {N_MIN:,} y {N_MAX:,}.")


def main():
    n = pedir_cantidad_llaves()

    print(f"\nGenerando datos (n = {n:,}, semilla = {SEMILLA}) ...")
    claves, a_borrar, a_buscar = generar_datos(n, SEMILLA)

    resultados = {}
    for nombre, clase in (("AVL", AVLTree), ("Red-Black", RBTree)):
        arbol = clase()
        resultados[nombre] = probar_arbol(nombre, arbol, claves, a_borrar, a_buscar)
        del arbol                       # libera memoria antes de probar el siguiente árbol

    # Consistencia entre ambos árboles: mismas búsquedas -> mismos aciertos/fallos
    assert resultados["AVL"]["aciertos"] == resultados["Red-Black"]["aciertos"], \
        "Los dos árboles dieron resultados de búsqueda distintos"

    imprimir_tabla(resultados["AVL"], resultados["Red-Black"], n, SEMILLA)


if __name__ == "__main__":
    main()