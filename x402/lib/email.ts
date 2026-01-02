import nodemailer from 'nodemailer'

const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app'

/**
 * Get configured email transporter (returns null if SMTP not configured)
 */
function getTransporter() {
  if (!process.env.SMTP_HOST) {
    return null
  }

  return nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: process.env.SMTP_PORT === '465', // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  })
}

/**
 * Send email (no-op if SMTP not configured)
 */
async function sendEmail(to: string, subject: string, html: string): Promise<boolean> {
  const transporter = getTransporter()
  if (!transporter) {
    console.log(`[Email] Would send to ${to}: ${subject}`)
    return false
  }

  try {
    await transporter.sendMail({
      from: process.env.SMTP_FROM || process.env.SMTP_USER,
      to,
      subject,
      html,
    })
    return true
  } catch (error) {
    console.error('Email send error:', error)
    return false
  }
}

/**
 * Welcome email (sent after first login/signup)
 */
export async function sendWelcomeEmail(email: string): Promise<boolean> {
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Welcome to QuickSync!</h1>
        </div>
        <div class="content">
          <p>Hi there,</p>
          <p>Thanks for signing up for QuickSync! We're excited to help you convert your bank and credit card statements into clean CSV or QBO files.</p>
          
          <p><strong>Get started:</strong></p>
          <ol>
            <li>Upload a PDF statement</li>
            <li>Preview your results (with watermark)</li>
            <li>Download clean files when ready</li>
          </ol>
          
          <p><strong>🎁 New user bonus:</strong> Your first file is free! Try it out without any payment.</p>
          
          <p style="text-align: center;">
            <a href="${appUrl}" class="button">Start Converting</a>
          </p>
          
          <p>If you have any questions, just reply to this email. We're here to help!</p>
          
          <p>Best,<br>The QuickSync Team</p>
        </div>
        <div class="footer">
          <p>QuickSync - Convert PDF statements to CSV/QBO</p>
          <p><a href="${appUrl}">Visit our website</a></p>
        </div>
      </div>
    </body>
    </html>
  `

  return sendEmail(email, 'Welcome to QuickSync! 🎉', html)
}

/**
 * File ready email (sent after processing completes)
 */
export async function sendFileReadyEmail(
  email: string,
  jobId: string,
  fileName: string,
  rowCount?: number,
  confidenceScore?: number
): Promise<boolean> {
  const jobUrl = `${appUrl}/jobs/${jobId}`
  const rowCountText = rowCount ? `${rowCount} transactions extracted` : 'Processing complete'
  const confidenceText = confidenceScore !== undefined ? ` (${confidenceScore}% confidence)` : ''

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .info-box { background: white; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Your file is ready! ✅</h1>
        </div>
        <div class="content">
          <p>Hi there,</p>
          <p>Great news! Your file <strong>${fileName}</strong> has been processed successfully.</p>
          
          <div class="info-box">
            <p><strong>Results:</strong></p>
            <ul>
              <li>${rowCountText}${confidenceText}</li>
              <li>CSV and QBO formats ready</li>
            </ul>
          </div>
          
          <p>You can preview your results and download the files:</p>
          
          <p style="text-align: center;">
            <a href="${jobUrl}" class="button">View & Download</a>
          </p>
          
          <p><small>If you're a new user, your first file is free! No payment required.</small></p>
          
          <p>Best,<br>The QuickSync Team</p>
        </div>
        <div class="footer">
          <p>QuickSync - Convert PDF statements to CSV/QBO</p>
          <p><a href="${appUrl}">Visit our website</a></p>
        </div>
      </div>
    </body>
    </html>
  `

  return sendEmail(email, `Your file "${fileName}" is ready`, html)
}

/**
 * Abandoned cart email (sent if user uploaded but hasn't paid after 24 hours)
 */
export async function sendAbandonedCartEmail(
  email: string,
  jobId: string,
  fileName: string
): Promise<boolean> {
  const jobUrl = `${appUrl}/jobs/${jobId}`

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f59e0b; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Your file is waiting! 📄</h1>
        </div>
        <div class="content">
          <p>Hi there,</p>
          <p>We noticed you uploaded <strong>${fileName}</strong> but haven't downloaded it yet.</p>
          
          <p>Your file has been processed and is ready to download. Preview the results and get your clean CSV or QBO file.</p>
          
          <p style="text-align: center;">
            <a href="${jobUrl}" class="button">View Your File</a>
          </p>
          
          <p><small>Remember: If you're a new user, your first file is free!</small></p>
          
          <p>Questions? Just reply to this email.</p>
          
          <p>Best,<br>The QuickSync Team</p>
        </div>
        <div class="footer">
          <p>QuickSync - Convert PDF statements to CSV/QBO</p>
          <p><a href="${appUrl}">Visit our website</a></p>
        </div>
      </div>
    </body>
    </html>
  `

  return sendEmail(email, `Don't forget: Your file "${fileName}" is ready`, html)
}

