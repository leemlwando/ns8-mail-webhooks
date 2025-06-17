/*
 * Scheduled Webhook Routes for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { Hono } from '@hono/hono'
import { z } from 'zod'
import type { ScheduledWebhookService } from '../services/scheduled-webhook.ts'

const scheduledWebhooks = new Hono()

// Validation schemas
const scheduledWebhookSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  url: z.string().url(),
  schedule: z.string(), // Cron expression
  active: z.boolean().default(true),
  payload: z.record(z.any()),
  secret: z.string().optional(),
  headers: z.record(z.string()).optional(),
  timeout_seconds: z.number().min(1).max(300).default(30),
  retry_count: z.number().min(0).max(10).default(3),
  timezone: z.string().default('UTC')
})

const updateScheduledWebhookSchema = scheduledWebhookSchema.partial()

// List all scheduled webhooks
scheduledWebhooks.get('/', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const page = parseInt(c.req.query('page') || '1')
    const limit = parseInt(c.req.query('limit') || '20')
    const search = c.req.query('search')
    const active = c.req.query('active')

    const filters = {
      search,
      active: active ? active === 'true' : undefined
    }

    const result = await scheduledWebhookService.list(page, limit, filters)
    
    return c.json({
      success: true,
      data: result.scheduledWebhooks,
      pagination: {
        page,
        limit,
        total: result.total,
        pages: Math.ceil(result.total / limit)
      }
    })
  } catch (error) {
    console.error('Error listing scheduled webhooks:', error)
    return c.json({ success: false, error: 'Failed to list scheduled webhooks' }, 500)
  }
})

// Get scheduled webhook by ID
scheduledWebhooks.get('/:id', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    
    const scheduledWebhook = await scheduledWebhookService.getById(id)
    
    if (!scheduledWebhook) {
      return c.json({ success: false, error: 'Scheduled webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: scheduledWebhook })
  } catch (error) {
    console.error('Error getting scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to get scheduled webhook' }, 500)
  }
})

// Create new scheduled webhook
scheduledWebhooks.post('/', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const body = await c.req.json()
    
    const validation = scheduledWebhookSchema.safeParse(body)
    if (!validation.success) {
      return c.json({ 
        success: false, 
        error: 'Validation failed',
        details: validation.error.errors
      }, 400)
    }
    
    const scheduledWebhook = await scheduledWebhookService.create(validation.data)
    
    return c.json({ success: true, data: scheduledWebhook }, 201)
  } catch (error) {
    console.error('Error creating scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to create scheduled webhook' }, 500)
  }
})

// Update scheduled webhook
scheduledWebhooks.put('/:id', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    const body = await c.req.json()
    
    const validation = updateScheduledWebhookSchema.safeParse(body)
    if (!validation.success) {
      return c.json({ 
        success: false, 
        error: 'Validation failed',
        details: validation.error.errors
      }, 400)
    }
    
    const scheduledWebhook = await scheduledWebhookService.update(id, validation.data)
    
    if (!scheduledWebhook) {
      return c.json({ success: false, error: 'Scheduled webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: scheduledWebhook })
  } catch (error) {
    console.error('Error updating scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to update scheduled webhook' }, 500)
  }
})

// Delete scheduled webhook
scheduledWebhooks.delete('/:id', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    
    const success = await scheduledWebhookService.delete(id)
    
    if (!success) {
      return c.json({ success: false, error: 'Scheduled webhook not found' }, 404)
    }
    
    return c.json({ success: true, message: 'Scheduled webhook deleted successfully' })
  } catch (error) {
    console.error('Error deleting scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to delete scheduled webhook' }, 500)
  }
})

// Toggle scheduled webhook active status
scheduledWebhooks.patch('/:id/toggle', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    
    const scheduledWebhook = await scheduledWebhookService.toggle(id)
    
    if (!scheduledWebhook) {
      return c.json({ success: false, error: 'Scheduled webhook not found' }, 404)
    }
    
    return c.json({ success: true, data: scheduledWebhook })
  } catch (error) {
    console.error('Error toggling scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to toggle scheduled webhook' }, 500)
  }
})

// Trigger scheduled webhook manually
scheduledWebhooks.post('/:id/trigger', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const deliveryService = c.get('deliveryService')
    const id = c.req.param('id')
    
    const scheduledWebhook = await scheduledWebhookService.getById(id)
    
    if (!scheduledWebhook) {
      return c.json({ success: false, error: 'Scheduled webhook not found' }, 404)
    }
    
    // Trigger the webhook manually
    const result = await scheduledWebhookService.trigger(id)
    
    return c.json({ 
      success: true, 
      data: {
        execution_id: result.id,
        status: result.status,
        message: 'Scheduled webhook triggered manually'
      }
    })
  } catch (error) {
    console.error('Error triggering scheduled webhook:', error)
    return c.json({ success: false, error: 'Failed to trigger scheduled webhook' }, 500)
  }
})

// Get scheduled webhook execution history
scheduledWebhooks.get('/:id/executions', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    const page = parseInt(c.req.query('page') || '1')
    const limit = parseInt(c.req.query('limit') || '20')
    const status = c.req.query('status')
    
    const filters = { status }
    const result = await scheduledWebhookService.getExecutions(id, page, limit, filters)
    
    return c.json({
      success: true,
      data: result.executions,
      pagination: {
        page,
        limit,
        total: result.total,
        pages: Math.ceil(result.total / limit)
      }
    })
  } catch (error) {
    console.error('Error getting scheduled webhook executions:', error)
    return c.json({ success: false, error: 'Failed to get scheduled webhook executions' }, 500)
  }
})

// Get next execution times for scheduled webhooks
scheduledWebhooks.get('/:id/next-runs', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const id = c.req.param('id')
    const count = parseInt(c.req.query('count') || '5')
    
    const nextRuns = await scheduledWebhookService.getNextRuns(id, count)
    
    return c.json({ success: true, data: nextRuns })
  } catch (error) {
    console.error('Error getting next runs:', error)
    return c.json({ success: false, error: 'Failed to get next runs' }, 500)
  }
})

// Validate cron expression
scheduledWebhooks.post('/validate-cron', (c) => {
  try {
    const body = c.req.json() as { schedule: string }
    
    // Basic cron validation - in a real implementation, you'd use a proper cron library
    const cronPattern = /^(\*|([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])|\*\/([0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])) (\*|([0-9]|1[0-9]|2[0-3])|\*\/([0-9]|1[0-9]|2[0-3])) (\*|([1-9]|1[0-9]|2[0-9]|3[0-1])|\*\/([1-9]|1[0-9]|2[0-9]|3[0-1])) (\*|([1-9]|1[0-2])|\*\/([1-9]|1[0-2])) (\*|([0-6])|\*\/([0-6]))$/
    
    const isValid = cronPattern.test(body.schedule)
    
    return c.json({
      success: true,
      data: {
        valid: isValid,
        schedule: body.schedule,
        message: isValid ? 'Valid cron expression' : 'Invalid cron expression'
      }
    })
  } catch (error) {
    console.error('Error validating cron:', error)
    return c.json({ success: false, error: 'Failed to validate cron expression' }, 500)
  }
})

export { scheduledWebhooks as scheduledWebhookRoutes }
