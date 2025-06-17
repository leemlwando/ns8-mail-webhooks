/*
 * Statistics Routes for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { Hono } from '@hono/hono'
import type { WebhookService } from '../services/webhook.ts'
import type { ScheduledWebhookService } from '../services/scheduled-webhook.ts'
import type { DeliveryService } from '../services/delivery.ts'

const statistics = new Hono()

// Get overall statistics
statistics.get('/', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const deliveryService = c.get('deliveryService') as DeliveryService

    // Get webhook stats
    const webhookStats = await webhookService.getStats()
    
    // Get scheduled webhook stats
    const scheduledStats = await scheduledWebhookService.getStats()
    
    // Get delivery stats for different timeframes
    const deliveryStats24h = await deliveryService.getDeliveryStats('24h')
    const deliveryStats7d = await deliveryService.getDeliveryStats('7d')
    const deliveryStats30d = await deliveryService.getDeliveryStats('30d')

    return c.json({
      success: true,
      data: {
        webhooks: webhookStats,
        scheduled_webhooks: scheduledStats,
        deliveries: {
          last_24h: deliveryStats24h,
          last_7d: deliveryStats7d,
          last_30d: deliveryStats30d
        },
        summary: {
          total_webhooks: webhookStats.total_webhooks + scheduledStats.total_scheduled_webhooks,
          active_webhooks: webhookStats.active_webhooks + scheduledStats.active_scheduled_webhooks,
          total_deliveries: deliveryStats30d.total_deliveries,
          success_rate: deliveryStats30d.success_rate,
          avg_response_time: deliveryStats30d.avg_response_time
        }
      }
    })
  } catch (error) {
    console.error('Error getting statistics:', error)
    return c.json({ success: false, error: 'Failed to get statistics' }, 500)
  }
})

// Get webhook statistics
statistics.get('/webhooks', async (c) => {
  try {
    const webhookService = c.get('webhookService') as WebhookService
    const stats = await webhookService.getStats()
    
    return c.json({ success: true, data: stats })
  } catch (error) {
    console.error('Error getting webhook statistics:', error)
    return c.json({ success: false, error: 'Failed to get webhook statistics' }, 500)
  }
})

// Get scheduled webhook statistics
statistics.get('/scheduled-webhooks', async (c) => {
  try {
    const scheduledWebhookService = c.get('scheduledWebhookService') as ScheduledWebhookService
    const stats = await scheduledWebhookService.getStats()
    
    return c.json({ success: true, data: stats })
  } catch (error) {
    console.error('Error getting scheduled webhook statistics:', error)
    return c.json({ success: false, error: 'Failed to get scheduled webhook statistics' }, 500)
  }
})

// Get delivery statistics
statistics.get('/deliveries', async (c) => {
  try {
    const deliveryService = c.get('deliveryService') as DeliveryService
    const timeframe = c.req.query('timeframe') as '1h' | '24h' | '7d' | '30d' || '24h'
    
    const stats = await deliveryService.getDeliveryStats(timeframe)
    
    return c.json({ success: true, data: stats })
  } catch (error) {
    console.error('Error getting delivery statistics:', error)
    return c.json({ success: false, error: 'Failed to get delivery statistics' }, 500)
  }
})

// Get recent activity
statistics.get('/activity', async (c) => {
  try {
    const deliveryService = c.get('deliveryService') as DeliveryService
    const limit = parseInt(c.req.query('limit') || '20')
    
    const activity = await deliveryService.getRecentActivity(limit)
    
    return c.json({ success: true, data: activity })
  } catch (error) {
    console.error('Error getting recent activity:', error)
    return c.json({ success: false, error: 'Failed to get recent activity' }, 500)
  }
})

// Get system health metrics
statistics.get('/health', async (c) => {
  try {
    const startTime = Date.now()
    
    // Basic health metrics
    const healthMetrics = {
      timestamp: new Date().toISOString(),
      uptime: process.uptime ? process.uptime() : 0,
      memory: {
        used: 0,
        total: 0,
        free: 0
      },
      response_time: 0,
      status: 'healthy'
    }

    // Calculate response time
    healthMetrics.response_time = Date.now() - startTime

    return c.json({ success: true, data: healthMetrics })
  } catch (error) {
    console.error('Error getting health metrics:', error)
    return c.json({ success: false, error: 'Failed to get health metrics' }, 500)
  }
})

export { statistics as statisticsRoutes }
