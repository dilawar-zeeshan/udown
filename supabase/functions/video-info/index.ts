import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { url } = await req.json()
    if (!url) throw new Error('URL is required')

    // Detect platform
    let platform = 'unknown'
    if (url.includes('youtube.com') || url.includes('youtu.be')) platform = 'YouTube'
    else if (url.includes('instagram.com')) platform = 'Instagram'
    else if (url.includes('tiktok.com')) platform = 'TikTok'
    else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'Twitter'
    else if (url.includes('facebook.com')) platform = 'Facebook'

    // Rate Limiting Logic
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const clientIP = req.headers.get('x-real-ip') || req.headers.get('x-forwarded-for') || 'unknown'
    
    // Check rate limit (simplified for brevity, should use rate_limits table)
    const { data: limitData, error: limitError } = await supabase
      .from('rate_limits')
      .select('*')
      .eq('ip', clientIP)
      .single()

    const now = new Date()
    if (limitData) {
      const lastRequest = new Date(limitData.last_request)
      const hoursSinceLast = (now.getTime() - lastRequest.getTime()) / (1000 * 60 * 60)
      
      if (hoursSinceLast < 1 && limitData.request_count >= 10) {
        return new Response(JSON.stringify({ error: 'Rate limit exceeded. Try again later.' }), {
          status: 429,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }

      await supabase.from('rate_limits').update({
        request_count: hoursSinceLast >= 1 ? 1 : limitData.request_count + 1,
        last_request: now.toISOString()
      }).eq('ip', clientIP)
    } else {
      await supabase.from('rate_limits').insert({ ip: clientIP, request_count: 1, last_request: now.toISOString() })
    }

    // Log the download attempt
    await supabase.from('downloads_log').insert({
      url,
      platform,
      ip: clientIP
    })

    // 4. Create a Job in the Downloads Queue
    const { data: job, error: jobError } = await supabase
      .from('downloads_queue')
      .insert({
        url,
        status: 'pending_info'
      })
      .select()
      .single()

    if (jobError) throw jobError

    // 5. Trigger GitHub Action
    const GITHUB_REPO = Deno.env.get('GITHUB_REPO') // e.g., "username/vdownloader"
    const GH_TOKEN = Deno.env.get('GH_TOKEN')

    if (GITHUB_REPO && GH_TOKEN) {
      console.log(`🚀 Triggering GHA for job ${job.id}`)
      try {
        await fetch(`https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/video_worker.yml/dispatches`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${GH_TOKEN}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ref: 'main',
            inputs: {
              job_id: job.id,
              url: url,
              mode: 'info'
            }
          })
        })
      } catch (e) {
        console.error('Error triggering GHA:', e)
      }
    }

    return new Response(JSON.stringify({ job_id: job.id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})
