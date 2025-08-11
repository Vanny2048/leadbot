import OpenAI from 'openai';

let openaiClient = null;
if (process.env.OPENAI_API_KEY) {
  openaiClient = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

const KEYWORDS_QUALIFY = ['veneers', 'invisalign', 'whitening', 'smile makeover', 'smile', 'cosmetic'];
const KEYWORDS_DISQUALIFY = ['emergency', 'root canal', 'extraction', 'toothache', 'medicaid', 'insurance only'];

export async function qualifyLeadWithAI({ mode = 'qualify', prompt = '', context = {}, interestHint = null }) {
  if (mode === 'chat') {
    // Simple echo/fallback chat if no API key
    if (!openaiClient) {
      return `Thanks! Could you share whether you're interested in veneers, Invisalign, whitening, or a smile makeover?`;
    }
    const completion = await openaiClient.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      messages: [
        { role: 'system', content: 'You are a helpful concierge for a cosmetic dental practice in Los Angeles. Be concise and friendly.' },
        { role: 'user', content: prompt },
      ],
      temperature: 0.3,
      max_tokens: 120,
    });
    return completion.choices[0]?.message?.content?.trim() || 'Thanks for reaching out!';
  }

  // Qualification mode
  let interest = interestHint;
  const lower = String(prompt || '').toLowerCase();
  for (const kw of KEYWORDS_QUALIFY) {
    if (lower.includes(kw)) {
      interest = interest || kw;
      break;
    }
  }
  let disqualify = false;
  for (const kw of KEYWORDS_DISQUALIFY) {
    if (lower.includes(kw)) {
      disqualify = true;
      break;
    }
  }

  if (!openaiClient) {
    const qualified = !disqualify && (interest != null);
    const reason = qualified ? 'Matched elective cosmetic interest keywords.' : 'Did not match cosmetic service intent or indicated general/emergency dentistry.';
    return { qualified, reason, interest };
  }

  const systemPrompt = `You qualify inbound leads for a cosmetic dentistry practice in Los Angeles (Beverly Hills, West Hollywood, Santa Monica, Pasadena, Glendale, Burbank, Culver City). Only elective services like veneers, Invisalign, whitening, smile makeovers. Disqualify clear general dentistry/emergency. Output JSON with keys: qualified (boolean), reason (string <= 120 chars), interest (string or null from {veneers,invisalign,whitening,smile makeover}).`;

  const completion = await openaiClient.chat.completions.create({
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: lower },
    ],
    temperature: 0.2,
    max_tokens: 120,
    response_format: { type: 'json_object' },
  });

  try {
    const parsed = JSON.parse(completion.choices[0]?.message?.content || '{}');
    return {
      qualified: Boolean(parsed.qualified),
      reason: parsed.reason || 'No reason provided',
      interest: parsed.interest || interest || null,
    };
  } catch (e) {
    const qualified = !disqualify && (interest != null);
    const reason = qualified ? 'Matched elective cosmetic interest keywords.' : 'Did not match cosmetic service intent or indicated general/emergency dentistry.';
    return { qualified, reason, interest };
  }
}