"""Cálculo de indicadores (KPI) del proceso de pedido y reposición
de la Distribuidora Nacional de Alimentos.

Uso:
    python kpis_dna.py                 # genera datos simulados y calcula los KPI
    python kpis_dna.py pedidos.csv     # calcula los KPI con un archivo propio

El archivo de pedidos debe tener las columnas:
    pedido_id, registro, liberado_almacen, entrega, fecha_comprometida,
    unidades_solicitadas, unidades_entregadas, lineas, lineas_correctas,
    registro_automatico, reclamo_tardanza, costo_operativo
(fechas en formato ISO: AAAA-MM-DD HH:MM)

Los datos simulados solo sirven para comprobar el cálculo; no representan
información real de la empresa.
"""
import csv
import random
import sys
from datetime import datetime, timedelta
from statistics import mean

FMT = "%Y-%m-%d %H:%M"

# KPI: (nombre, unidad, meta, sentido)  sentido: "max" = mayor es mejor, "min" = menor es mejor
METAS = {
    "tiempo_ciclo_h": ("Tiempo de ciclo del pedido", "h", 24, "min"),
    "tiempo_procesamiento_h": ("Tiempo de procesamiento administrativo", "h", 2, "min"),
    "entregas_a_tiempo": ("Entregas a tiempo (OTD)", "%", 95, "max"),
    "otif": ("Pedidos completos y a tiempo (OTIF)", "%", 92, "max"),
    "fill_rate": ("Nivel de servicio por unidades (fill rate)", "%", 97, "max"),
    "quiebre_stock": ("Pedidos con quiebre de stock", "%", 3, "min"),
    "exactitud_picking": ("Exactitud de preparación (picking)", "%", 99.5, "max"),
    "registro_automatico": ("Pedidos registrados sin intervención manual", "%", 90, "max"),
    "reclamos_tardanza": ("Reclamos por entrega tardía", "%", 2, "min"),
    "costo_por_pedido": ("Costo operativo por pedido", "S/", 45, "min"),
    "exactitud_inventario": ("Exactitud del inventario (IRA)", "%", 98, "max"),
    "oc_a_tiempo": ("Órdenes de compra recibidas a tiempo", "%", 95, "max"),
    "rotacion": ("Rotación de inventario (anualizada)", "veces", 18, "max"),
}


def simular_pedidos(n=400, semilla=12):
    rnd = random.Random(semilla)
    inicio = datetime(2026, 10, 1, 8, 0)
    filas = []
    for i in range(1, n + 1):
        reg = inicio + timedelta(hours=rnd.uniform(0, 30 * 24))
        lib = reg + timedelta(hours=rnd.uniform(4, 30))
        ent = lib + timedelta(hours=rnd.uniform(6, 36))
        comp = reg + timedelta(hours=48)
        sol = rnd.randint(20, 300)
        falt = rnd.random() < 0.12
        entreg = sol - (rnd.randint(1, max(1, sol // 5)) if falt else 0)
        lineas = rnd.randint(3, 25)
        ok = lineas - (1 if rnd.random() < 0.06 else 0)
        tarde = ent > comp
        filas.append(dict(
            pedido_id=f"P{i:05d}", registro=reg.strftime(FMT), liberado_almacen=lib.strftime(FMT),
            entrega=ent.strftime(FMT), fecha_comprometida=comp.strftime(FMT),
            unidades_solicitadas=sol, unidades_entregadas=entreg, lineas=lineas, lineas_correctas=ok,
            registro_automatico=int(rnd.random() < 0.05),
            reclamo_tardanza=int(tarde and rnd.random() < 0.55),
            costo_operativo=round(rnd.uniform(40, 85), 2)))
    return filas


def simular_inventario(semilla=12):
    rnd = random.Random(semilla + 1)
    conteos = [(rnd.randint(50, 900), rnd.random()) for _ in range(250)]
    # (stock en sistema, aleatorio para diferencia)
    items = []
    for stock, r in conteos:
        dif = 0 if r > 0.15 else rnd.randint(1, max(2, stock // 10))
        items.append((stock, stock - dif))
    compras = [rnd.random() > 0.2 for _ in range(60)]  # True = OC recibida a tiempo
    costo_ventas_mensual = 2_350_000
    inventario_promedio = 1_900_000
    return items, compras, costo_ventas_mensual, inventario_promedio


def leer_csv(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def calcular(pedidos, items, compras, costo_ventas_mensual, inventario_promedio, tolerancia=0.02):
    p = lambda f, k: datetime.strptime(f[k], FMT)
    n = len(pedidos)
    a_tiempo = [p(f, "entrega") <= p(f, "fecha_comprometida") for f in pedidos]
    completos = [int(f["unidades_entregadas"]) >= int(f["unidades_solicitadas"]) for f in pedidos]
    k = {
        "tiempo_ciclo_h": mean((p(f, "entrega") - p(f, "registro")).total_seconds() / 3600 for f in pedidos),
        "tiempo_procesamiento_h": mean((p(f, "liberado_almacen") - p(f, "registro")).total_seconds() / 3600 for f in pedidos),
        "entregas_a_tiempo": pct(sum(a_tiempo), n),
        "otif": pct(sum(t and c for t, c in zip(a_tiempo, completos)), n),
        "fill_rate": pct(sum(int(f["unidades_entregadas"]) for f in pedidos),
                         sum(int(f["unidades_solicitadas"]) for f in pedidos)),
        "quiebre_stock": pct(sum(not c for c in completos), n),
        "exactitud_picking": pct(sum(int(f["lineas_correctas"]) for f in pedidos),
                                 sum(int(f["lineas"]) for f in pedidos)),
        "registro_automatico": pct(sum(int(f["registro_automatico"]) for f in pedidos), n),
        "reclamos_tardanza": pct(sum(int(f["reclamo_tardanza"]) for f in pedidos), n),
        "costo_por_pedido": mean(float(f["costo_operativo"]) for f in pedidos),
        "exactitud_inventario": pct(sum(abs(s - c) <= tolerancia * s for s, c in items), len(items)),
        "oc_a_tiempo": pct(sum(compras), len(compras)),
        "rotacion": 12 * costo_ventas_mensual / inventario_promedio,
    }
    return k


def reporte(k):
    filas = []
    for clave, valor in k.items():
        nombre, unidad, meta, sentido = METAS[clave]
        cumple = valor <= meta if sentido == "min" else valor >= meta
        filas.append((nombre, f"{valor:,.1f} {unidad}", f"{'≤' if sentido == 'min' else '≥'} {meta} {unidad}",
                      "Cumple" if cumple else "No cumple"))
    ancho = max(len(f[0]) for f in filas)
    print(f"{'Indicador':<{ancho}}  {'Valor':>14}  {'Meta':>14}  Estado")
    print("-" * (ancho + 44))
    for f in filas:
        print(f"{f[0]:<{ancho}}  {f[1]:>14}  {f[2]:>14}  {f[3]}")
    return filas


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pedidos = leer_csv(sys.argv[1])
    else:
        pedidos = simular_pedidos()
        with open("pedidos_simulados.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(pedidos[0].keys()))
            w.writeheader()
            w.writerows(pedidos)
    items, compras, cv, inv = simular_inventario()
    filas = reporte(calcular(pedidos, items, compras, cv, inv))
    with open("resultado_kpis.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["indicador", "valor", "meta", "estado"])
        w.writerows(filas)
