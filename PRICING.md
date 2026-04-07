# AgentKit — Modelo de Pricing Chile

> Ultima actualizacion: Abril 2026
> Tipo de cambio referencial: 1 USD = ~950 CLP | 1 EUR = ~1.030 CLP

---

## 1. Competencia en Chile y LATAM

### Plataformas globales (precios convertidos a CLP)

| Plataforma | Plan basico | Plan medio | Plan alto | IA incluida? |
|-----------|------------|-----------|----------|-------------|
| Botmaker (AR/CL) | $141.550/mes (USD 149) | $236.550/mes (USD 249) | $474.050/mes (USD 499) | No, add-on |
| Respond.io | $75.050/mes (USD 79) | $151.050/mes (USD 159) | $265.050/mes (USD 279) | Solo en Growth+ |
| Landbot | $82.400/mes (EUR 80) | $164.800/mes (EUR 160) | $412.000/mes (EUR 400) | 100-1,000 chats IA |
| Wati.io | $60.770/mes (EUR 59) | $122.570/mes (EUR 119) | $287.370/mes (EUR 279) | Add-on EUR 60 extra |
| Trengo | $113.300/mes (EUR 110) | $169.950/mes (EUR 165) | $284.280/mes (EUR 276) | No |
| ManyChat | $14.250/mes (USD 15) | $61.750/mes (USD 65) | $517.750/mes (USD 545) | Add-on USD 29 |

### Agencias digitales en Chile

| Servicio | Rango de precio |
|---------|----------------|
| Setup chatbot WhatsApp (una vez) | $200.000 — $1.500.000 |
| Mantenimiento mensual agencia | $150.000 — $400.000/mes |
| Chatbot con IA full-service | $300.000 — $800.000/mes |
| Freelancer (implementacion unica) | $150.000 — $500.000 |

### Costos ocultos de la competencia

| Concepto | Costo extra tipico |
|---------|-------------------|
| IA como add-on (Wati) | EUR 60/mes (~$61.800 CLP) por 1,000 respuestas |
| Markup en mensajes WhatsApp (Wati) | ~20% sobre tarifas Meta |
| Exceso de contactos (Respond.io) | USD 12 por cada 100 contactos extra |
| Chats extra (Landbot) | EUR 0.05/chat + EUR 1.00/chat IA |
| Setup WhatsApp (Botmaker) | USD 99 (~$94.050 CLP) pago unico |
| Exceso conversaciones (Botmaker) | USD 0.05-0.07 por conversacion extra |

---

## 2. Costos operativos reales (lo que nos cuesta)

### Infraestructura fija

| Componente | Costo USD/mes | Costo CLP/mes |
|-----------|--------------|---------------|
| Railway Pro (backend + PostgreSQL) | $20-30 | $19.000 — $28.500 |
| Vercel Pro (frontend) | $20 | $19.000 |
| Dominio .cl (NIC Chile, prorrateado) | ~$1 | ~$700 |
| SSL (Let's Encrypt) | $0 | $0 |
| **Total infraestructura** | **~$45** | **~$42.750** |

> Se diluye entre clientes: 20 clientes = $2.138/cliente, 100 clientes = $428/cliente

### Costo variable por cliente

| Concepto | Costo USD | Costo CLP | Notas |
|---------|----------|----------|-------|
| OpenAI GPT-4o-mini (1,000 conv/mes) | ~$10 | ~$9.500 | $0.15/1M input + $0.60/1M output |
| OpenAI GPT-4o-mini (3,000 conv/mes) | ~$30 | ~$28.500 | Escala lineal |
| OpenAI GPT-4o-mini (10,000 conv/mes) | ~$100 | ~$95.000 | Alto volumen |
| Whapi.cloud (1 numero) | $29 | $27.550 | Tarifa plana, sin costo por mensaje |
| Meta Cloud API (respuestas 24h) | $0 | $0 | Gratis si el cliente escribe primero |

### Costo por conversacion (20 mensajes promedio)

| Componente | Costo |
|-----------|-------|
| OpenAI tokens | ~$0.01 (~$9.50 CLP) |
| WhatsApp (Whapi) | $0.00 |
| Infra (prorrateado) | ~$0.001 |
| **Total por conversacion** | **~$10 CLP** |

### Stack Google (costos si se ofrece como parte del servicio)

| Servicio Google | Costo/mes | Notas |
|----------------|----------|-------|
| Google Workspace Business Starter | USD 7/usuario (~$6.650 CLP) | Email profesional, Drive 30GB, Meet |
| Google Workspace Business Standard | USD 14/usuario (~$13.300 CLP) | Drive 2TB, grabacion Meet |
| Google Workspace Business Plus | USD 22/usuario (~$20.900 CLP) | Drive 5TB, Vault, eDiscovery |
| Google Analytics 4 | Gratis | Tracking de sitio web |
| Google My Business | Gratis | Perfil de negocio en Google |
| Google Tag Manager | Gratis | Tags de conversion |
| Google Ads (CPC Chile promedio) | $300-1.500 CLP/click | Depende del rubro |
| Google Ads presupuesto minimo | ~$300.000-500.000 CLP/mes | Para testear con resultados |

---

## 3. Modelo de pricing — Planes AgentKit Chile

> Base minima: $100.000 CLP/mes. Posicionamiento: servicio premium con IA incluida y sin costos ocultos.

---

### Plan Pyme — $99.990/mes + IVA

**Para:** Negocios locales (peluqueria, cafeteria, tienda, profesional independiente)

| Incluye | Detalle |
|---------|---------|
| Agente IA WhatsApp | 1 numero conectado |
| Mensajes IA | 1,000/mes |
| Conversaciones | Ilimitadas |
| Dashboard | 1 usuario |
| Setup wizard | Autoservicio (5 min) |
| Historial | 30 dias |
| Google My Business | Optimizacion basica |
| Soporte | Email + WhatsApp |

**Costo nuestro:** ~$37.000 CLP (Whapi $27.550 + IA ~$9.500)
**Margen:** ~63% ($62.990)

---

### Plan Profesional — $199.990/mes + IVA

**Para:** Restaurantes, hoteles, clinicas, e-commerce mediano

| Incluye | Detalle |
|---------|---------|
| Agente IA WhatsApp | 1 numero conectado |
| Mensajes IA | 5,000/mes |
| Conversaciones | Ilimitadas |
| Dashboard | 3 usuarios |
| Analytics avanzado | Metricas diarias/semanales |
| Knowledge base | Editable desde dashboard |
| Onboarding asistido | Configuracion guiada |
| Google Workspace | 1 cuenta email profesional incluida |
| Google My Business | Setup + optimizacion |
| Google Analytics | Instalacion + dashboard basico |
| Historial | 90 dias |
| Soporte | WhatsApp prioritario |

**Costo nuestro:** ~$62.000 CLP (Whapi $27.550 + IA ~$28.500 + Workspace ~$6.650)
**Margen:** ~69% ($137.990)

---

### Plan Business — $349.990/mes + IVA

**Para:** Empresas con alto volumen, multiples sucursales, cadenas

| Incluye | Detalle |
|---------|---------|
| Agentes IA WhatsApp | Hasta 3 numeros |
| Mensajes IA | 15,000/mes |
| Conversaciones | Ilimitadas |
| Dashboard | 10 usuarios |
| Analytics avanzado | Exportable, reportes automaticos |
| Knowledge base | Editable + historial de cambios |
| API + Webhooks | Integraciones con CRM, ERP |
| Google Workspace | 3 cuentas email profesional |
| Google My Business | Multi-sucursal |
| Google Analytics + Tag Manager | Setup completo |
| Google Ads | Setup inicial de campanas (1 vez) |
| Historial | Ilimitado |
| Soporte | Prioritario + reuniones mensuales |

**Costo nuestro:** ~$142.000 CLP (Whapi 3x = $82.650 + IA ~$40.000 + Workspace 3x = ~$19.950)
**Margen:** ~59% ($207.990)

---

### Plan Enterprise — Desde $599.990/mes + IVA

**Para:** Franquicias, holding, empresas con requerimientos a medida

| Incluye | Detalle |
|---------|---------|
| Agentes IA | Ilimitados |
| Mensajes IA | Ilimitados |
| Usuarios | Ilimitados |
| Todo lo de Business | Si |
| White-label | Tu marca, tu dominio |
| SLA garantizado | 99.9% uptime |
| Modelo IA personalizado | Fine-tuning o modelo dedicado |
| Google Workspace | Cuentas ilimitadas |
| Google Ads | Gestion mensual incluida |
| Onboarding dedicado | Sesiones 1:1 |
| Soporte | Dedicado + Slack/Teams |
| Account manager | Contacto directo |

**Precio:** Cotizacion segun volumen y requerimientos.

---

## 4. Add-ons

| Add-on | Precio CLP/mes |
|--------|---------------|
| Pack 1,000 mensajes IA extra | $14.990 |
| Numero WhatsApp adicional | $29.990 |
| Google Workspace usuario extra | $9.990 |
| Integracion custom (CRM, ERP) | Desde $99.990 |
| Configuracion asistida (1 vez) | $149.990 |
| White-label (tu marca) | $149.990/mes |
| Google Ads gestion mensual | Desde $149.990 + presupuesto ads |

---

## 5. Comparacion con competencia en Chile

| Feature | AgentKit Pyme ($99.990) | Botmaker Standard ($141.550) | Wati Growth ($60.770 + add-ons) | Agencia digital (~$350.000) |
|---------|------------------------|-----------------------------|---------------------------------|---------------------------|
| IA incluida | 1,000 msgs | No incluida | EUR 60 extra | Depende |
| Setup | 5 min autoservicio | Manual + USD 99 | Manual | 1-2 semanas |
| WhatsApp incluido | Si (Whapi) | No (Meta fees) | No (20% markup) | Si pero caro |
| Google incluido | My Business | No | No | A veces |
| Costos ocultos | Ninguno | $0.07/conv extra | Markup + add-ons | Horas extra |
| Costo real mensual | $99.990 | ~$200.000+ | ~$130.000+ | ~$350.000+ |
| Contrato | Mensual, cancela cuando quieras | Mensual | Mensual | 3-6 meses minimo |

---

## 6. Proyeccion de ingresos (CLP)

| Escenario | Clientes | MRR | Costo mensual | Ganancia |
|-----------|---------|-----|---------------|----------|
| Arranque (mes 3) | 10 | $1.499.900 | ~$420.000 | $1.079.900 |
| Crecimiento (mes 6) | 30 | $4.999.700 | ~$1.110.000 | $3.889.700 |
| Traccion (mes 12) | 80 | $14.399.200 | ~$2.960.000 | $11.439.200 |
| Escala (mes 18) | 150 | $27.998.500 | ~$5.250.000 | $22.748.500 |

> Supuesto: mix 50% Pyme, 30% Profesional, 15% Business, 5% Enterprise

---

## 7. Estrategia comercial Chile

### Posicionamiento
"Tu agente de WhatsApp con IA, listo en 5 minutos. Sin contratos, sin costos ocultos."

### Canales de venta
1. **Google Ads** — Palabras clave: "chatbot whatsapp chile", "agente ia whatsapp", "automatizar whatsapp empresa"
   - CPC estimado: $300-800 CLP
   - Presupuesto inicial: $300.000/mes
   - Conversion esperada: 3-5% → 15-25 leads/mes
2. **Instagram/LinkedIn Ads** — Casos de estudio, demos en video
3. **Partnerships** — Agencias de marketing digital que quieran revender
4. **Referidos** — 1 mes gratis por cada cliente referido

### Diferenciadores clave vs competencia chilena
1. **Precio transparente** — sin setup, sin markup, sin add-ons escondidos
2. **IA lista desde el dia 1** — no es un chatbot de reglas, es IA real
3. **Setup en 5 minutos** — vs 1-2 semanas con agencia
4. **Google incluido** — Workspace + My Business + Analytics en planes Pro+
5. **Sin contrato** — mensual, cancela cuando quieras
6. **Soporte en espanol** — WhatsApp directo, no tickets en ingles

### Precio ancla
Siempre mostrar el plan Profesional ($199.990) como recomendado. El plan Pyme ($99.990) se ve como "ganga" al comparar. El Business ($349.990) se ve como "premium accesible" vs agencias ($350.000-800.000+).

---

## 8. Facturacion Chile

| Concepto | Detalle |
|---------|---------|
| Facturacion | Boleta o factura electronica (SII) |
| IVA | 19% sobre el precio del plan |
| Medios de pago | Transferencia, tarjeta credito/debito, Webpay |
| Ciclo | Mensual, cobro automatico |
| Descuento anual | 20% (ej: Pyme $99.990 → $79.990/mes pagando anual) |
| Trial | 7 dias gratis en cualquier plan (sin tarjeta) |
