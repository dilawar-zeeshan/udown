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
    const { url, format_id, job_id, session_id } = await req.json()
    if (!url || !format_id || !job_id) throw new Error('url, format_id, and job_id are required')

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 1. Update Job Status
    await supabase.from('downloads_queue').update({
      format_id,
      status: 'pending_download'
    }).eq('id', job_id)

    // 2. Trigger GitHub Action
    const GITHUB_REPO = Deno.env.get('GITHUB_REPO')
    const GH_TOKEN = Deno.env.get('GH_TOKEN')

    if (GITHUB_REPO && GH_TOKEN) {
      console.log(`🚀 Triggering GHA Download for job ${job_id} on repos/${GITHUB_REPO}`)
      try {
        const fetchUrl = `https://api.github.com/repos/${GITHUB_REPO.trim()}/actions/workflows/video_worker.yml/dispatches`
        const ghaResponse = await fetch(fetchUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${GH_TOKEN.trim()}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Supabase-Edge-Function-VDownloader'
          },
          body: JSON.stringify({
            ref: 'main',
            inputs: {
              job_id: job_id,
              url: url,
              mode: 'download',
              format_id: format_id,
              session_id: session_id
            }
          })
        })
        console.log(`📡 GHA Trigger Status for ${job_id}: ${ghaResponse.status} ${ghaResponse.statusText}`)
        if (!ghaResponse.ok) {
          const errorBody = await ghaResponse.text()
          console.error(`❌ GHA Trigger Failed for ${job_id}: ${errorBody}`)
        } else {
          console.log(`✅ GHA Triggered Successfully for ${job_id}`)
        }
      } catch (e) {
        console.error(`💥 Fatal error triggering GHA for ${job_id}:`, e)
      }
    } else {
      console.warn('⚠️ GITHUB_REPO or GH_TOKEN missing, skipping GHA trigger.')
    }

    return new Response(JSON.stringify({ success: true, job_id }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})
