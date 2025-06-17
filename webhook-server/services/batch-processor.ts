/*
 * Batch Processor Service for NS8 Mail Webhooks Server
 * 
 * Copyright (C) 2025 Lee M. Lwando <leemlwando@gmail.com>
 * Licensed under GPL-3.0
 */

export interface BatchJob {
  id: string
  type: 'webhook_delivery' | 'scheduled_execution' | 'cleanup'
  status: 'pending' | 'running' | 'completed' | 'failed'
  payload: any
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

export class BatchProcessor {
  private jobs: Map<string, BatchJob> = new Map()
  private processing = false
  private processingInterval?: number

  constructor() {
    // Start processing jobs every 10 seconds
    this.processingInterval = setInterval(() => {
      this.processJobs()
    }, 10000)
  }

  addJob(type: BatchJob['type'], payload: any): string {
    const job: BatchJob = {
      id: crypto.randomUUID(),
      type,
      status: 'pending',
      payload,
      created_at: new Date().toISOString()
    }

    this.jobs.set(job.id, job)
    return job.id
  }

  getJob(id: string): BatchJob | undefined {
    return this.jobs.get(id)
  }

  getJobs(status?: BatchJob['status']): BatchJob[] {
    const jobs = Array.from(this.jobs.values())
    return status ? jobs.filter(job => job.status === status) : jobs
  }

  private async processJobs() {
    if (this.processing) {
      return
    }

    this.processing = true

    try {
      const pendingJobs = this.getJobs('pending')
      
      for (const job of pendingJobs.slice(0, 5)) { // Process max 5 jobs at once
        await this.processJob(job)
      }
    } catch (error) {
      console.error('Error processing batch jobs:', error)
    } finally {
      this.processing = false
    }
  }

  private async processJob(job: BatchJob) {
    try {
      // Update job status
      job.status = 'running'
      job.started_at = new Date().toISOString()
      this.jobs.set(job.id, job)

      // Process based on job type
      switch (job.type) {
        case 'webhook_delivery':
          await this.processWebhookDelivery(job)
          break
        case 'scheduled_execution':
          await this.processScheduledExecution(job)
          break
        case 'cleanup':
          await this.processCleanup(job)
          break
        default:
          throw new Error(`Unknown job type: ${job.type}`)
      }

      // Mark as completed
      job.status = 'completed'
      job.completed_at = new Date().toISOString()
      this.jobs.set(job.id, job)

    } catch (error) {
      // Mark as failed
      job.status = 'failed'
      job.completed_at = new Date().toISOString()
      job.error_message = error instanceof Error ? error.message : 'Unknown error'
      this.jobs.set(job.id, job)
    }
  }

  private async processWebhookDelivery(job: BatchJob) {
    const { webhooks, payload } = job.payload
    
    // This would integrate with the delivery service
    console.log(`Processing webhook delivery for ${webhooks.length} webhooks`)
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1000))
  }

  private async processScheduledExecution(job: BatchJob) {
    const { scheduledWebhookId } = job.payload
    
    console.log(`Processing scheduled execution for webhook ${scheduledWebhookId}`)
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 500))
  }

  private async processCleanup(job: BatchJob) {
    const { type, olderThanDays } = job.payload
    
    console.log(`Processing cleanup for ${type} older than ${olderThanDays} days`)
    
    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 2000))
  }

  // Cleanup completed/failed jobs older than specified days
  cleanupJobs(olderThanDays: number = 7) {
    const cutoffTime = new Date(Date.now() - olderThanDays * 24 * 60 * 60 * 1000)
    
    for (const [id, job] of this.jobs.entries()) {
      if (job.status === 'completed' || job.status === 'failed') {
        const jobTime = new Date(job.completed_at || job.created_at)
        if (jobTime < cutoffTime) {
          this.jobs.delete(id)
        }
      }
    }
  }

  // Get statistics
  getStats() {
    const jobs = Array.from(this.jobs.values())
    
    return {
      total_jobs: jobs.length,
      pending_jobs: jobs.filter(j => j.status === 'pending').length,
      running_jobs: jobs.filter(j => j.status === 'running').length,
      completed_jobs: jobs.filter(j => j.status === 'completed').length,
      failed_jobs: jobs.filter(j => j.status === 'failed').length,
      processing: this.processing
    }
  }

  shutdown() {
    if (this.processingInterval) {
      clearInterval(this.processingInterval)
      this.processingInterval = undefined
    }
  }
}
