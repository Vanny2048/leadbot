import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import path from 'path';
import { fileURLToPath } from 'url';

import { getDb } from './src/db.js';
import { sendLeadQualifiedEmail } from './src/services/email.js';
import { createTwilioClient, sendSms, createOutboundCall } from './src/services/twilio.js';
import { qualifyLeadWithAI } from './src/services/ai.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Initialize dependencies
const db = getDb();
const twilioClient = createTwilioClient();

// Health
app.get('/health', (req, res) => {
  res.json({ ok: true, uptimeSec: process.uptime() });
});

// Create a lead (e.g., from website form or DM). Triggers outbound call attempt.
app.post('/leads', async (req, res) => {
  try {
    const {
      fullName,
      phoneE164,
      email,
      interest, // e.g., veneers, whitening, Invisalign
      source = 'web',
    } = req.body;

    if (!fullName || !phoneE164) {
      return res.status(400).json({ error: 'fullName and phoneE164 are required' });
    }

    const stmt = db.prepare(`
      INSERT INTO leads (full_name, phone_e164, email, interest, source, status, created_at)
      VALUES (@fullName, @phoneE164, @email, @interest, @source, 'new', strftime('%s','now'))
    `);
    const info = stmt.run({ fullName, phoneE164, email, interest, source });

    const leadId = info.lastInsertRowid;

    // Trigger outbound call attempt if Twilio is configured
    if (twilioClient) {
      try {
        await createOutboundCall({
          client: twilioClient,
          to: phoneE164,
          from: process.env.TWILIO_CALLER_ID,
          leadId,
          // Twilio will request TwiML from this URL
          url: `${process.env.PUBLIC_BASE_URL || `http://localhost:${port}`}/twilio/voice/outbound?leadId=${leadId}`,
        });
      } catch (err) {
        console.error('Failed to initiate outbound call:', err.message);
      }
    } else {
      console.warn('Twilio not configured; skipping outbound call.');
    }

    res.status(201).json({ leadId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create lead' });
  }
});

// Simple web chat endpoint (text-in, text-out)
app.post('/chat', async (req, res) => {
  try {
    const { message, context } = req.body;
    const reply = await qualifyLeadWithAI({
      mode: 'chat',
      prompt: message,
      context,
    });
    res.json({ reply });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Chat failed' });
  }
});

// Twilio Voice: inbound call webhook
app.post('/twilio/voice/inbound', async (req, res) => {
  // Minimal IVR that gathers speech and routes to qualification
  res.type('text/xml');
  const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">Thank you for calling. One moment while I gather a few details.</Say>
  <Gather input="speech dtmf" numDigits="1" action="/twilio/voice/qualify" method="POST" timeout="5">
    <Say voice="Polly.Joanna">Are you interested in cosmetic dental services like veneers, Invisalign, or whitening? Press 1 for yes, or say yes. Press 2 for no, or say no.</Say>
  </Gather>
  <Say voice="Polly.Joanna">I didn't catch that. Goodbye.</Say>
  <Hangup/>
</Response>`;
  res.send(twiml);
});

// Twilio Voice: outbound call script
app.post('/twilio/voice/outbound', async (req, res) => {
  const { leadId } = req.query;
  res.type('text/xml');
  const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">Hi, this is the concierge from your selected cosmetic dental practice. We received your request. I have a quick question to match you with the right specialist.</Say>
  <Gather input="speech dtmf" numDigits="1" action="/twilio/voice/qualify?leadId=${leadId || ''}" method="POST" timeout="6">
    <Say voice="Polly.Joanna">Are you looking for veneers, Invisalign, whitening, or a smile makeover? You can say your interest now. Or press 1 for veneers, 2 for Invisalign, 3 for whitening.</Say>
  </Gather>
  <Say voice="Polly.Joanna">Thanks for your time. Goodbye.</Say>
  <Hangup/>
</Response>`;
  res.send(twiml);
});

// Twilio Voice: qualification handler for both inbound and outbound gathers
app.post('/twilio/voice/qualify', async (req, res) => {
  try {
    const speechResult = req.body.SpeechResult || '';
    const digits = req.body.Digits || '';
    const leadId = req.query.leadId;

    let inferredInterest = null;
    if (digits === '1') inferredInterest = 'veneers';
    else if (digits === '2') inferredInterest = 'invisalign';
    else if (digits === '3') inferredInterest = 'whitening';

    const { qualified, reason, interest } = await qualifyLeadWithAI({
      mode: 'qualify',
      prompt: speechResult,
      interestHint: inferredInterest,
    });

    // Update DB if we have a leadId
    if (leadId) {
      const update = db.prepare(`UPDATE leads SET status=@status, interest=COALESCE(@interest, interest), qualified_reason=@reason, updated_at=strftime('%s','now') WHERE id=@leadId`);
      update.run({
        status: qualified ? 'qualified' : 'disqualified',
        interest: interest || inferredInterest || null,
        reason,
        leadId,
      });

      // Fetch lead row
      const lead = db.prepare('SELECT * FROM leads WHERE id = ?').get(leadId);

      // If qualified, send email and SMS with booking link
      if (qualified && lead) {
        const bookingLink = process.env.BOOKING_URL || 'https://cal.com/your-practice/consult';
        if (lead.email) {
          try {
            await sendLeadQualifiedEmail({
              to: lead.email,
              fullName: lead.full_name,
              bookingLink,
              interest: interest || lead.interest,
            });
          } catch (err) {
            console.error('Email send failed:', err.message);
          }
        }
        if (twilioClient && lead.phone_e164) {
          try {
            await sendSms({ client: twilioClient, to: lead.phone_e164, body: `Thanks for your interest! Book your consult here: ${bookingLink}` });
          } catch (err) {
            console.error('SMS send failed:', err.message);
          }
        }
      }
    }

    res.type('text/xml');
    const responseText = qualified
      ? 'Great, you seem like a good fit. I just sent a booking link by email and text. Please choose a convenient time.'
      : 'Thanks for your time. Based on your answers, we may not be the best fit at the moment. Have a great day.';

    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">${responseText}</Say>
  <Hangup/>
</Response>`;
    res.send(twiml);
  } catch (err) {
    console.error(err);
    res.type('text/xml');
    res.send(`<?xml version="1.0" encoding="UTF-8"?>\n<Response><Say>Sorry, something went wrong.</Say><Hangup/></Response>`);
  }
});

// Twilio call status callback (optional)
app.post('/twilio/voice/status', (req, res) => {
  try {
    const { CallStatus, CallSid } = req.body;
    if (CallStatus && CallSid) {
      db.prepare(`INSERT INTO call_events (call_sid, status, created_at) VALUES (?,?,strftime('%s','now'))`).run(CallSid, CallStatus);
    }
  } catch (err) {
    console.error('Failed to record call status:', err.message);
  }
  res.sendStatus(204);
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
  if (!process.env.TWILIO_ACCOUNT_SID || !process.env.TWILIO_AUTH_TOKEN || !process.env.TWILIO_CALLER_ID) {
    console.warn('Warning: Twilio env variables are not fully set. Outbound calls/SMS will be disabled.');
  }
  if (!process.env.SMTP_HOST) {
    console.warn('Warning: SMTP env variables are not set. Emails will be disabled.');
  }
});