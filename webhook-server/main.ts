/*
 * Main Entry Point for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { Hono } from '@hono/hono'
import { logger } from '@hono/hono/middleware'
import { cors } from '@hono/hono/middleware'
import { webhookRoutes } from './routes/webhooks.ts'
import { scheduledWebhookRoutes } from './routes/scheduled-webhooks.ts'
import { healthRoutes } from './routes/health.ts'
import { statisticsRoutes } from './routes/statistics.ts'
import { WebhookService } from './services/webhook.ts'
import { ScheduledWebhookService } from './services/scheduled-webhook.ts'
import { DeliveryService } from './services/delivery.ts'
import { BatchProcessor } from './services/batch-processor.ts'

const app = new Hono()

// Middleware
app.use('*', logger())
app.use('*', cors({
  origin: ['http://localhost:8080', ...(Deno.env.get('ALLOWED_ORIGINS')?.split(',') || [])],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
}))

// Global error handler
app.onError((err, c) => {
  console.error('Global error:', err)
  return c.json({ error: 'Internal server error' }, 500)
})

// Initialize services
const webhookService = new WebhookService()
const scheduledWebhookService = new ScheduledWebhookService()
const deliveryService = new DeliveryService()
const batchProcessor = new BatchProcessor()

// Setup service dependencies
deliveryService.setWebhookService(webhookService)

// Make services available to routes
app.use('*', async (c, next) => {
  c.set('webhookService', webhookService)
  c.set('scheduledWebhookService', scheduledWebhookService)
  c.set('deliveryService', deliveryService)
  c.set('batchProcessor', batchProcessor)
  await next()
})

// API Routes
app.route('/api/webhooks', webhookRoutes)
app.route('/api/scheduled-webhooks', scheduledWebhookRoutes)
app.route('/api/statistics', statisticsRoutes)
app.route('/health', healthRoutes)

// Root endpoint
app.get('/', (c) => {
  return c.json({
    name: 'NS8 Mail Webhooks Server',
    version: '1.0.0',
    author: 'Lee M. Lwando <leemlwando@gmail.com>',
    status: 'running',
    timestamp: new Date().toISOString()
  })
})

// Start server
const port = parseInt(Deno.env.get('API_PORT') || '3000')
const hostname = Deno.env.get('API_HOST') || '0.0.0.0'

console.log(`🚀 NS8 Mail Webhooks Server starting...`)
console.log(`📧 Author: Lee M. Lwando <leemlwando@gmail.com>`)
console.log(`🌐 Server: http://${hostname}:${port}`)
console.log(`📝 Log Level: ${Deno.env.get('LOG_LEVEL') || 'info'}`)
console.log(`💾 Data Directory: ${Deno.env.get('DATA_DIR') || './data'}`)

// Graceful shutdown handling
const abortController = new AbortController()

Deno.addSignalListener('SIGTERM', () => {
  console.log('📴 Received SIGTERM, shutting down gracefully...')
  abortController.abort()
})

Deno.addSignalListener('SIGINT', () => {
  console.log('📴 Received SIGINT, shutting down gracefully...')
  abortController.abort()
})

try {
  await Deno.serve({ 
    port, 
    hostname,
    signal: abortController.signal
  }, app.fetch)
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('✅ Server shut down gracefully')
  } else {
    console.error('❌ Server error:', error)
    Deno.exit(1)
  }
}
