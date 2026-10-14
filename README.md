# NEXORA — Tienda digital (prelanzamiento)

Landing pública en preparación para el Kit de Gestión para Emprendedores.

## Estado
- Sitio estático: `index.html`
- Contacto: nexoraproductosdigitales@gmail.com
- Precio de referencia: ARS 9.900
- Cobros: **deshabilitados** hasta verificar el flujo completo
- Entrega digital: **pendiente**
- Archivos de pago: **no subir a este repositorio público**

## Lista de verificación previa a ventas
- [ ] Validar planilla y fórmulas con datos de prueba en Excel y Google Sheets
- [ ] Definir y publicar condiciones de venta, soporte, devoluciones y plazo de entrega
- [ ] Configurar una plataforma que confirme pagos aprobados de Mercado Pago y entregue archivos protegidos
- [ ] Hacer compra de prueba y verificar confirmación, entrega y soporte
- [ ] Verificar disponibilidad del nombre NEXORA
- [ ] Elegir hosting compatible con uso comercial y publicar URL

## Seguridad
No subir tokens, claves de Mercado Pago, contraseñas, datos personales de clientes ni archivos exclusivos para compradores. Un link de pago por sí solo no verifica una transacción para liberar una descarga.

## Publicación
Publicación actual en **Cloudflare Workers Static Assets**, conectada a `main`:
https://nexora.nexoraproductosdigitales.workers.dev/

El despliegue usa `wrangler.jsonc`, ejecuta `python3 scripts/build_site.py` y publica únicamente `dist/`. No ejecuta un backend ni configura bases de datos o servicios de pago. `.assetsignore` excluye por defecto todos los archivos salvo las páginas públicas y sus cabeceras.

**Workers y Pages son productos distintos. Cloudflare Pages sigue pendiente**; las instrucciones para configurarlo se conservan a continuación.

Configuración y comprobaciones: [docs/CLOUDFLARE_PAGES.md](docs/CLOUDFLARE_PAGES.md).

GitHub Actions comprueba el paquete, simula seis tamaños de pantalla y valida la URL publicada en `main`, incluidas respuestas 404 para archivos internos y de producto. Consultar el resultado de cada ejecución en Actions. Las pruebas son simuladas y no sustituyen una prueba en un celular físico.
