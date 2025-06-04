# CV Template Variables Guide

This document explains how to create a CV template for use with Operation CV.

## Available Variables

Your DOCX template can use any of these variables:

- `{{ summary }}` - Professional summary/profile section
- `{{ experience }}` - Work experience section
- `{{ education }}` - Education section
- `{{ skills }}` - Skills & certifications
- `{{ projects }}` - Project section 
- `{{ languages }}` - Languages section
- `{{ publications }}` - Publications section
- `{{ interests }}` - Interests section
- `{{ awards }}` - Awards section
- `{{ activities }}` - Activities section
- `{{ volunteering }}` - Volunteering experience
- `{{ extracurricular }}` - Extracurricular activities
- `{{ content }}` - Full CV content (used if sections aren't detected)

## Example Template Structure

Here's how a basic template might be structured:

```
[YOUR NAME]
[Contact Details]

PROFESSIONAL SUMMARY
{{ summary }}

EXPERIENCE
{{ experience }}

EDUCATION
{{ education }}

SKILLS & CERTIFICATIONS 
{{ skills }}

LANGUAGES
{{ languages }}

[Additional sections as needed...]
```

## Tips for Best Results

1. Create your template in DOCX format
2. Use consistent formatting (fonts, spacing, etc.)
3. Place variables exactly where the content should appear
4. Test with different CVs to ensure compatibility
5. Consider optional sections - they'll be skipped if empty

## Common Issues

- If a section isn't found in the CV, its variable will be replaced with an empty string
- Maintain proper spacing around variables
- Complex formatting may need adjustment
- Headers should match common CV section names for best results
