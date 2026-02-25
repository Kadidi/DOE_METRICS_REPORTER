# Google Docs Q&A - Quick Reference Card

## 🎯 One-Time Setup

```bash
module load python/3.11
/global/common/software/nersc/google-docs-qa/setup_user.sh
```

## 💻 Basic Usage

```bash
module load python/3.11

# Single question
python /global/common/software/nersc/google-docs-qa/ask_document.py \
  <DOC_ID> "Your question"

# Interactive mode
python /global/common/software/nersc/google-docs-qa/ask_document.py <DOC_ID>

# List your docs
python /global/common/software/nersc/google-docs-qa/list_docs.py
```

## 🔑 Get Document ID

From Google Docs URL:
```
https://docs.google.com/document/d/1ABC123xyz/edit
                                    ^^^^^^^^^^^ = Document ID
```

## 📝 Example Questions

```bash
DOC_ID="1rus_ZvsEctYG0dRSq7vePU6lD72OrnOtc-WWfiMyuX8"

# Timeline questions
python ask_document.py $DOC_ID "What happened on December 15?"

# Search questions
python ask_document.py $DOC_ID "What issues with login nodes?"

# Counting questions (better with AI)
export ANTHROPIC_API_KEY='your-key'
python ask_document.py $DOC_ID "How many outages were there?"

# Summary questions (AI only)
python ask_document.py $DOC_ID "Summarize the incidents"
```

## 🤖 AI-Powered Mode (Optional)

```bash
# Get API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY='sk-ant-...'

# Add to ~/.bashrc to persist:
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "token.json not found" | Run setup script again |
| "Module not found" | `module load python/3.11` |
| "API not enabled" | Enable Google Docs API in Google Cloud Console |
| "Permission denied" | Check you have access to the document |

## 📖 Documentation

```bash
# View README
cat /global/common/software/nersc/google-docs-qa/README.md

# User guide
less /global/common/software/nersc/google-docs-qa/docs/NL_QA_GUIDE.md
```

## 🔗 Links

- **Setup**: `/global/common/software/nersc/google-docs-qa/setup_user.sh`
- **Docs**: `/global/common/software/nersc/google-docs-qa/docs/`
- **Support**: support@nersc.gov
- **NERSC Docs**: https://docs.nersc.gov/tools/google-docs-qa/

---

**Print this card and keep it handy!**
