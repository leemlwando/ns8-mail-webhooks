/*
 * Health Check Script for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

try {
  const port = Deno.env.get('API_PORT') || '3000'
  const response = await fetch(`http://localhost:${port}/health/live`)
  
  if (response.ok) {
    console.log('Health check passed')
    Deno.exit(0)
  } else {
    console.error('Health check failed:', response.status)
    Deno.exit(1)
  }
} catch (error) {
  console.error('Health check error:', error.message)
  Deno.exit(1)
}
