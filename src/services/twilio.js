import twilio from 'twilio';

export function createTwilioClient() {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  if (!accountSid || !authToken) return null;
  return twilio(accountSid, authToken);
}

export async function createOutboundCall({ client, to, from, url, leadId }) {
  if (!client || !to || !from || !url) throw new Error('Missing params for outbound call');
  return client.calls.create({ to, from, url, statusCallback: process.env.PUBLIC_BASE_URL ? `${process.env.PUBLIC_BASE_URL}/twilio/voice/status` : undefined, machineDetection: 'Enable', record: true, timeout: 20 });
}

export async function sendSms({ client, to, body }) {
  if (!client || !to || !body) throw new Error('Missing params for SMS');
  const from = process.env.TWILIO_SMS_NUMBER || process.env.TWILIO_CALLER_ID;
  if (!from) throw new Error('Missing TWILIO_SMS_NUMBER or TWILIO_CALLER_ID');
  return client.messages.create({ to, from, body });
}