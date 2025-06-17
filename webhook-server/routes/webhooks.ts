/*
 * Webhook Routes for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { Hono } from '@hono/hono'
import { z } from 'zod'
import type { WebhookService } from '../services/webhook.ts'

const webhooks = new Hono()

// Validation schemas
const webhookSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  url: z.string().url(),
  events: z.array(z.enum(['email_received', 'email_sent', 'email_bounced', 'email_delivered', 'email_opened', 'email_clicked'])),
  active: z.boolean().default(true),
  secret: z.string().optional(),
  headers: z.record(z.string()).optional(),
  timeout_seconds: z.number().min(1).max(300).default(30),
  retry_count: z.number().min(0).max(10).default(3),
  mailbox_filter: z.string().optional(),
  domain_filter: z.string().optional()
})

const updateWebhookSchema = webhookSchema.partial()

// List all webhooks
webhooks.get('/', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const page = parseInt(c.req.query('page') || '1')
    const limit = parseInt(c.req.query('limit') || '20')
    const search = c.req.query('search')
    const active = c.req.query('active')

    const filters = {
      search,
      active: active ? active === 'true' : undefined
    }

    const result = await webhookService.list(page, limit, filters)
    
    return c.json({
      success: true,
      data: result.webhooks,
      pagination: {
        page,
        limit,
        total: result.total,
        pages: Math.ceil(result.total / limit)
      }
    })
  } catch (error) {
    console.error('Error listing webhooks:', error)
    return c.json({ success: false, error: 'Failed to list webhooks' }, 500)
  }
})

// Get webhook by ID
webhooks.get('/:id', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const id = c.req.param('id')
    
    const webhook = await webhookService.getById(id)
    
    if (!webhook) {
      return c.json({ success: false, error: 'Webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: webhook })
  } catch (error) {
    console.error('Error getting webhook:', error)
    return c.json({ success: false, error: 'Failed to get webhook' }, 500)
  }
})

// Create new webhook
webhooks.post('/', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const body = await c.req.json()
    
    const validation = webhookSchema.safeParse(body)
    if (!validation.success) {
      return c.json({ 
        success: false, 
        error: 'Validation failed',
        details: validation.error.errors
      }, 400)
    }
    
    const webhook = await webhookService.create(validation.data)
    
    return c.json({ success: true, data: webhook }, 201)
  } catch (error) {
    console.error('Error creating webhook:', error)
    return c.json({ success: false, error: 'Failed to create webhook' }, 500)
  }
})

// Update webhook
webhooks.put('/:id', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const id = c.req.param('id')
    const body = await c.req.json()
    
    const validation = updateWebhookSchema.safeParse(body)
    if (!validation.success) {
      return c.json({ 
        success: false, 
        error: 'Validation failed',
        details: validation.error.errors
      }, 400)
    }
    
    const webhook = await webhookService.update(id, validation.data)
    
    if (!webhook) {
      return c.json({ success: false, error: 'Webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: webhook })
  } catch (error) {
    console.error('Error updating webhook:', error)
    return c.json({ success: false, error: 'Failed to update webhook' }, 500)
  }
})

// Delete webhook
webhooks.delete('/:id', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const id = c.req.param('id')
    
    const success = await webhookService.delete(id)
    
    if (!success) {
      return c.json({ success: false, error: 'Webhook not found' }, 404)
    }
    
    return c.json({ success: true, message: 'Webhook deleted successfully' })
  } catch (error) {
    console.error('Error deleting webhook:', error)
    return c.json({ success: false, error: 'Failed to delete webhook' }, 500)
  }
})

// Toggle webhook active status
webhooks.patch('/:id/toggle', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const id = c.req.param('id')
    
    const webhook = await webhookService.toggle(id)
    
    if (!webhook) {
      return c.json({ success: false, error: 'Webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: webhook })
  } catch (error) {
    console.error('Error toggling webhook:', error)
    return c.json({ success: false, error: 'Failed to toggle webhook' }, 500)
  }
})

// Test webhook
webhooks.post('/:id/test', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const deliveryService = c.get('deliveryService')
    const id = c.req.param('id')
    
    const webhook = await webhookService.getById(id)
    
    if (!webhook) {
      return c.json({ success: false, error: 'Webhook not found' }, 404)
    }
    
    // Create test payload
    const testPayload = {
      event: 'test',
      timestamp: new Date().toISOString(),
      webhook_id: id,
      data: {
        message: 'This is a test webhook delivery',
        test_mode: true
      }
    }
    
    const result = await deliveryService.deliver(webhook, testPayload)
    
    return c.json({ 
      success: true, 
      data: {
        delivery_id: result.id,
        status: result.status,
        response_code: result.response_code,
        response_time: result.response_time
      }
    })
  } catch (error) {
    console.error('Error testing webhook:', error)
    return c.json({ success: false, error: 'Failed to test webhook' }, 500)
  }
})

// Get webhook delivery history
webhooks.get('/:id/deliveries', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const id = c.req.param('id')
    const page = parseInt(c.req.query('page') || '1')
    const limit = parseInt(c.req.query('limit') || '20')
    const status = c.req.query('status')
    
    const filters = { status }
    const result = await webhookService.getDeliveries(id, page, limit, filters)
    
    return c.json({
      success: true,
      data: result.deliveries,
      pagination: {
        page,
        limit,
        total: result.total,
        pages: Math.ceil(result.total / limit)
      }
    })
  } catch (error) {
    console.error('Error getting webhook deliveries:', error)
    return c.json({ success: false, error: 'Failed to get webhook deliveries' }, 500)
  }
})

// Retry failed webhook delivery
webhooks.post('/:id/deliveries/:deliveryId/retry', async (c) => {
  try {
    const deliveryService = c.get('deliveryService')
    const id = c.req.param('id')
    const deliveryId = c.req.param('deliveryId')
    
    const result = await deliveryService.retry(deliveryId)
    
    if (!result) {
      return c.json({ success: false, error: 'Delivery not found or cannot be retried' }, 404)
    }
    
    return c.json({ success: true, data: result })
  } catch (error) {
    console.error('Error retrying webhook delivery:', error)
    return c.json({ success: false, error: 'Failed to retry webhook delivery' }, 500)
  }
})

export { webhooks as webhookRoutes }
