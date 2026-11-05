# Productos principales de Saúl Muñoz Pedreros

## Tallertrack: qué es

Tallertrack es el proyecto principal de Saúl. Es un SaaS para talleres mecánicos, antes llamado LYRA ERP. Es una plataforma multi-tenant que digitaliza los talleres: órdenes de trabajo, CRM, inventario, cotizaciones y pagos en un solo lugar. La usan más de 15 talleres.

## Tallertrack: funcionalidades

En Tallertrack, las órdenes de trabajo tienen estados configurables y un enlace público para que el cliente siga su vehículo en tiempo real. Las cotizaciones se convierten en orden con un clic y se envían por correo o WhatsApp.

Tallertrack incluye cobros online con Mercado Pago y Fintoc mediante webhooks idempotentes. También ofrece aislamiento total de datos entre talleres y control de acceso con 7 niveles de permisos.

El marketplace B2B de Tallertrack permite que los talleres pidan cotizaciones de repuestos a vendedores verificados de todo Chile.

## Tallertrack: arquitectura y cifras

Tallertrack usa una caché distribuida con Redis 7 que baja la latencia más de un 60 %, con degradación gradual. Su stack es Next.js 16, React 19, TypeScript, PostgreSQL, Prisma, Redis y Docker.

Tallertrack registra más de 99.954 órdenes de trabajo, más de 15 talleres activos y 10 mil millones de pesos chilenos en transacciones.

## VertiTrack: qué es

VertiTrack es una app de telemedicina vestibular, con apoyo de CORFO. Ganó el Capital Semilla Inicia Chile 2025. Permite que las personas con vértigo registren sus mareos desde el celular, entiendan qué los desencadena y lleguen a la consulta con datos claros. Los especialistas siguen a sus pacientes entre consultas desde un panel.

## VertiTrack: funcionalidades

VertiTrack usa los sensores del smartphone, sin dispositivos externos. Detecta con IA las situaciones que se repiten antes de un episodio. Incluye los cuestionarios clínicos DHI y ABC, y reportes que se comparten con el especialista.

La interfaz de VertiTrack es anti-mareo: tiene alto contraste, botones grandes y no usa animaciones bruscas.

## VertiTrack: tecnología

VertiTrack tiene observabilidad en producción con Pino, Grafana y Loki. Su stack es Next.js, TypeScript, Android, shadcn/ui, Grafana y Loki.

## asjk: qué es

asjk es una CLI open source para iniciar proyectos, con licencia MIT. Va en la versión 3.1.0. Es un comando interactivo que pregunta con qué framework quieres trabajar y crea el proyecto por ti, sin configuración.

## asjk: uso

asjk se usa directo con npx, mediante el comando `npx asjk`, o se instala de forma global con npm. Está hecho con Node.js, JavaScript y npm.

asjk soporta Vite, Astro, Next.js, SvelteKit, Nuxt, Remix, Angular, SolidStart, Qwik y Preact.
