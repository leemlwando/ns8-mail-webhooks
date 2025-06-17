/*
 * Webhook Service for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { DB } from "@std/sqlite"
import { v4 as uuid } from "uuid"

export interface Webhook {
  id: string
  name: string
  description?: string
  url: string
  events: string[]
  active: boolean
  secret?: string
  headers?: Record<string, string>
  timeout_seconds: number
  retry_count: number
  mailbox_filter?: string
  domain_filter?: string
  created_at: string
  updated_at: string
}

export interface WebhookDelivery {
  id: string
  webhook_id: string
  event_type: string
  payload: string
  status: 'pending' | 'success' | 'failed' | 'retrying'
  response_code?: number
  response_body?: string
  response_time?: number
  error_message?: string
  attempt_count: number
  created_at: string
  updated_at: string
}

export interface WebhookFilters {
  search?: string
  active?: boolean
}

export interface DeliveryFilters {
  status?: string
}

export class WebhookService {
  private db: DB

  constructor() {
    // Initialize database
    const dataDir = Deno.env.get('DATA_DIR') || './data'
    
    try {
      Deno.mkdirSync(dataDir, { recursive: true })
    } catch (error) {
      if (!(error instanceof Deno.errors.AlreadyExists)) {
        throw error
      }
    }

    this.db = new DB(`${dataDir}/webhooks.db`)
    this.initializeDatabase()
  }

  private initializeDatabase() {
    // Create webhooks table
    this.db.execute(`
      CREATE TABLE IF NOT EXISTS webhooks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        url TEXT NOT NULL,
        events TEXT NOT NULL, -- JSON array
        active INTEGER DEFAULT 1,
        secret TEXT,
        headers TEXT, -- JSON object
        timeout_seconds INTEGER DEFAULT 30,
        retry_count INTEGER DEFAULT 3,
        mailbox_filter TEXT,
        domain_filter TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `)

    // Create webhook_deliveries table
    this.db.execute(`
      CREATE TABLE IF NOT EXISTS webhook_deliveries (
        id TEXT PRIMARY KEY,
        webhook_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        response_code INTEGER,
        response_body TEXT,
        response_time INTEGER,
        error_message TEXT,
        attempt_count INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (webhook_id) REFERENCES webhooks (id) ON DELETE CASCADE
      )
    `)

    // Create indexes
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks (active)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks (events)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_webhook_id ON webhook_deliveries (webhook_id)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_status ON webhook_deliveries (status)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_deliveries_created_at ON webhook_deliveries (created_at)')
  }

  async list(page: number = 1, limit: number = 20, filters: WebhookFilters = {}): Promise<{ webhooks: Webhook[], total: number }> {
    let query = 'SELECT * FROM webhooks WHERE 1=1'
    const params: (string | number)[] = []

    if (filters.search) {
      query += ' AND (name LIKE ? OR description LIKE ? OR url LIKE ?)'
      const searchParam = `%${filters.search}%`
      params.push(searchParam, searchParam, searchParam)
    }

    if (filters.active !== undefined) {
      query += ' AND active = ?'
      params.push(filters.active ? 1 : 0)
    }

    // Get total count
    const countQuery = query.replace('SELECT *', 'SELECT COUNT(*)')
    const totalResult = this.db.query(countQuery, params)
    const total = totalResult[0][0] as number

    // Get paginated results
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.push(limit, (page - 1) * limit)

    const rows = this.db.query(query, params)
    const webhooks = rows.map(row => this.mapRowToWebhook(row))

    return { webhooks, total }
  }

  async getById(id: string): Promise<Webhook | null> {
    const rows = this.db.query('SELECT * FROM webhooks WHERE id = ?', [id])
    
    if (rows.length === 0) {
      return null
    }

    return this.mapRowToWebhook(rows[0])
  }

  async create(data: Omit<Webhook, 'id' | 'created_at' | 'updated_at'>): Promise<Webhook> {
    const id = uuid()
    const now = new Date().toISOString()

    this.db.query(`
      INSERT INTO webhooks (
        id, name, description, url, events, active, secret, headers,
        timeout_seconds, retry_count, mailbox_filter, domain_filter,
        created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      id,
      data.name,
      data.description || null,
      data.url,
      JSON.stringify(data.events),
      data.active ? 1 : 0,
      data.secret || null,
      data.headers ? JSON.stringify(data.headers) : null,
      data.timeout_seconds,
      data.retry_count,
      data.mailbox_filter || null,
      data.domain_filter || null,
      now,
      now
    ])

    return await this.getById(id) as Webhook
  }

  async update(id: string, data: Partial<Omit<Webhook, 'id' | 'created_at' | 'updated_at'>>): Promise<Webhook | null> {
    const existing = await this.getById(id)
    if (!existing) {
      return null
    }

    const updates: string[] = []
    const params: (string | number | null)[] = []

    if (data.name !== undefined) {
      updates.push('name = ?')
      params.push(data.name)
    }

    if (data.description !== undefined) {
      updates.push('description = ?')
      params.push(data.description || null)
    }

    if (data.url !== undefined) {
      updates.push('url = ?')
      params.push(data.url)
    }

    if (data.events !== undefined) {
      updates.push('events = ?')
      params.push(JSON.stringify(data.events))
    }

    if (data.active !== undefined) {
      updates.push('active = ?')
      params.push(data.active ? 1 : 0)
    }

    if (data.secret !== undefined) {
      updates.push('secret = ?')
      params.push(data.secret || null)
    }

    if (data.headers !== undefined) {
      updates.push('headers = ?')
      params.push(data.headers ? JSON.stringify(data.headers) : null)
    }

    if (data.timeout_seconds !== undefined) {
      updates.push('timeout_seconds = ?')
      params.push(data.timeout_seconds)
    }

    if (data.retry_count !== undefined) {
      updates.push('retry_count = ?')
      params.push(data.retry_count)
    }

    if (data.mailbox_filter !== undefined) {
      updates.push('mailbox_filter = ?')
      params.push(data.mailbox_filter || null)
    }

    if (data.domain_filter !== undefined) {
      updates.push('domain_filter = ?')
      params.push(data.domain_filter || null)
    }

    if (updates.length === 0) {
      return existing
    }

    updates.push('updated_at = ?')
    params.push(new Date().toISOString())
    params.push(id)

    const query = `UPDATE webhooks SET ${updates.join(', ')} WHERE id = ?`
    this.db.query(query, params)

    return await this.getById(id)
  }

  async delete(id: string): Promise<boolean> {
    const result = this.db.query('DELETE FROM webhooks WHERE id = ?', [id])
    return result.changes > 0
  }

  async toggle(id: string): Promise<Webhook | null> {
    const existing = await this.getById(id)
    if (!existing) {
      return null
    }

    return await this.update(id, { active: !existing.active })
  }

  async getByEvents(events: string[]): Promise<Webhook[]> {
    if (events.length === 0) {
      return []
    }

    // SQLite doesn't have a JSON_CONTAINS function, so we'll use LIKE with each event
    const conditions = events.map(() => 'events LIKE ?').join(' OR ')
    const params = events.map(event => `%"${event}"%`)

    const query = `SELECT * FROM webhooks WHERE active = 1 AND (${conditions})`
    const rows = this.db.query(query, params)

    return rows.map(row => this.mapRowToWebhook(row))
      .filter(webhook => {
        // Double-check that the webhook actually has one of the requested events
        return webhook.events.some(event => events.includes(event))
      })
  }

  async getDeliveries(webhookId: string, page: number = 1, limit: number = 20, filters: DeliveryFilters = {}): Promise<{ deliveries: WebhookDelivery[], total: number }> {
    let query = 'SELECT * FROM webhook_deliveries WHERE webhook_id = ?'
    const params: (string | number)[] = [webhookId]

    if (filters.status) {
      query += ' AND status = ?'
      params.push(filters.status)
    }

    // Get total count
    const countQuery = query.replace('SELECT *', 'SELECT COUNT(*)')
    const totalResult = this.db.query(countQuery, params)
    const total = totalResult[0][0] as number

    // Get paginated results
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.push(limit, (page - 1) * limit)

    const rows = this.db.query(query, params)
    const deliveries = rows.map(row => this.mapRowToDelivery(row))

    return { deliveries, total }
  }

  async createDelivery(delivery: Omit<WebhookDelivery, 'id' | 'created_at' | 'updated_at'>): Promise<WebhookDelivery> {
    const id = uuid()
    const now = new Date().toISOString()

    this.db.query(`
      INSERT INTO webhook_deliveries (
        id, webhook_id, event_type, payload, status, response_code,
        response_body, response_time, error_message, attempt_count,
        created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      id,
      delivery.webhook_id,
      delivery.event_type,
      delivery.payload,
      delivery.status,
      delivery.response_code || null,
      delivery.response_body || null,
      delivery.response_time || null,
      delivery.error_message || null,
      delivery.attempt_count,
      now,
      now
    ])

    const rows = this.db.query('SELECT * FROM webhook_deliveries WHERE id = ?', [id])
    return this.mapRowToDelivery(rows[0])
  }

  async updateDelivery(id: string, data: Partial<Pick<WebhookDelivery, 'status' | 'response_code' | 'response_body' | 'response_time' | 'error_message' | 'attempt_count'>>): Promise<WebhookDelivery | null> {
    const updates: string[] = []
    const params: (string | number | null)[] = []

    if (data.status !== undefined) {
      updates.push('status = ?')
      params.push(data.status)
    }

    if (data.response_code !== undefined) {
      updates.push('response_code = ?')
      params.push(data.response_code)
    }

    if (data.response_body !== undefined) {
      updates.push('response_body = ?')
      params.push(data.response_body)
    }

    if (data.response_time !== undefined) {
      updates.push('response_time = ?')
      params.push(data.response_time)
    }

    if (data.error_message !== undefined) {
      updates.push('error_message = ?')
      params.push(data.error_message)
    }

    if (data.attempt_count !== undefined) {
      updates.push('attempt_count = ?')
      params.push(data.attempt_count)
    }

    if (updates.length === 0) {
      const rows = this.db.query('SELECT * FROM webhook_deliveries WHERE id = ?', [id])
      return rows.length > 0 ? this.mapRowToDelivery(rows[0]) : null
    }

    updates.push('updated_at = ?')
    params.push(new Date().toISOString())
    params.push(id)

    const query = `UPDATE webhook_deliveries SET ${updates.join(', ')} WHERE id = ?`
    this.db.query(query, params)

    const rows = this.db.query('SELECT * FROM webhook_deliveries WHERE id = ?', [id])
    return rows.length > 0 ? this.mapRowToDelivery(rows[0]) : null
  }

  private mapRowToWebhook(row: any[]): Webhook {
    return {
      id: row[0] as string,
      name: row[1] as string,
      description: row[2] as string,
      url: row[3] as string,
      events: JSON.parse(row[4] as string),
      active: Boolean(row[5]),
      secret: row[6] as string,
      headers: row[7] ? JSON.parse(row[7] as string) : undefined,
      timeout_seconds: row[8] as number,
      retry_count: row[9] as number,
      mailbox_filter: row[10] as string,
      domain_filter: row[11] as string,
      created_at: row[12] as string,
      updated_at: row[13] as string
    }
  }

  private mapRowToDelivery(row: any[]): WebhookDelivery {
    return {
      id: row[0] as string,
      webhook_id: row[1] as string,
      event_type: row[2] as string,
      payload: row[3] as string,
      status: row[4] as 'pending' | 'success' | 'failed' | 'retrying',
      response_code: row[5] as number,
      response_body: row[6] as string,
      response_time: row[7] as number,
      error_message: row[8] as string,
      attempt_count: row[9] as number,
      created_at: row[10] as string,
      updated_at: row[11] as string
    }
  }

  // Get statistics
  async getStats(): Promise<{
    total_webhooks: number
    active_webhooks: number
    total_deliveries: number
    successful_deliveries: number
    failed_deliveries: number
    pending_deliveries: number
  }> {
    const stats = {
      total_webhooks: 0,
      active_webhooks: 0,
      total_deliveries: 0,
      successful_deliveries: 0,
      failed_deliveries: 0,
      pending_deliveries: 0
    }

    // Webhook stats
    const webhookStats = this.db.query(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active
      FROM webhooks
    `)

    if (webhookStats.length > 0) {
      stats.total_webhooks = webhookStats[0][0] as number
      stats.active_webhooks = webhookStats[0][1] as number
    }

    // Delivery stats
    const deliveryStats = this.db.query(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
        SUM(CASE WHEN status = 'pending' OR status = 'retrying' THEN 1 ELSE 0 END) as pending
      FROM webhook_deliveries
    `)

    if (deliveryStats.length > 0) {
      stats.total_deliveries = deliveryStats[0][0] as number
      stats.successful_deliveries = deliveryStats[0][1] as number
      stats.failed_deliveries = deliveryStats[0][2] as number
      stats.pending_deliveries = deliveryStats[0][3] as number
    }

    return stats
  }

  close() {
    this.db.close()
  }
}
