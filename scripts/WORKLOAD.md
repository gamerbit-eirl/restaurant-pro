# Carga de trabajo - Restaurant Pro

## 1) Seed catalogo desde SQL (opcional)
Ejecuta el archivo:

`backend/db/seeds/20260326_menu_base.sql`

Esto carga:
- platos del menu del dia (`incluye_entrada=1`)
- adicionales (`incluye_entrada=0`)
- entradas base
- bebidas de barra
- mesas 1..15

## 2) Seed + carga masiva desde script
Desde la raiz del repo:

```bat
scripts\db-workload.cmd --solo-seed
```

Carga de trabajo (300 pedidos por defecto):

```bat
scripts\db-workload.cmd --ordenes 300 --min-items 2 --max-items 6
```

Carga fuerte:

```bat
scripts\db-workload.cmd --ordenes 2000 --min-items 3 --max-items 8 --mesas 30
```
