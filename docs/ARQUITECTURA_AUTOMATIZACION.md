# NEXORA — Arquitectura de venta segura

## Estado
Este repositorio contiene solo una página de prelanzamiento. El link de pago de Mercado Pago ya existe, pero **no está conectado a una verificación de transacciones ni a una entrega digital**. No habilitar ventas hasta superar una prueba real o de sandbox del flujo completo.

## Arquitectura propuesta (a implementar)
1. Hosting comercial gratuito compatible con página estática y backend serverless.
2. Checkout identificado por orden individual, con email de comprador y referencia de producto.
3. Webhook de Mercado Pago autenticado con firma, validación de timestamp y consulta posterior a API oficial.
4. Confirmar estado aprobado, moneda ARS, importe 9900, identificador de producto y cuenta receptora. No confiar en parámetros enviados desde navegador.
5. Registrar el identificador de pago de forma idempotente para evitar entregas repetidas.
6. Entregar archivo privado mediante URL firmada con vencimiento y límite de descargas, o correo transaccional con enlace seguro.
7. Reintentos controlados, alertas de error, registros mínimos y eliminación de datos cuando corresponda.
8. Gestionar reembolsos, contracargos y soporte.

## Límites importantes
- El enlace fijo https://mpago.la/2vuapFA por sí solo no demuestra a qué comprador pertenece cada pago.
- Nunca publicar el .xlsx pago en un repositorio público.
- Nunca poner access tokens o secretos en HTML, GitHub público o mensajes de chat.
- La entrega automática requiere configuración de infraestructura, permisos y pruebas; no está activa.
- Las funciones gratuitas tienen límites y sus términos pueden cambiar.

Documentación oficial:
https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-preferences/payment-notifications
https://developers.cloudflare.com/pages/
