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
    const urlPayload = new URL(req.url)
    const jobId = urlPayload.searchParams.get('job_id')

    if (!jobId) throw new Error('job_id is required')

    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 1. Get Job Info to find storage path
    const { data: job, error: jobError } = await supabase
      .from('downloads_queue')
      .select('result_url')
      .eq('id', jobId)
      .single()

    if (jobError || !job) throw new Error('Job not found')
    
    // Extract path from public URL
    // Public URL format: https://.../storage/v1/object/public/video/downloads/filename.mp4
    const urlParts = job.result_url.split('/public/video/')
    if (urlParts.length < 2) throw new Error('Invalid result URL')
    const storagePath = urlParts[1]

    // 2. Download from Storage
    const { data: fileData, error: downloadError } = await supabase
      .storage
      .from('video')
      .download(storagePath)

    if (downloadError) throw downloadError

    // 3. Delete from Storage (Fire and forget, or handle after response)
    // In Deno, we can use a small delay or a background promise
    (async () => {
        const { error: deleteError } = await supabase.storage.from('video').remove([storagePath])
        if (deleteError) console.error('Error deleting file:', deleteError)
        else console.log(`🗑️ Successfully deleted ${storagePath} after serve`)
    })()

    return new Response(fileData, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'video/mp4',
        'Content-Disposition': `attachment; filename="video.mp4"`
      }
    })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})
