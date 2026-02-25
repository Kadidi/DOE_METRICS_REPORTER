# Email Announcement Template

---

**Subject:** New Tool: Query Google Docs with Natural Language at NERSC

**To:** all-users@nersc.gov

---

Hi NERSC Users,

We're excited to announce a new tool that lets you **query Google Docs using natural language questions**!

## 🚀 What It Does

Ask questions about your Google Docs and get instant answers:
- "What were the outages in December?"
- "Summarize the incidents"
- "How many maintenance windows were there?"

## ⚡ Quick Start

### One-Time Setup (5 minutes):

```bash
module load python/3.11
/global/common/software/nersc/google-docs-qa/setup_user.sh
```

### Usage:

```bash
module load python/3.11
python /global/common/software/nersc/google-docs-qa/ask_document.py <DOC_ID> "Your question"
```

**Get Document ID from URL:**
```
https://docs.google.com/document/d/1ABC123xyz/edit
                                    ^^^^^^^^^^^ This is the ID
```

## 📚 Examples

```bash
# Single question
python /global/common/software/nersc/google-docs-qa/ask_document.py \
  1ABC123xyz "What were the main issues?"

# Interactive mode
python /global/common/software/nersc/google-docs-qa/ask_document.py 1ABC123xyz

# List your Google Docs
python /global/common/software/nersc/google-docs-qa/list_docs.py
```

## ✨ Features

- ✅ **Free keyword search** - instant answers
- ✅ **AI-powered analysis** - with optional API key
- ✅ **Interactive mode** - ask multiple questions
- ✅ **Secure** - uses your Google credentials
- ✅ **Works with any Google Doc** you have access to

## 📖 Documentation

- **Installation**: `/global/common/software/nersc/google-docs-qa/README.md`
- **User Guide**: `/global/common/software/nersc/google-docs-qa/docs/NL_QA_GUIDE.md`
- **NERSC Docs**: https://docs.nersc.gov/tools/google-docs-qa/

## 💡 Advanced: AI-Powered Answers

For intelligent summaries and analysis:

1. Get a free API key: https://console.anthropic.com/
2. Set environment variable: `export ANTHROPIC_API_KEY='your-key'`
3. Ask complex questions: `"Summarize all incidents by type"`

## 🎓 Training Session

Join us for a live demo and Q&A:
- **Date**: [TBD]
- **Time**: [TBD]
- **Location**: [Zoom link or room]

## 💬 Support

- **Documentation**: `/global/common/software/nersc/google-docs-qa/`
- **Questions**: support@nersc.gov
- **Slack**: #google-docs-qa

Try it out and let us know what you think!

---

NERSC User Services Team
support@nersc.gov
