#!/usr/bin/env python3
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

commits = [
    {
        'hash': 'e93547a78b853d47eef672f5ce9865d290c7865f',
        'author': 'Lucia Alexandra Little',
        'email': '73139437+chufakiks@users.noreply.github.com',
        'date': '2025-12-29 18:34:07',
        'title': 'Remove GitHub sponsors and unused animation features',
        'body': '''Remove FUNDING.yml and clean up unused pose animation settings
and Three.js animation track getters that are no longer needed.

Generated with Claude Code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>'''
    },
    {
        'hash': 'e6dae2b3abbd38ee2cbbee2c1e05ed283ee9dc34',
        'author': 'Lucia Alexandra Little',
        'email': '73139437+chufakiks@users.noreply.github.com',
        'date': '2025-12-29 11:36:54',
        'title': 'Add pose toggle and improve UI layout',
        'body': '''- Add displayPose input to video component for optional pose overlay
- Add toggle button to show/hide pose skeleton
- Simplify desktop layout with centered card design
- Video on left (60%), translation output on right (40%)
- Blue background with white card, dark mode support

Generated with Claude Code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>'''
    },
    {
        'hash': '4b0507ac7928a7bca7d7f5c0e0ebabea555abd18',
        'author': 'Lucia Alexandra Little',
        'email': '73139437+chufakiks@users.noreply.github.com',
        'date': '2025-12-29 10:44:10',
        'title': 'Fix broken imports after component removal',
        'body': '''- Remove url helper, CookieConsent, and embed logic from app.component
- Simplify routes to only translate page (remove not-found, settings)
- Remove SignWriting imports from video component
- Remove input button component (webcam-only mode)
- Simplify signed-to-spoken component (remove SignWriting, language selectors)
- Simplify translate-desktop component

Generated with Claude Code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>'''
    },
    {
        'hash': '6fda26d40da03e9498e71cb44ca7e4a45fbda1d5',
        'author': 'Lucia Alexandra Little',
        'email': '73139437+chufakiks@users.noreply.github.com',
        'date': '2025-12-29 10:32:28',
        'title': 'Remove unused components for ASL-to-English focus',
        'body': '''Delete SignWriting module, language selectors, file upload/drop
components, and URL helpers since app now focuses on webcam-based
ASL-to-English translation only.

Generated with Claude Code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>'''
    },
    {
        'hash': '548c0b1663daa66663b6bd800e2f085e37beadc0',
        'author': 'Lucia Alexandra Little',
        'email': '73139437+chufakiks@users.noreply.github.com',
        'date': '2025-12-29 10:25:38',
        'title': 'Remove test files and test configuration',
        'body': '''Delete all *.spec.ts files, karma.conf.js, and tsconfig.spec.json
since tests are not being used currently.

Generated with Claude Code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>'''
    }
]

# Create PDF
output_file = 'Sign2Speech_Last_5_Commits.pdf'
doc = SimpleDocTemplate(output_file, pagesize=letter,
                        rightMargin=72, leftMargin=72,
                        topMargin=72, bottomMargin=18)

# Container for the 'Flowable' objects
elements = []

# Define styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=12,
    alignment=TA_CENTER,
)

subtitle_style = ParagraphStyle(
    'CustomSubtitle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#666666'),
    spaceAfter=20,
    alignment=TA_CENTER,
)

commit_title_style = ParagraphStyle(
    'CommitTitle',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.HexColor('#0066cc'),
    spaceAfter=6,
    spaceBefore=12,
)

metadata_style = ParagraphStyle(
    'Metadata',
    parent=styles['Normal'],
    fontSize=9,
    textColor=colors.HexColor('#444444'),
    spaceAfter=3,
)

body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#333333'),
    spaceAfter=6,
    leftIndent=12,
)

# Add title
title = Paragraph("Sign2Speech - Last 5 Commits", title_style)
elements.append(title)

# Add generation date
subtitle = Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style)
elements.append(subtitle)

elements.append(Spacer(1, 0.2*inch))

# Add commits
for i, commit in enumerate(commits, 1):
    # Commit title
    commit_title = Paragraph(f"<b>Commit #{i}: {commit['title']}</b>", commit_title_style)
    elements.append(commit_title)

    # Commit hash
    hash_text = Paragraph(f"<font face='Courier' size='8'>Hash: {commit['hash'][:12]}</font>", metadata_style)
    elements.append(hash_text)

    # Author
    author_text = Paragraph(f"<b>Author:</b> {commit['author']} &lt;{commit['email']}&gt;", metadata_style)
    elements.append(author_text)

    # Date
    date_text = Paragraph(f"<b>Date:</b> {commit['date']}", metadata_style)
    elements.append(date_text)

    elements.append(Spacer(1, 0.1*inch))

    # Commit body - split into lines
    body_lines = commit['body'].split('\n')
    for line in body_lines:
        if line.strip():
            # Escape special characters for XML
            line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            body_para = Paragraph(line_escaped, body_style)
            elements.append(body_para)

    # Add separator
    if i < len(commits):
        elements.append(Spacer(1, 0.2*inch))
        # Add a horizontal line
        from reportlab.platypus import HRFlowable
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=0.1*inch))

# Build PDF
doc.build(elements)
print(f"PDF generated successfully: {output_file}")
