/*
 * Delivery Service for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import type { Webhook, WebhookDelivery } from './webhook.ts'

export interface DeliveryResult {
  id: string
  status: 'success' | 'failed'
  response_code?: number
  response_body?: string
  response_time: number
  error_message?: string
  attempt_count: number
}

export class DeliveryService {
  private webhookService: any // Will be injected

  constructor() {
    // Constructor will be updated to accept webhook service
  }

  setWebhookService(webhookService: any) {
    this.webhookService = webhookService
  }  async deliver(webhook: Webhook, payload: any): Promise<DeliveryResult> {
    const startTime = Date.now()
    let delivery: WebhookDelivery | undefined

    try {
      // Create delivery record
      delivery = await this.webhookService.createDelivery({
        webhook_id: webhook.id,
        event_type: payload.event || 'unknown',
        payload: JSON.stringify(payload),
        status: 'pending',
        attempt_count: 1
      })

      if (!delivery) {
        throw new Error('Failed to create delivery record')
      }

      // Prepare request
      const body = JSON.stringify(payload)
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'User-Agent': 'NS8-Mail-Webhooks/1.0.0',
        'X-Webhook-Event': payload.event || 'unknown',
        'X-Webhook-Delivery-ID': delivery.id,
        'X-Webhook-Timestamp': new Date().toISOString()
      }

      // Add custom headers
      if (webhook.headers) {
        Object.assign(headers, webhook.headers)
      }

      // Add signature if secret is provided
      if (webhook.secret) {
        const signature = await this.generateSignature(body, webhook.secret)
        headers['X-Webhook-Signature-256'] = `sha256=${signature}`
      }

      // Make HTTP request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), webhook.timeout_seconds * 1000)

      const response = await fetch(webhook.url, {
        method: 'POST',
        headers,
        body,
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      const responseTime = Date.now() - startTime
      const responseBody = await response.text()

      // Update delivery record
      const status = response.ok ? 'success' : 'failed'
      await this.webhookService.updateDelivery(delivery.id, {
        status,
        response_code: response.status,
        response_body: responseBody.substring(0, 1000), // Limit response body size
        response_time: responseTime,
        error_message: response.ok ? undefined : `HTTP ${response.status}: ${response.statusText}`
      })

      return {
        id: delivery.id,
        status,
        response_code: response.status,
        response_body: responseBody,
        response_time: responseTime,
        error_message: response.ok ? undefined : `HTTP ${response.status}: ${response.statusText}`,
        attempt_count: 1
      }

    } catch (error) {
      const responseTime = Date.now() - startTime
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'

      // Update delivery record with error
      if (delivery) {
        await this.webhookService.updateDelivery(delivery.id, {
          status: 'failed',
          response_time: responseTime,
          error_message: errorMessage
        })
      }

      return {
        id: delivery?.id || 'unknown',
        status: 'failed',
        response_time: responseTime,
        error_message: errorMessage,
        attempt_count: 1
      }
    }
  }

  async retry(deliveryId: string): Promise<DeliveryResult | null> {
    // Get delivery record
    const rows = this.webhookService.db.query('SELECT * FROM webhook_deliveries WHERE id = ?', [deliveryId])
    
    if (rows.length === 0) {
      return null
    }

    const delivery = this.webhookService.mapRowToDelivery(rows[0])
    
    // Check if delivery can be retried
    if (delivery.status === 'success') {
      return null
    }

    // Get webhook
    const webhook = await this.webhookService.getById(delivery.webhook_id)
    if (!webhook) {
      return null
    }

    // Check retry limit
    if (delivery.attempt_count >= webhook.retry_count) {
      return null
    }

    // Update attempt count
    await this.webhookService.updateDelivery(deliveryId, {
      status: 'retrying',
      attempt_count: delivery.attempt_count + 1
    })

    // Parse original payload
    const payload = JSON.parse(delivery.payload)

    // Retry delivery
    const result = await this.deliver(webhook, payload)

    // Update the attempt count in the result
    result.attempt_count = delivery.attempt_count + 1

    return result
  }

  async deliverBatch(webhooks: Webhook[], payload: any): Promise<DeliveryResult[]> {
    const promises = webhooks.map(webhook => 
      this.deliver(webhook, payload).catch(error => ({
        id: 'error',
        status: 'failed' as const,
        response_time: 0,
        error_message: error.message,
        attempt_count: 1
      }))
    )

    return await Promise.all(promises)
  }
  private async generateSignature(payload: string, secret: string): Promise<string> {
    const encoder = new TextEncoder()
    const keyData = encoder.encode(secret)
    const messageData = encoder.encode(payload)

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )

    const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageData)
    
    // Convert ArrayBuffer to hex string
    return Array.from(new Uint8Array(signature))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  }

  // Get delivery statistics
  async getDeliveryStats(timeframe: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<{
    total_deliveries: number
    successful_deliveries: number
    failed_deliveries: number
    pending_deliveries: number
    avg_response_time: number
    success_rate: number
  }> {
    const intervals = {
      '1h': 1,
      '24h': 24,
      '7d': 24 * 7,
      '30d': 24 * 30
    }

    const hours = intervals[timeframe]
    const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()

    const stats = this.webhookService.db.query(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
        SUM(CASE WHEN status = 'pending' OR status = 'retrying' THEN 1 ELSE 0 END) as pending,
        AVG(CASE WHEN response_time IS NOT NULL THEN response_time ELSE 0 END) as avg_response_time
      FROM webhook_deliveries
      WHERE created_at >= ?
    `, [cutoffTime])

    if (stats.length === 0) {
      return {
        total_deliveries: 0,
        successful_deliveries: 0,
        failed_deliveries: 0,
        pending_deliveries: 0,
        avg_response_time: 0,
        success_rate: 0
      }
    }

    const row = stats[0]
    const total = row[0] as number
    const successful = row[1] as number
    const failed = row[2] as number
    const pending = row[3] as number
    const avgResponseTime = row[4] as number

    return {
      total_deliveries: total,
      successful_deliveries: successful,
      failed_deliveries: failed,
      pending_deliveries: pending,
      avg_response_time: Math.round(avgResponseTime || 0),
      success_rate: total > 0 ? Math.round((successful / total) * 100) : 0
    }
  }

  // Get recent delivery activity
  async getRecentActivity(limit: number = 10): Promise<{
    delivery_id: string
    webhook_name: string
    event_type: string
    status: string
    response_time?: number
    created_at: string
  }[]> {
    const rows = this.webhookService.db.query(`
      SELECT 
        wd.id,
        w.name,
        wd.event_type,
        wd.status,
        wd.response_time,
        wd.created_at
      FROM webhook_deliveries wd
      JOIN webhooks w ON wd.webhook_id = w.id
      ORDER BY wd.created_at DESC
      LIMIT ?
    `, [limit])

    return rows.map(row => ({
      delivery_id: row[0] as string,
      webhook_name: row[1] as string,
      event_type: row[2] as string,
      status: row[3] as string,
      response_time: row[4] as number,
      created_at: row[5] as string
    }))
  }

  // Cleanup old delivery records
  async cleanup(olderThanDays: number = 30): Promise<number> {
    const cutoffTime = new Date(Date.now() - olderThanDays * 24 * 60 * 60 * 1000).toISOString()
    
    const result = this.webhookService.db.query(
      'DELETE FROM webhook_deliveries WHERE created_at < ? AND status IN (?, ?)',
      [cutoffTime, 'success', 'failed']
    )

    return result.changes
  }
}
