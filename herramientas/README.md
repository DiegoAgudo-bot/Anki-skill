# Herramientas del vendedor

Esta carpeta **no forma parte del add-on**: no entra en el `.ankiaddon`.

## Licencias de Pagewise Pro

Una licencia es un texto firmado (`PW1.….…`) que el comprador pega en *Herramientas → Pagewise → Pagewise Pro…*. El add-on la comprueba en el ordenador del usuario, sin conexión, con la clave pública que lleva dentro (`pagewise/licencia.py`). Solo quien tiene la **clave privada** puede emitir licencias.

### La clave privada

- Guárdala fuera del repositorio (los archivos `*.clave-privada` están en `.gitignore`), con una copia de seguridad.
- Si alguien la consigue, puede emitir licencias. Si la pierdes, no podrás emitir más para las versiones ya distribuidas.
- Cambiarla invalida todas las licencias emitidas con la anterior, así que hazlo solo antes de empezar a vender o ante una filtración.

```bash
python herramientas/licencias.py generar-claves mi.clave-privada
```

Escribe la clave pública nueva en `pagewise/licencia.py`. Después hay que regenerar el paquete (`./build.sh`).

### Emitir una licencia

Sin caducidad (pago único):

```bash
python herramientas/licencias.py emitir mi.clave-privada ana@correo.es
```

Con caducidad (suscripción) y tu referencia de pedido:

```bash
python herramientas/licencias.py emitir mi.clave-privada ana@correo.es --caduca 2027-12-31 --id pedido-123
```

El texto que imprime es lo que le envías al comprador. Su correo queda dentro de la licencia y se muestra en el add-on al activarla.

### Comprobar una licencia

```bash
python herramientas/licencias.py comprobar "PW1.xxxx.yyyy"
```

### Qué protege y qué no

El código del add-on es legible, así que quien quiera saltarse la comprobación puede hacerlo editándolo. La licencia es la vía cómoda y legítima de activar Pro, no un candado. Al caducar una licencia no se pierde nada: las fuentes siguen funcionando y solo se bloquea añadir más de las que permite la versión gratuita.

### Automatizarlo más adelante

Hoy las licencias se emiten a mano. Cuando haya volumen, la plataforma de pago puede llamar a un pequeño servicio que ejecute `licencia.emitir(...)` y envíe el texto por correo. Ese servicio sería lo único que necesita la clave privada.
