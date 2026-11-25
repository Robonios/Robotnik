/**
 * Robotnik Lead Capture
 * ---------------------
 * Apps Script that receives Early Access form submissions from
 * robotnik.world and appends them to this Sheet.
 *
 * Setup (Robert, one time):
 *   1. Create a Google Sheet titled "Robotnik Early Access Leads".
 *   2. Extensions → Apps Script → paste this file.
 *   3. Save; name the project "Robotnik Lead Capture".
 *   4. Deploy → New deployment → Type: Web app
 *        Description: "Robotnik Early Access Form Handler"
 *        Execute as:  Me (robert@robotnik.world)
 *        Who has access: Anyone
 *   5. Copy the /exec URL and paste it into js/nav.js EARLY_ACCESS_URL.
 *
 * Wire format
 *   POST  (Content-Type: text/plain; browser CORS-simple)
 *   Body: JSON object with keys {
 *           name, email, organisation, role, linkedin,
 *           use_case, how_did_you_hear, source_page, user_agent
 *         }
 *   Response: {"status": "ok"}  on success
 *             {"status": "error", "message": "..."}  on failure
 *
 * Behaviour
 *   - Name, email, organisation and the source page are mandatory; the
 *     waitlist form (November 2026) asks for role and a message as optional
 *     and no longer asks for LinkedIn or the referral. Until this version is
 *     redeployed, js/nav.js sends a placeholder for each of those four, so
 *     the April deployment, which requires them, accepts the form.
 *   - Basic email format check.
 *   - LinkedIn URL is accepted as-is; if it doesn't contain
 *     "linkedin.com/in/" we log a note but don't reject.
 *   - Duplicate emails: existing row is overwritten in place rather
 *     than appending — the Timestamp column updates to the newest
 *     submission.
 */

const HEADERS = [
  'Timestamp', 'Name', 'Email', 'Organisation', 'Role', 'LinkedIn',
  'Use Case', 'How Did You Hear', 'Source Page', 'User Agent',
];

// Keys in the posted JSON that must be present and non-empty.
const REQUIRED_FIELDS = ['name', 'email', 'organisation', 'source_page'];

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return json({ status: 'error', message: 'Empty request body' });
    }
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
    } catch (parseErr) {
      return json({ status: 'error', message: 'Request body is not valid JSON' });
    }

    // Required-field validation.
    for (const field of REQUIRED_FIELDS) {
      const val = payload[field];
      if (typeof val !== 'string' || !val.trim()) {
        return json({
          status: 'error',
          message: 'Missing required field: ' + field,
        });
      }
    }

    // Basic email format check — one @, domain with a dot.
    const email = payload.email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return json({ status: 'error', message: 'Invalid email format' });
    }

    // LinkedIn URL is soft-checked: log if it doesn't look like a
    // profile URL, but still accept — the column preserves whatever
    // the user entered so Robert can follow up regardless.
    const linkedin = String(payload.linkedin || '').trim();
    if (linkedin.indexOf('linkedin.com/in/') === -1) {
      console.log('LinkedIn URL did not match expected pattern:', linkedin);
    }

    const row = [
      new Date().toISOString(),
      payload.name.trim(),
      email,
      payload.organisation.trim(),
      String(payload.role || '').trim(),
      linkedin,
      String(payload.use_case || '').trim(),
      String(payload.how_did_you_hear || '').trim(),
      payload.source_page.trim(),
      (payload.user_agent || '').toString().slice(0, 500),
    ];

    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    ensureHeaders(sheet);

    const existingRow = findEmailRow(sheet, email);
    if (existingRow > 0) {
      console.log('Duplicate submission from', email, '— overwriting row', existingRow);
      sheet.getRange(existingRow, 1, 1, row.length).setValues([row]);
    } else {
      sheet.appendRow(row);
    }

    return json({ status: 'ok' });
  } catch (err) {
    console.error('Unhandled error in doPost:', err && err.stack || err);
    return json({
      status: 'error',
      message: (err && err.message) ? err.message : String(err),
    });
  }
}

// Convenience: hitting the URL in a browser shows a liveness ping.
function doGet() {
  return json({
    status: 'ok',
    message: 'Robotnik Lead Capture is live. POST JSON to this URL.',
  });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ensureHeaders(sheet) {
  // Re-write the header row if the sheet was created empty. Idempotent;
  // won't clobber a sheet that already has headers.
  const firstRow = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
  const blank = firstRow.every(function(c) { return c === '' || c == null; });
  if (blank) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.setFrozenRows(1);
  }
}

function findEmailRow(sheet, email) {
  // Email column is index 3 (Timestamp, Name, Email, …). Returns the
  // 1-indexed row number if the email already exists, or 0 otherwise.
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return 0;
  const emails = sheet.getRange(2, 3, lastRow - 1, 1).getValues();
  const needle = email.toLowerCase();
  for (let i = 0; i < emails.length; i++) {
    const cell = (emails[i][0] || '').toString().toLowerCase();
    if (cell === needle) return i + 2;
  }
  return 0;
}
