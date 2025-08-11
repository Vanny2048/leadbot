import nodemailer from 'nodemailer';

function getTransport() {
  if (process.env.SMTP_URL) {
    return nodemailer.createTransport(process.env.SMTP_URL);
  }
  if (process.env.SMTP_HOST) {
    return nodemailer.createTransport({
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT || 587),
      secure: Boolean(process.env.SMTP_SECURE === 'true'),
      auth: process.env.SMTP_USER && process.env.SMTP_PASS ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS } : undefined,
    });
  }
  return null;
}

export async function sendLeadQualifiedEmail({ to, fullName, bookingLink, interest }) {
  const transport = getTransport();
  if (!transport) {
    console.warn('No SMTP configured; skipping email');
    return;
  }
  const from = process.env.MAIL_FROM || 'no-reply@practice.local';
  const subject = `Next steps to book your cosmetic dental consult`;
  const html = `
    <p>Hi ${fullName || ''},</p>
    <p>Great news — you qualify for a consult${interest ? ' regarding ' + interest : ''}. Use the link below to pick a time that works for you:</p>
    <p><a href="${bookingLink}">${bookingLink}</a></p>
    <p>We look forward to helping you achieve your best smile.</p>
  `;
  await transport.sendMail({ to, from, subject, html });
}