"""Definición de los procesos modelados en el informe PROCESOS DE NEGOCIOS INTEGRADOS_S12.

Ejecutar:  python procesos.py
Genera los archivos .bpmn en ../bpmn y las imágenes .svg en ../diagramas.
"""
import os
from bpmn_gen import Diagram

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_BPMN = os.path.join(BASE, "..", "bpmn")
OUT_SVG = os.path.join(BASE, "..", "diagramas")


def desarrollo_sgh_crm():
    d = Diagram("01_desarrollo_software_SGH_CRM",
                "Proceso de desarrollo del módulo CRM del Sistema de Gestión Hotelera con IA",
                laneh=112)
    d.pool("doc", "Docente del curso", blackbox=True)
    d.pool("eq", "Equipo del módulo CRM", [
        ("jp", "Jefe de proyecto (Scrum Master)"),
        ("an", "Analista de negocio"),
        ("ar", "Arquitecto y diseñador UX/UI"),
        ("dv", "Desarrolladores y tester"),
    ])
    d.pool("mod", "Módulos del supergrupo hotelero", blackbox=True)
    d.node("s", "startMsg", "Avance asignado", "jp", 0)
    d.node("t1", "userTask", "Revisar alcance y actualizar el backlog", "jp", 0.85)
    d.node("t2", "userTask", "Levantar requerimientos y casos de uso", "an", 1.6)
    d.node("t3", "task", "Modelar procesos de negocio en BPMN", "an", 2.6)
    d.node("t4", "task", "Diseñar modelo de datos y contratos de integración", "ar", 3.35)
    d.node("t5", "task", "Prototipar interfaces UX/UI", "ar", 4.35)
    d.node("t6", "userTask", "Planificar el sprint y asignar tareas", "jp", 5.1)
    d.node("sp", "subProcess", "Construir y probar el incremento", "dv", 5.85)
    d.node("t7", "sendTask", "Consolidar documentación y presentar el avance", "jp", 6.6)
    d.node("e1", "interMsgCatch", "Retroalimentación recibida", "jp", 7.45)
    d.node("g1", "xor", "¿Requiere ajustes?", "jp", 8.1)
    d.node("g2", "xor", "¿Último avance?", "jp", 8.85)
    d.node("t8", "task", "Desplegar versión final y cerrar el proyecto", "jp", 9.7)
    d.node("e", "end", "Módulo CRM entregado", "jp", 10.55)
    for a, b in [("s", "t1"), ("t1", "t2"), ("t2", "t3"), ("t3", "t4"), ("t4", "t5"), ("t5", "t6"),
                 ("t6", "sp"), ("sp", "t7"), ("t7", "e1"), ("e1", "g1")]:
        d.flow(a, b)
    d.flow("g1", "t6", "Sí", via="jp:top:10", lpos=(5, -6))
    d.flow("g1", "g2", "No")
    d.flow("g2", "t1", "No", via="jp:top:4", lpos=(5, -6))
    d.flow("g2", "t8", "Sí")
    d.flow("t8", "e")
    d.msg("doc", "s", "Indicaciones del avance")
    d.msg("t7", "doc", "Entregables del avance")
    d.msg("doc", "e1", "Observaciones")
    d.msg("t4", "mod", "Contratos de eventos y API", dx=0)
    d.msg("sp", "mod", "Pruebas de integración", dx=0)
    return d


def pipeline_mejorado():
    d = Diagram("02_subproceso_construccion_CI_CD",
                "Subproceso mejorado: construir y probar el incremento con integración continua",
                laneh=118)
    d.pool("eq", "Equipo del módulo CRM", [
        ("dv", "Desarrollador"),
        ("ci", "Plataforma CI/CD (automatizada)"),
        ("qa", "Tester (QA)"),
    ])
    d.pool("mod", "Módulos del supergrupo hotelero", blackbox=True)
    d.node("s", "start", "Sprint planificado", "dv", 0)
    d.node("t1", "userTask", "Tomar la historia del tablero y crear la rama", "dv", 0.85)
    d.node("t2", "userTask", "Codificar y escribir pruebas unitarias", "dv", 1.85)
    d.node("t3", "userTask", "Abrir solicitud de integración (pull request)", "dv", 2.85)
    d.node("t4", "serviceTask", "Compilar y ejecutar pruebas automáticas", "ci", 3.6)
    d.node("g1", "xor", "¿Pipeline exitoso?", "ci", 4.45)
    d.node("t5", "userTask", "Revisar el código (revisión por pares)", "dv", 5.2)
    d.node("g2", "xor", "¿Cambios aprobados?", "dv", 6.0, label="above")
    d.node("t6", "serviceTask", "Fusionar y desplegar en pruebas", "ci", 6.75)
    d.node("t7", "userTask", "Ejecutar pruebas funcionales y de integración", "qa", 7.6)
    d.node("g3", "xor", "¿Cumple criterios de aceptación?", "qa", 8.45)
    d.node("e", "end", "Incremento listo", "qa", 9.3)
    for a, b in [("s", "t1"), ("t1", "t2"), ("t2", "t3"), ("t3", "t4"), ("t4", "g1")]:
        d.flow(a, b)
    d.flow("g1", "t2", "No", via="dv:top:16", lpos=(5, -6))
    d.flow("g1", "t5", "Sí", route="hv", lpos=(4, -5))
    d.flow("t5", "g2")
    d.flow("g2", "t2", "No", via="dv:bottom:8", lpos=(5, 14))
    d.flow("g2", "t6", "Sí", route="hv", lpos=(4, -5))
    d.flow("t6", "t7")
    d.flow("t7", "g3")
    d.flow("g3", "t2", "No", via="dv:top:8", lpos=(5, -8))
    d.flow("g3", "e", "Sí")
    d.msg("t6", "mod", "Pruebas de contrato", dx=0, lpos=(-80, 30))
    return d


def dna_as_is():
    d = Diagram("03_DNA_reposicion_AS-IS",
                "Distribuidora Nacional de Alimentos: proceso actual de pedido y reposición",
                laneh=112)
    d.pool("cli", "Supermercado (cliente)", blackbox=True)
    d.pool("dna", "Distribuidora Nacional de Alimentos", [
        ("com", "Área comercial"),
        ("alm", "Almacén"),
        ("cmp", "Compras"),
        ("dis", "Distribución"),
    ])
    d.pool("prv", "Proveedor", blackbox=True)
    d.node("s", "startMsg", "Pedido recibido por teléfono o correo", "com", 0)
    d.node("t1", "manualTask", "Registrar el pedido en una hoja de cálculo", "com", 0.85)
    d.node("t2", "sendTask", "Enviar el pedido por correo al almacén", "com", 1.85)
    d.node("t3", "manualTask", "Revisar el correo y el kárdex manual", "alm", 2.6)
    d.node("g1", "xor", "¿Hay stock?", "alm", 3.45)
    d.node("t4", "manualTask", "Reenviar el requerimiento por correo", "cmp", 4.2)
    d.node("t5", "manualTask", "Cotizar y emitir la orden de compra", "cmp", 5.2)
    d.node("t6", "manualTask", "Recibir mercadería y anotar en el kárdex", "alm", 5.95)
    d.node("g2", "xor", "", "alm", 6.75)
    d.node("t7", "manualTask", "Preparar el pedido manualmente", "alm", 7.5)
    d.node("t8", "manualTask", "Despachar y anotar la salida", "alm", 8.5)
    d.node("t9", "manualTask", "Programar el transporte y entregar", "dis", 9.25)
    d.node("e", "end", "Pedido entregado con demora", "dis", 10.1, label="above")
    for a, b in [("s", "t1"), ("t1", "t2"), ("t2", "t3"), ("t3", "g1")]:
        d.flow(a, b)
    d.flow("g1", "t4", "No", route="hv")
    d.flow("g1", "g2", "Sí", via="alm:top:12", lpos=(5, -6))
    d.flow("t4", "t5")
    d.flow("t5", "t6", route="hv")
    d.flow("t6", "g2")
    d.flow("g2", "t7")
    d.flow("t7", "t8")
    d.flow("t8", "t9")
    d.flow("t9", "e")
    d.msg("cli", "s", "Pedido")
    d.msg("t5", "prv", "Orden de compra")
    d.msg("prv", "t6", "Mercadería", dx=-30)
    d.msg("t9", "cli", "Entrega", dx=40)
    return d


def dna_to_be():
    d = Diagram("04_DNA_reposicion_TO-BE",
                "Distribuidora Nacional de Alimentos: proceso futuro integrado de pedido y reposición",
                laneh=112)
    d.pool("cli", "Supermercado (cliente)", blackbox=True)
    d.pool("dna", "Distribuidora Nacional de Alimentos", [
        ("com", "Área comercial"),
        ("erp", "ERP (automatizado)"),
        ("cmp", "Compras"),
        ("alm", "Almacén"),
        ("dis", "Distribución"),
    ])
    d.pool("prv", "Proveedor", blackbox=True)
    d.node("s", "startMsg", "Pedido recibido por el portal B2B o EDI", "com", 0)
    d.node("t1", "serviceTask", "Registrar pedido y validar crédito", "erp", 0.75)
    d.node("t2", "serviceTask", "Verificar y reservar stock en tiempo real", "erp", 1.75)
    d.node("g1", "xor", "¿Stock completo?", "erp", 2.6, label="above")
    d.node("t3", "serviceTask", "Generar OC sugerida y notificar fecha", "erp", 3.4)
    d.node("t4", "userTask", "Aprobar y enviar la orden de compra", "cmp", 4.15)
    d.node("t5", "userTask", "Recibir y registrar la mercadería", "alm", 5.15)
    d.node("g2", "xor", "", "alm", 5.95)
    d.node("t6", "userTask", "Preparar pedido con código de barras", "alm", 6.75)
    d.node("t7", "userTask", "Despachar pedido y registrar salida", "alm", 7.75)
    d.node("t8", "userTask", "Planificar la ruta y entregar el pedido", "dis", 8.5)
    d.node("t9", "userTask", "Registrar la prueba de entrega digital", "dis", 9.5)
    d.node("t10", "serviceTask", "Emitir factura electrónica y actualizar KPI", "erp", 10.25)
    d.node("e", "end", "Pedido entregado y facturado", "erp", 11.05)
    d.flow("s", "t1")
    d.flow("t1", "t2")
    d.flow("t2", "g1")
    d.flow("g1", "t3", "No")
    d.flow("g1", "g2", "Sí", via="alm:bottom:10", lpos=(5, 14))
    d.flow("t3", "t4")
    d.flow("t4", "t5")
    d.flow("t5", "g2")
    d.flow("g2", "t6")
    d.flow("t6", "t7")
    d.flow("t7", "t8")
    d.flow("t8", "t9")
    d.flow("t9", "t10")
    d.flow("t10", "e")
    d.msg("cli", "s", "Pedido electrónico")
    d.msg("t3", "cli", "Fecha comprometida", dx=0)
    d.msg("t4", "prv", "Orden de compra electrónica", dx=0)
    d.msg("prv", "t5", "Mercadería y guía", dx=-30)
    d.msg("t9", "cli", "Pedido y comprobante", dx=0)
    return d


if __name__ == "__main__":
    for fn in (desarrollo_sgh_crm, pipeline_mejorado, dna_as_is, dna_to_be):
        dg = fn()
        dg.save(OUT_BPMN, OUT_SVG)
        print("Generado:", dg.id)
