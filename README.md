# PROCESOS DE NEGOCIOS INTEGRADOS_S12

**Curso:** Sistemas de Información Integrados (NRC 12054 – 12055)
**Docente:** Dr. Mendoza Corpus Carlos Alfredo
**Estudiante:** Carranza Jacinto Juan Diego (ID 000257022)
**Universidad Privada Antenor Orrego – Escuela de Ingeniería de Sistemas e Inteligencia Artificial, 2026**

Repositorio con la solución de los casos del informe: modelos BPMN 2.0, mapa conceptual y programa de cálculo de indicadores.

## Contenido

| Carpeta | Contenido |
|---|---|
| `informe/` | Informe en PDF |
| `bpmn/` | Modelos BPMN 2.0 en XML (`.bpmn`), importables en Bizagi Modeler (Archivo › Importar), Camunda Modeler o https://demo.bpmn.io |
| `diagramas/` | Imágenes SVG de los modelos |
| `generador/` | Programa en Python que genera los `.bpmn` y los `.svg` a partir de la definición de cada proceso |
| `mapa_conceptual/` | Mapa conceptual del caso en Graphviz (`.dot`) y su imagen (`.svg`) |
| `kpis/` | Programa de cálculo de los KPI del caso Distribuidora Nacional de Alimentos |

### Modelos BPMN

1. `01_desarrollo_software_SGH_CRM.bpmn`: proceso de desarrollo del módulo CRM del Sistema de Gestión Hotelera con IA.
2. `02_subproceso_construccion_CI_CD.bpmn`: subproceso mejorado de construcción y pruebas con integración y despliegue continuos.
3. `03_DNA_reposicion_AS-IS.bpmn`: proceso actual de pedido y reposición de la Distribuidora Nacional de Alimentos.
4. `04_DNA_reposicion_TO-BE.bpmn`: proceso futuro integrado con ERP, SCM y automatización.

## Ejecución

Requiere Python 3.10 o superior, sin librerías externas.

```bash
# Regenerar modelos BPMN e imágenes
cd generador
python procesos.py

# Calcular los KPI con datos simulados (o con un CSV propio)
cd ../kpis
python kpis_dna.py
python kpis_dna.py mis_pedidos.csv
```

Para regenerar la imagen del mapa conceptual se necesita Graphviz:

```bash
dot -Tsvg mapa_conceptual/mapa_conceptual.dot -o mapa_conceptual/mapa_conceptual.svg
```

Los datos de `kpis/pedidos_simulados.csv` son generados por el programa para comprobar el cálculo; no corresponden a información real de la empresa.
