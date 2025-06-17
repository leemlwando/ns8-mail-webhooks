/*
 * Scheduled Webhook Service for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { DB } from "@std/sqlite"
import { v4 as uuid } from "uuid"

export interface ScheduledWebhook {
  id: string
  name: string
  description?: string
  url: string
  schedule: string // Cron expression
  active: boolean
  payload: Record<string, any>
  secret?: string
  headers?: Record<string, string>
  timeout_seconds: number
  retry_count: number
  timezone: string
  next_run?: string
  last_run?: string
  created_at: string
  updated_at: string
}

export interface ScheduledWebhookExecution {
  id: string
  scheduled_webhook_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  started_at?: string
  completed_at?: string
  response_code?: number
  response_body?: string
  response_time?: number
  error_message?: string
  attempt_count: number
  created_at: string
  updated_at: string
}

export interface ScheduledWebhookFilters {
  search?: string
  active?: boolean
}

export interface ExecutionFilters {
  status?: string
}

export class ScheduledWebhookService {
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

    this.db = new DB(`${dataDir}/scheduled-webhooks.db`)
    this.initializeDatabase()
  }

  private initializeDatabase() {
    // Create scheduled_webhooks table
    this.db.execute(`
      CREATE TABLE IF NOT EXISTS scheduled_webhooks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        url TEXT NOT NULL,
        schedule TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        payload TEXT NOT NULL, -- JSON object
        secret TEXT,
        headers TEXT, -- JSON object
        timeout_seconds INTEGER DEFAULT 30,
        retry_count INTEGER DEFAULT 3,
        timezone TEXT DEFAULT 'UTC',
        next_run TEXT,
        last_run TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `)

    // Create scheduled_webhook_executions table
    this.db.execute(`
      CREATE TABLE IF NOT EXISTS scheduled_webhook_executions (
        id TEXT PRIMARY KEY,
        scheduled_webhook_id TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        started_at TEXT,
        completed_at TEXT,
        response_code INTEGER,
        response_body TEXT,
        response_time INTEGER,
        error_message TEXT,
        attempt_count INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (scheduled_webhook_id) REFERENCES scheduled_webhooks (id) ON DELETE CASCADE
      )
    `)

    // Create indexes
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_scheduled_webhooks_active ON scheduled_webhooks (active)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_scheduled_webhooks_next_run ON scheduled_webhooks (next_run)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_executions_webhook_id ON scheduled_webhook_executions (scheduled_webhook_id)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_executions_status ON scheduled_webhook_executions (status)')
    this.db.execute('CREATE INDEX IF NOT EXISTS idx_executions_created_at ON scheduled_webhook_executions (created_at)')
  }

  async list(page: number = 1, limit: number = 20, filters: ScheduledWebhookFilters = {}): Promise<{ scheduledWebhooks: ScheduledWebhook[], total: number }> {
    let query = 'SELECT * FROM scheduled_webhooks WHERE 1=1'
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
    const scheduledWebhooks = rows.map(row => this.mapRowToScheduledWebhook(row))

    return { scheduledWebhooks, total }
  }

  async getById(id: string): Promise<ScheduledWebhook | null> {
    const rows = this.db.query('SELECT * FROM scheduled_webhooks WHERE id = ?', [id])
    
    if (rows.length === 0) {
      return null
    }

    return this.mapRowToScheduledWebhook(rows[0])
  }

  async create(data: Omit<ScheduledWebhook, 'id' | 'next_run' | 'last_run' | 'created_at' | 'updated_at'>): Promise<ScheduledWebhook> {
    const id = uuid()
    const now = new Date().toISOString()
    const nextRun = this.calculateNextRun(data.schedule, data.timezone)

    this.db.query(`
      INSERT INTO scheduled_webhooks (
        id, name, description, url, schedule, active, payload, secret, headers,
        timeout_seconds, retry_count, timezone, next_run, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      id,
      data.name,
      data.description || null,
      data.url,
      data.schedule,
      data.active ? 1 : 0,
      JSON.stringify(data.payload),
      data.secret || null,
      data.headers ? JSON.stringify(data.headers) : null,
      data.timeout_seconds,
      data.retry_count,
      data.timezone,
      nextRun,
      now,
      now
    ])

    return await this.getById(id) as ScheduledWebhook
  }

  async update(id: string, data: Partial<Omit<ScheduledWebhook, 'id' | 'next_run' | 'last_run' | 'created_at' | 'updated_at'>>): Promise<ScheduledWebhook | null> {
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

    if (data.schedule !== undefined) {
      updates.push('schedule = ?')
      params.push(data.schedule)
      
      // Recalculate next run if schedule changed
      const timezone = data.timezone || existing.timezone
      const nextRun = this.calculateNextRun(data.schedule, timezone)
      updates.push('next_run = ?')
      params.push(nextRun)
    }

    if (data.active !== undefined) {
      updates.push('active = ?')
      params.push(data.active ? 1 : 0)
    }

    if (data.payload !== undefined) {
      updates.push('payload = ?')
      params.push(JSON.stringify(data.payload))
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

    if (data.timezone !== undefined) {
      updates.push('timezone = ?')
      params.push(data.timezone)
      
      // Recalculate next run if timezone changed
      const schedule = data.schedule || existing.schedule
      const nextRun = this.calculateNextRun(schedule, data.timezone)
      updates.push('next_run = ?')
      params.push(nextRun)
    }

    if (updates.length === 0) {
      return existing
    }

    updates.push('updated_at = ?')
    params.push(new Date().toISOString())
    params.push(id)

    const query = `UPDATE scheduled_webhooks SET ${updates.join(', ')} WHERE id = ?`
    this.db.query(query, params)

    return await this.getById(id)
  }

  async delete(id: string): Promise<boolean> {
    const result = this.db.query('DELETE FROM scheduled_webhooks WHERE id = ?', [id])
    return result.changes > 0
  }

  async toggle(id: string): Promise<ScheduledWebhook | null> {
    const existing = await this.getById(id)
    if (!existing) {
      return null
    }

    return await this.update(id, { active: !existing.active })
  }

  async trigger(id: string): Promise<ScheduledWebhookExecution> {
    const scheduledWebhook = await this.getById(id)
    if (!scheduledWebhook) {
      throw new Error('Scheduled webhook not found')
    }

    // Create execution record
    const execution = await this.createExecution({
      scheduled_webhook_id: id,
      status: 'pending',
      attempt_count: 1
    })

    // Update last run time
    this.db.query('UPDATE scheduled_webhooks SET last_run = ? WHERE id = ?', [
      new Date().toISOString(),
      id
    ])

    return execution
  }

  async getDueWebhooks(): Promise<ScheduledWebhook[]> {
    const now = new Date().toISOString()
    
    const rows = this.db.query(`
      SELECT * FROM scheduled_webhooks 
      WHERE active = 1 AND next_run IS NOT NULL AND next_run <= ?
      ORDER BY next_run ASC
    `, [now])

    return rows.map(row => this.mapRowToScheduledWebhook(row))
  }

  async updateNextRun(id: string): Promise<void> {
    const scheduledWebhook = await this.getById(id)
    if (!scheduledWebhook) {
      return
    }

    const nextRun = this.calculateNextRun(scheduledWebhook.schedule, scheduledWebhook.timezone)
    
    this.db.query('UPDATE scheduled_webhooks SET next_run = ? WHERE id = ?', [
      nextRun,
      id
    ])
  }

  async getExecutions(scheduledWebhookId: string, page: number = 1, limit: number = 20, filters: ExecutionFilters = {}): Promise<{ executions: ScheduledWebhookExecution[], total: number }> {
    let query = 'SELECT * FROM scheduled_webhook_executions WHERE scheduled_webhook_id = ?'
    const params: (string | number)[] = [scheduledWebhookId]

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
    const executions = rows.map(row => this.mapRowToExecution(row))

    return { executions, total }
  }

  async createExecution(execution: Omit<ScheduledWebhookExecution, 'id' | 'created_at' | 'updated_at'>): Promise<ScheduledWebhookExecution> {
    const id = uuid()
    const now = new Date().toISOString()

    this.db.query(`
      INSERT INTO scheduled_webhook_executions (
        id, scheduled_webhook_id, status, started_at, completed_at,
        response_code, response_body, response_time, error_message,
        attempt_count, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      id,
      execution.scheduled_webhook_id,
      execution.status,
      execution.started_at || null,
      execution.completed_at || null,
      execution.response_code || null,
      execution.response_body || null,
      execution.response_time || null,
      execution.error_message || null,
      execution.attempt_count,
      now,
      now
    ])

    const rows = this.db.query('SELECT * FROM scheduled_webhook_executions WHERE id = ?', [id])
    return this.mapRowToExecution(rows[0])
  }

  async updateExecution(id: string, data: Partial<Pick<ScheduledWebhookExecution, 'status' | 'started_at' | 'completed_at' | 'response_code' | 'response_body' | 'response_time' | 'error_message' | 'attempt_count'>>): Promise<ScheduledWebhookExecution | null> {
    const updates: string[] = []
    const params: (string | number | null)[] = []

    if (data.status !== undefined) {
      updates.push('status = ?')
      params.push(data.status)
    }

    if (data.started_at !== undefined) {
      updates.push('started_at = ?')
      params.push(data.started_at)
    }

    if (data.completed_at !== undefined) {
      updates.push('completed_at = ?')
      params.push(data.completed_at)
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
      const rows = this.db.query('SELECT * FROM scheduled_webhook_executions WHERE id = ?', [id])
      return rows.length > 0 ? this.mapRowToExecution(rows[0]) : null
    }

    updates.push('updated_at = ?')
    params.push(new Date().toISOString())
    params.push(id)

    const query = `UPDATE scheduled_webhook_executions SET ${updates.join(', ')} WHERE id = ?`
    this.db.query(query, params)

    const rows = this.db.query('SELECT * FROM scheduled_webhook_executions WHERE id = ?', [id])
    return rows.length > 0 ? this.mapRowToExecution(rows[0]) : null
  }

  async getNextRuns(id: string, count: number = 5): Promise<string[]> {
    const scheduledWebhook = await this.getById(id)
    if (!scheduledWebhook) {
      return []
    }

    const nextRuns: string[] = []
    let nextRun = this.calculateNextRun(scheduledWebhook.schedule, scheduledWebhook.timezone)
    
    for (let i = 0; i < count; i++) {
      nextRuns.push(nextRun)
      nextRun = this.calculateNextRun(scheduledWebhook.schedule, scheduledWebhook.timezone, new Date(nextRun))
    }

    return nextRuns
  }

  private calculateNextRun(schedule: string, timezone: string = 'UTC', fromDate?: Date): string {
    // This is a simplified cron calculation
    // In a real implementation, you'd use a proper cron library
    const now = fromDate || new Date()
    
    // Add 1 hour as a simple example (in real implementation, parse cron expression)
    const nextRun = new Date(now.getTime() + 60 * 60 * 1000)
    
    return nextRun.toISOString()
  }

  private mapRowToScheduledWebhook(row: any[]): ScheduledWebhook {
    return {
      id: row[0] as string,
      name: row[1] as string,
      description: row[2] as string,
      url: row[3] as string,
      schedule: row[4] as string,
      active: Boolean(row[5]),
      payload: JSON.parse(row[6] as string),
      secret: row[7] as string,
      headers: row[8] ? JSON.parse(row[8] as string) : undefined,
      timeout_seconds: row[9] as number,
      retry_count: row[10] as number,
      timezone: row[11] as string,
      next_run: row[12] as string,
      last_run: row[13] as string,
      created_at: row[14] as string,
      updated_at: row[15] as string
    }
  }

  private mapRowToExecution(row: any[]): ScheduledWebhookExecution {
    return {
      id: row[0] as string,
      scheduled_webhook_id: row[1] as string,
      status: row[2] as 'pending' | 'running' | 'success' | 'failed',
      started_at: row[3] as string,
      completed_at: row[4] as string,
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
    total_scheduled_webhooks: number
    active_scheduled_webhooks: number
    total_executions: number
    successful_executions: number
    failed_executions: number
    pending_executions: number
  }> {
    const stats = {
      total_scheduled_webhooks: 0,
      active_scheduled_webhooks: 0,
      total_executions: 0,
      successful_executions: 0,
      failed_executions: 0,
      pending_executions: 0
    }

    // Scheduled webhook stats
    const webhookStats = this.db.query(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active
      FROM scheduled_webhooks
    `)

    if (webhookStats.length > 0) {
      stats.total_scheduled_webhooks = webhookStats[0][0] as number
      stats.active_scheduled_webhooks = webhookStats[0][1] as number
    }

    // Execution stats
    const executionStats = this.db.query(`
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
        SUM(CASE WHEN status = 'pending' OR status = 'running' THEN 1 ELSE 0 END) as pending
      FROM scheduled_webhook_executions
    `)

    if (executionStats.length > 0) {
      stats.total_executions = executionStats[0][0] as number
      stats.successful_executions = executionStats[0][1] as number
      stats.failed_executions = executionStats[0][2] as number
      stats.pending_executions = executionStats[0][3] as number
    }

    return stats
  }

  close() {
    this.db.close()
  }
}
