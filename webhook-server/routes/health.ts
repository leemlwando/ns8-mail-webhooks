/*
 * Health Check Routes for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

import { Hono } from 'https://deno.land/x/hono@v3.12.0/mod.ts'

const health = new Hono()

// Store server start time
const serverStartTime = Date.now()

// Basic health check
health.get('/', (c) => {
  const uptime = Date.now() - serverStartTime
  
  return c.json({
    status: 'healthy',
    service: 'ns8-mail-webhooks-server',
    version: '1.0.0',
    author: 'Lee M. Lwando <leemlwando@gmail.com>',
    timestamp: new Date().toISOString(),
    uptime_ms: uptime,
    uptime_human: formatUptime(uptime),
    response_time: 0, // Will be calculated by calling service
    memory_usage: getMemoryUsage(),
    environment: {
      api_port: Deno.env.get('API_PORT') || '3000',
      log_level: Deno.env.get('LOG_LEVEL') || 'info',
      data_dir: Deno.env.get('DATA_DIR') || './data'
    }
  })
})

// Detailed health check with dependencies
health.get('/detailed', async (c) => {
  const startTime = Date.now()
  
  // Check database connection
  const dbHealth = await checkDatabaseHealth()
  
  // Check file system
  const fsHealth = checkFileSystemHealth()
  
  const responseTime = Date.now() - startTime
  const uptime = Date.now() - serverStartTime
  
  const overallStatus = dbHealth.status === 'healthy' && fsHealth.status === 'healthy' 
    ? 'healthy' 
    : 'degraded'
  
  return c.json({
    status: overallStatus,
    service: 'ns8-mail-webhooks-server',
    version: '1.0.0',
    author: 'Lee M. Lwando <leemlwando@gmail.com>',
    timestamp: new Date().toISOString(),
    uptime_ms: uptime,
    uptime_human: formatUptime(uptime),
    response_time: responseTime,
    memory_usage: getMemoryUsage(),
    checks: {
      database: dbHealth,
      filesystem: fsHealth
    },
    environment: {
      api_port: Deno.env.get('API_PORT') || '3000',
      log_level: Deno.env.get('LOG_LEVEL') || 'info',
      data_dir: Deno.env.get('DATA_DIR') || './data',
      memory_limit: Deno.env.get('API_MEMORY_LIMIT') || '256M'
    }
  })
})

// Readiness probe
health.get('/ready', async (c) => {
  try {
    // Check if database is accessible
    const dbHealth = await checkDatabaseHealth()
    
    if (dbHealth.status === 'healthy') {
      return c.json({
        status: 'ready',
        timestamp: new Date().toISOString()
      })
    } else {
      return c.json({
        status: 'not_ready',
        reason: 'Database not accessible',
        timestamp: new Date().toISOString()
      }, 503)
    }
  } catch (error) {
    return c.json({
      status: 'not_ready',
      reason: error.message,
      timestamp: new Date().toISOString()
    }, 503)
  }
})

// Liveness probe
health.get('/live', (c) => {
  return c.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime_ms: Date.now() - serverStartTime
  })
})

function formatUptime(uptimeMs: number): string {
  const seconds = Math.floor(uptimeMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

function getMemoryUsage() {
  try {
    const memInfo = Deno.memoryUsage()
    return {
      rss: Math.round(memInfo.rss / 1024 / 1024 * 100) / 100, // MB
      heapTotal: Math.round(memInfo.heapTotal / 1024 / 1024 * 100) / 100, // MB
      heapUsed: Math.round(memInfo.heapUsed / 1024 / 1024 * 100) / 100, // MB
      external: Math.round(memInfo.external / 1024 / 1024 * 100) / 100 // MB
    }
  } catch {
    return null
  }
}

async function checkDatabaseHealth() {
  try {
    const dataDir = Deno.env.get('DATA_DIR') || './data'
    const dbPath = `${dataDir}/webhooks.db`
    
    // Check if we can access the database directory
    await Deno.stat(dataDir)
    
    // Try to access database file (it will be created if it doesn't exist)
    try {
      await Deno.stat(dbPath)
    } catch {
      // Database file doesn't exist yet, that's ok
    }
    
    return {
      status: 'healthy',
      message: 'Database accessible',
      database_path: dbPath
    }
  } catch (error) {
    return {
      status: 'error',
      message: `Database check failed: ${error.message}`
    }
  }
}

function checkFileSystemHealth() {
  try {
    const dataDir = Deno.env.get('DATA_DIR') || './data'
    
    // Check if data directory is writable
    Deno.statSync(dataDir)
    
    return {
      status: 'healthy',
      message: 'File system accessible',
      data_directory: dataDir
    }
  } catch (error) {
    return {
      status: 'error',
      message: `File system check failed: ${error.message}`
    }
  }
}

export { health as healthRoutes }
