/**
 * Google Apps Script for Conference Notes
 *
 * This script receives summaries from the Conference Notes app
 * and appends them to a Google Doc.
 *
 * SETUP:
 * 1. Create a new Google Doc for your conference report
 * 2. Copy this doc's ID from the URL (the long string between /d/ and /edit)
 * 3. Go to https://script.google.com and create a new project
 * 4. Paste this code and replace YOUR_DOCUMENT_ID below
 * 5. Deploy as Web App (Execute as: Me, Access: Anyone)
 * 6. Copy the Web App URL and set it as GOOGLE_SCRIPT_URL in your app
 */

// Replace with your Google Doc ID
const DOCUMENT_ID = 'YOUR_DOCUMENT_ID';

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    const doc = DocumentApp.openById(DOCUMENT_ID);
    const body = doc.getBody();

    // Add a horizontal line separator (if not first entry)
    if (body.getText().trim() !== '') {
      body.appendHorizontalRule();
    }

    // Add the session title as heading
    const title = data.title || 'Untitled Session';
    const heading = body.appendParagraph(title);
    heading.setHeading(DocumentApp.ParagraphHeading.HEADING2);

    // Add date
    const date = data.date ? new Date(data.date).toLocaleDateString() : new Date().toLocaleDateString();
    const datePara = body.appendParagraph('Date: ' + date);
    datePara.setForegroundColor('#666666');
    datePara.setFontSize(10);

    // Add the summary content
    body.appendParagraph(''); // spacing

    // Parse and add the markdown content
    const lines = data.summary.split('\n');

    for (const line of lines) {
      if (line.startsWith('## ')) {
        // Section heading
        const heading = body.appendParagraph(line.substring(3));
        heading.setHeading(DocumentApp.ParagraphHeading.HEADING3);
        heading.setForegroundColor('#5046e5');
      } else if (line.startsWith('- ')) {
        // Bullet point
        const item = body.appendListItem(line.substring(2));
        item.setGlyphType(DocumentApp.GlyphType.BULLET);
      } else if (line.trim() !== '') {
        // Regular paragraph
        body.appendParagraph(line);
      }
    }

    // Add timestamp
    body.appendParagraph('');
    const timestamp = body.appendParagraph('Added: ' + new Date().toLocaleString());
    timestamp.setForegroundColor('#999999');
    timestamp.setFontSize(8);

    doc.saveAndClose();

    return ContentService
      .createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({ success: false, error: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      status: 'ok',
      message: 'Conference Notes Google Apps Script is running'
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

// Test function - run this to verify your setup
function testAppend() {
  const testData = {
    postData: {
      contents: JSON.stringify({
        title: 'Test Session',
        date: new Date().toISOString(),
        summary: '## Key Takeaways\n- This is a test\n- The integration is working\n\n## Action Items\n- Verify the document was updated'
      })
    }
  };

  doPost(testData);
  Logger.log('Test complete - check your document');
}
