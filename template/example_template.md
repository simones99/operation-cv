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

## Scoring Impact

Different sections have varying impacts on your interview probability score:

### High Impact (Focus Areas)
- **Summary**: Key for Content Match score
- **Experience**: Major contributor to all scoring components
- **Skills**: Critical for Skill Coverage score
- **Keywords**: Affects Keyword Density score

### Medium Impact
- **Projects**: Supplements Experience score
- **Education**: Contributes to Content Match
- **Languages**: Adds to overall relevance

### Optional Impact
- Publications, Interests, Awards: Use if relevant to position

## Example Template Structure

Here's how a template optimized for scoring might be structured:

```
[YOUR NAME]
[Contact Details]

PROFESSIONAL SUMMARY
{{ summary }}

EXPERIENCE
{{ experience }}

SKILLS & CERTIFICATIONS 
{{ skills }}

EDUCATION
{{ education }}

LANGUAGES
{{ languages }}

[Additional sections as needed...]
```

## Best Practices for High Scores

1. **Summary Section**
   - Place early in CV
   - Include key industry terms
   - Match job description tone

2. **Experience Section**
   - Use action verbs
   - Include measurable achievements
   - Mirror job description terminology

3. **Skills Section**
   - Group by category
   - List most relevant first
   - Include proficiency levels

4. **Format Guidelines**
   - Keep styling minimal
   - Use consistent spacing
   - Maintain clear section headers

## Technical Requirements

1. Create your template in DOCX format
2. Use exact variable names with double curly braces
3. Include all required sections for scoring:
   - summary
   - experience
   - skills
   - education

## Optimization Tips

1. **For Content Match (50%)**
   - Strong professional summary
   - Detailed experience descriptions
   - Relevant projects and achievements

2. **For Skill Coverage (30%)**
   - Comprehensive skills section
   - Skills mentioned in context
   - Technical and soft skills

3. **For Keyword Density (20%)**
   - Natural keyword placement
   - Industry-specific terminology
   - Consistent skill references
