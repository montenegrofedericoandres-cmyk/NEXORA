# Publicar NEXORA en Cloudflare Pages (Free)

Estado: repositorio preparado; conexión con Cloudflare y URL pública todavía pendientes.

## Configuración del proyecto
| Campo | Valor |
| --- | --- |
| Proveedor | GitHub |
| Cuenta | montenegrofedericoandres-cmyk |
| Repositorio | NEXORA |
| Rama de producción | main |
| Despliegues automáticos de producción | Activados |
| Framework | None |
| Comando de compilación | python3 scripts/build_site.py |
| Directorio de salida | dist |
| Directorio raíz | Raíz del repositorio (dejar vacío) |
| Plan | Free |
| Dominio | Subdominio gratuito asignado por Pages (*.pages.dev) |
| Variables secretas / Functions / base de datos | Ninguna |

## Conectar
1. Entrar en el panel de Cloudflare, Workers & Pages.
2. Crear aplicación, elegir Pages e importar un repositorio Git existente.
3. Autorizar la aplicación Cloudflare Workers and Pages de GitHub únicamente para NEXORA.
4. Elegir el repositorio y cargar la configuración de la tabla.
5. Guardar y desplegar. Confirmar éxito y anotar la URL real asignada.
6. Verificar que producción use main y que los despliegues automáticos estén activados.
7. No contratar dominio, R2, Workers Paid ni otro complemento de pago.

## Qué se publica
El comando comprueba primero index.html y publica únicamente index.html, 404.html y _headers en dist. No publica la documentación, scripts, paquetes, claves ni archivos de producto. _headers configura controles del navegador y bloquea formularios y scripts en la página estática.

Las ventas y las entregas permanecen desactivadas. El único contacto habilitado es un enlace mailto; no envía mensajes automáticamente.

## Verificación
- Ejecutar python3 scripts/check_site.py y python3 scripts/build_site.py.
- GitHub Actions ejecuta comprobaciones en Chromium a 320, 360, 390, 412, 768 y 1280 px, contacto por teclado y página 404.
- Consultar el resultado real en Actions antes de dar por aprobada la verificación móvil. Son vistas simuladas, no dispositivos físicos.
- Después del despliegue verificar HTTPS, contenido, correo, ausencia de desplazamiento horizontal y respuesta 404 en la URL publicada.
- Para comprobar el automatismo, publicar un cambio comprobado en main y verificar que Pages despliegue ese mismo commit.

## Coste y límites
Pages Free permite 500 compilaciones al mes; las solicitudes estáticas son gratuitas. Las pruebas usan un runner estándar ubuntu-latest del repositorio público de GitHub. No se configura facturación ni una tarjeta.

Fuentes oficiales consultadas:
- https://developers.cloudflare.com/pages/get-started/git-integration/
- https://developers.cloudflare.com/pages/platform/limits/
- https://developers.cloudflare.com/pages/functions/pricing/
- https://docs.github.com/en/billing/concepts/product-billing/github-actions

## Habilitar ventas en otra etapa
Mantener las validaciones de prelanzamiento hasta comprobar el producto, condiciones de venta y el circuito completo de pago y entrega. No subir archivos pagos al repositorio público.
