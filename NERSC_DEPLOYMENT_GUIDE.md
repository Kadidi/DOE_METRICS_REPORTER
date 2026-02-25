# Deploying Google Docs Q&A for All NERSC Users

## 🎯 Goal
Make the natural language Q&A system available to all NERSC users so they can query Google Docs.

## 📍 Deployment Options

### Option 1: Community File System (Recommended)

Deploy to CFS where all users have read access:

```bash
# Typical NERSC shared location
/global/common/software/nersc/google-docs-qa/
```

### Option 2: Module System

Create a custom module that users can load.

### Option 3: Central Python Package

Install as a pip package in a shared environment.

---

## 🚀 Recommended Deployment (CFS)

### Step 1: Create Shared Installation Directory

```bash
# Choose installation location (check with NERSC policy)
INSTALL_DIR="/global/common/software/nersc/google-docs-qa"

# Create directory (may require admin/group permissions)
mkdir -p $INSTALL_DIR
chmod 755 $INSTALL_DIR
```

### Step 2: Copy Files

```bash
# Copy all necessary files
cp test_google_docs.py $INSTALL_DIR/
cp ask_document.py $INSTALL_DIR/
cp query_doc.py $INSTALL_DIR/
cp list_docs.py $INSTALL_DIR/
cp quick_ask.sh $INSTALL_DIR/
cp NL_QA_GUIDE.md $INSTALL_DIR/README.md

# Make scripts executable
chmod 755 $INSTALL_DIR/*.py
chmod 755 $INSTALL_DIR/*.sh

# Set appropriate permissions
chmod -R 755 $INSTALL_DIR
```

### Step 3: Create User-Friendly Wrapper

Create `/global/common/software/nersc/google-docs-qa/nersc-ask-doc`:

```bash
#!/bin/bash
# NERSC Google Docs Q&A Tool
# Usage: nersc-ask-doc <document_id> "Your question"

INSTALL_DIR="/global/common/software/nersc/google-docs-qa"

# Load required modules
module load python/3.11 2>/dev/null

# Run the tool
python $INSTALL_DIR/ask_document.py "$@"
```

### Step 4: Create Installation for Dependencies

Since users may not have the required packages:

```bash
# Create shared conda environment (if you have permission)
module load python/3.11
conda create -n google-docs-qa python=3.11
conda activate google-docs-qa
pip install google-auth-oauthlib google-api-python-client anthropic

# OR create a requirements.txt
cat > $INSTALL_DIR/requirements.txt <<EOF
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.188.0
anthropic>=0.77.0
EOF
```

### Step 5: Update User's PATH

Users add to their `~/.bashrc`:

```bash
# Google Docs Q&A Tool
export PATH="/global/common/software/nersc/google-docs-qa:$PATH"
```

---

## 📦 Option 2: Module File Deployment

### Create Module File

Location: `/global/common/software/modulefiles/google-docs-qa/1.0.lua`

```lua
-- Google Docs Q&A Tool Module
help([[
Google Docs Natural Language Q&A Tool

This module provides access to the NERSC Google Docs Q&A system.
Query your Google Docs using natural language questions.

Usage:
  nersc-ask-doc <document_id> "Your question"

Examples:
  nersc-ask-doc 1ABC...XYZ "What were the outages?"
  nersc-ask-doc 1ABC...XYZ "Summarize the incidents"

Documentation: /global/common/software/nersc/google-docs-qa/README.md
]])

whatis("Name: google-docs-qa")
whatis("Version: 1.0")
whatis("Category: tools")
whatis("Description: Natural language Q&A for Google Docs")
whatis("URL: https://docs.nersc.gov/")

local base = "/global/common/software/nersc/google-docs-qa"

prepend_path("PATH", base)
setenv("GOOGLE_DOCS_QA_HOME", base)

-- Load required Python
depends_on("python/3.11")
```

### Users Load Module

```bash
module load google-docs-qa
nersc-ask-doc <doc_id> "Your question"
```

---

## 👥 User Setup Instructions

Each user needs to do a one-time setup for authentication.

### Create User Guide

Save as `$INSTALL_DIR/USER_SETUP.md`:

````markdown
# Google Docs Q&A - User Setup Guide

## First Time Setup (5 minutes)

### Step 1: Authenticate with Google

You need to connect your Google account once:

```bash
module load python/3.11
cd ~  # Or any directory where you want to store your token
python /global/common/software/nersc/google-docs-qa/test_google_docs.py
```

This will:
1. Display a URL - open it in your browser
2. Sign in with your Google account
3. Authorize the application
4. Paste the redirect URL back

A `token.json` file will be created in your current directory.

### Step 2: Install Dependencies (If Not Using Shared Environment)

```bash
module load python/3.11
pip install --user google-auth-oauthlib google-api-python-client anthropic
```

### Step 3: Test It

```bash
nersc-ask-doc <YOUR_DOC_ID> "What is in this document?"
```

## Usage

### Basic Query
```bash
nersc-ask-doc 1ABC...XYZ "Your question here"
```

### Interactive Mode
```bash
nersc-ask-doc 1ABC...XYZ
# Then type questions interactively
```

### With AI-Powered Answers (Optional)
```bash
export ANTHROPIC_API_KEY='your-key'
nersc-ask-doc 1ABC...XYZ "Summarize the incidents"
```

## Getting Document IDs

From Google Doc URLs:
```
https://docs.google.com/document/d/1ABC123xyz/edit
                                    ^^^^^^^^^^^ This is the ID
```

## Troubleshooting

**"token.json not found"**
- Run the authentication step from the directory where you want to store your token
- Or specify token location: `export GOOGLE_APPLICATION_CREDENTIALS=/path/to/token.json`

**"Module not found"**
- Install dependencies: `pip install --user -r /global/common/software/nersc/google-docs-qa/requirements.txt`

## Documentation

Full guide: `/global/common/software/nersc/google-docs-qa/README.md`
````

---

## 🔧 Alternative: Lightweight Deployment

If you don't have admin access to shared directories:

### Option A: GitHub + User Installation

1. **Create a GitHub repository:**
   ```bash
   # Push your code to GitHub
   git init
   git add *.py *.sh *.md
   git commit -m "Initial commit"
   git remote add origin https://github.com/nersc/google-docs-qa
   git push -u origin main
   ```

2. **Users install:**
   ```bash
   git clone https://github.com/nersc/google-docs-qa
   cd google-docs-qa
   pip install --user -r requirements.txt
   ./quick_ask.sh <doc_id> "question"
   ```

### Option B: NERSC Portal/JupyterHub

Deploy as a JupyterHub extension or web service.

### Option C: User's Home Directory Template

Provide a setup script users run once:

```bash
#!/bin/bash
# setup_google_docs_qa.sh

echo "Setting up Google Docs Q&A..."

# Create local copy
mkdir -p ~/.local/bin/google-docs-qa
cd ~/.local/bin/google-docs-qa

# Download files
wget https://your-server/test_google_docs.py
wget https://your-server/ask_document.py
chmod +x *.py

# Add to PATH
echo 'export PATH="$HOME/.local/bin/google-docs-qa:$PATH"' >> ~/.bashrc

# Install dependencies
pip install --user google-auth-oauthlib google-api-python-client anthropic

echo "Setup complete! Run: source ~/.bashrc"
```

---

## 📢 Announcing to Users

### Email Template

```
Subject: New Tool: Natural Language Q&A for Google Docs

Hi NERSC Users,

We've deployed a new tool that lets you query Google Docs using natural language!

QUICK START:
  module load google-docs-qa
  nersc-ask-doc <DOCUMENT_ID> "Your question here"

FEATURES:
- Ask questions in natural language
- Get instant keyword-based answers (free)
- Optional AI-powered analysis (with API key)
- Interactive or command-line mode

SETUP (one-time):
  See: /global/common/software/nersc/google-docs-qa/USER_SETUP.md

EXAMPLES:
  nersc-ask-doc 1ABC...XYZ "What were the outages?"
  nersc-ask-doc 1ABC...XYZ "Summarize the incidents in December"

DOCUMENTATION:
  /global/common/software/nersc/google-docs-qa/README.md

Questions? Contact: support@nersc.gov
```

### NERSC Documentation Page

Add to NERSC docs site:
```
https://docs.nersc.gov/tools/google-docs-qa/
```

---

## 🔒 Security Considerations

### User Credentials
- Each user has their own `token.json` (OAuth credentials)
- Stored in user's home directory (private)
- Not shared between users

### API Keys (Optional)
- Users provide their own Anthropic API key
- Set as environment variable
- Not stored in shared location

### File Permissions
```bash
# Shared installation (read-only for users)
chmod -R 755 /global/common/software/nersc/google-docs-qa

# User token files (private)
chmod 600 ~/token.json
```

### Access Control
- Users can only access Google Docs they have permission to view
- OAuth respects Google Drive sharing settings

---

## 📊 Monitoring & Support

### Usage Tracking
```bash
# Log usage (optional)
LOG_DIR="/global/common/software/nersc/google-docs-qa/logs"
echo "$(date) $USER $*" >> $LOG_DIR/usage.log
```

### Support Documentation
Create FAQ at: `/global/common/software/nersc/google-docs-qa/FAQ.md`

---

## 🎓 Training Materials

### Tutorial Jupyter Notebook
```python
# google_docs_qa_tutorial.ipynb
"""
# Google Docs Q&A Tutorial

Learn how to query your Google Docs using natural language.
"""

# Step 1: Authentication
# Step 2: Basic queries
# Step 3: Advanced usage
# Step 4: Integration examples
```

### Video Tutorial
Record a short demo video showing:
1. Authentication
2. Basic query
3. Interactive mode
4. AI-powered analysis

---

## ✅ Deployment Checklist

- [ ] Choose installation location (CFS or module)
- [ ] Get necessary permissions
- [ ] Copy files to shared location
- [ ] Set correct file permissions (755 for dirs/scripts)
- [ ] Create requirements.txt
- [ ] Create module file (if using modules)
- [ ] Write user setup guide
- [ ] Create announcement email
- [ ] Update NERSC documentation
- [ ] Test with a few beta users
- [ ] Announce to all users
- [ ] Monitor usage and issues
- [ ] Provide ongoing support

---

## 🚦 Phased Rollout (Recommended)

### Phase 1: Beta (Week 1)
- Deploy to CFS
- Invite 5-10 beta testers
- Gather feedback
- Fix issues

### Phase 2: Limited Release (Week 2-3)
- Announce to specific groups
- Monitor usage
- Update documentation

### Phase 3: General Availability (Week 4+)
- Announce to all NERSC users
- Add to official documentation
- Provide training sessions

---

## 📞 Support Plan

### User Support Channels
1. **Documentation**: README and USER_SETUP.md
2. **Email**: support@nersc.gov
3. **Slack**: #google-docs-qa channel
4. **Office Hours**: Weekly Q&A sessions

### Common Issues & Solutions
- Authentication problems → Re-run auth flow
- API errors → Check permissions, enable APIs
- Module not found → Load python/3.11 first
- Performance issues → Use simple mode for basic queries

---

## 🔄 Maintenance

### Updates
```bash
# Update installation
cd /global/common/software/nersc/google-docs-qa
git pull  # If using git
chmod 755 *.py *.sh
```

### Version Management
```bash
# Keep multiple versions
/google-docs-qa/1.0/
/google-docs-qa/1.1/
/google-docs-qa/latest -> 1.1/
```

---

## 📝 Next Steps

1. **Contact NERSC admins** about shared directory location
2. **Request permissions** for CFS deployment
3. **Set up beta testing** with small group
4. **Create support documentation**
5. **Plan announcement** and training
6. **Deploy** using this guide

Need help? Contact NERSC support or consult:
- https://docs.nersc.gov/
- support@nersc.gov
