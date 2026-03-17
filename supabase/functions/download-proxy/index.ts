import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { url, format_id, job_id } = await req.json()
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
      console.log(`🚀 Triggering GHA Download for job ${job_id}`)
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
              job_id: job_id,
              url: url,
              mode: 'download',
              format_id: format_id
            }
          })
        })
      } catch (e) {
        console.error('Error triggering GHA:', e)
      }
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
