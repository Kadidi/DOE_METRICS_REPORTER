# 🚀 How to Make This Available to All NERSC Users

## TL;DR - Quick Deploy

```bash
# Option 1: If you have admin access
./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa

# Option 2: If you need approval first
# Email DEPLOYMENT_SUMMARY.md to support@nersc.gov
# Then run the command above once approved
```

---

## 📦 What You Have

✅ **Complete working system** for natural language Q&A on Google Docs
✅ **Automated deployment script** - one command to deploy
✅ **All documentation** - for users and admins
✅ **Support materials** - email templates, quick reference
✅ **User setup automation** - makes onboarding easy

---

## 🎯 Three Deployment Options

### Option 1: Shared NERSC Installation (Recommended)

**Best for:** Making it available to all NERSC users

**Steps:**
1. Contact NERSC support for shared directory:
   ```bash
   # Email support@nersc.gov requesting:
   # - Directory: /global/common/software/nersc/google-docs-qa
   # - Purpose: Natural language Q&A tool for Google Docs
   ```

2. Once approved, deploy:
   ```bash
   ./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa
   ```

3. Announce to users:
   ```bash
   # Use USER_ANNOUNCEMENT.md as email template
   cat USER_ANNOUNCEMENT.md
   ```

**Users will run:**
```bash
module load python/3.11
/global/common/software/nersc/google-docs-qa/setup_user.sh  # One-time
python /global/common/software/nersc/google-docs-qa/ask_document.py <DOC_ID> "question"
```

---

### Option 2: Module System

**Best for:** Integration with NERSC's module system

**Steps:**
1. Deploy files as in Option 1
2. Create module file at:
   ```
   /global/common/software/modulefiles/google-docs-qa/1.0.lua
   ```
   (See NERSC_DEPLOYMENT_GUIDE.md for template)

**Users will run:**
```bash
module load google-docs-qa
nersc-ask-doc <DOC_ID> "question"
```

---

### Option 3: GitHub + User Installation

**Best for:** Quick sharing without admin access

**Steps:**
1. Create GitHub repo (public or private):
   ```bash
   git init
   git add *.py *.sh *.md requirements.txt
   git commit -m "Initial commit"
   git remote add origin https://github.com/nersc/google-docs-qa
   git push -u origin main
   ```

2. Share installation instructions:
   ```bash
   git clone https://github.com/nersc/google-docs-qa
   cd google-docs-qa
   pip install --user -r requirements.txt
   ./test_google_docs.py  # One-time auth
   ./quick_ask.sh <DOC_ID> "question"
   ```

**Users install in their home directory**

---

## 📋 Deployment Checklist

### Before Deploying

- [x] ✅ Code tested and working (you did this!)
- [ ] Contact NERSC support for approval
- [ ] Decide on deployment location
- [ ] Review security/privacy implications
- [ ] Plan announcement strategy

### During Deployment

- [ ] Run `./deploy_to_nersc.sh <location>`
- [ ] Verify files are accessible (test as different user)
- [ ] Test setup script works
- [ ] Update NERSC documentation site
- [ ] Create module file (if using modules)

### After Deployment

- [ ] Send announcement email (use USER_ANNOUNCEMENT.md)
- [ ] Monitor support requests
- [ ] Update FAQ based on questions
- [ ] Gather user feedback
- [ ] Plan training session (optional)

---

## 📧 Email Templates

### To NERSC Support (Request Deployment)

```
Subject: Request for Shared Directory - Google Docs Q&A Tool

Hi NERSC Support Team,

I'd like to deploy a new tool that allows NERSC users to query Google Docs
using natural language questions.

Request:
  - Directory: /global/common/software/nersc/google-docs-qa
  - Permissions: 755 (world-readable, my group writes)
  - Purpose: Natural language Q&A for Google Docs
  - Users: All NERSC users

The tool is ready to deploy and includes:
  - Complete documentation
  - Automated setup scripts
  - User guides and examples

Documentation attached: DEPLOYMENT_SUMMARY.md

Can you create this directory or advise on the deployment process?

Thanks!
[Your name]
```

### To All Users (After Deployment)

```
Use the template in: USER_ANNOUNCEMENT.md
```

---

## 🎓 What Users Will Experience

### First Time (5 minutes)

1. Run setup script:
   ```bash
   module load python/3.11
   /global/common/software/nersc/google-docs-qa/setup_user.sh
   ```

2. Authenticate with Google (one-time):
   - Opens browser
   - Sign in to Google
   - Authorize app
   - Done!

### Daily Use (< 1 minute)

```bash
module load python/3.11
python /global/common/software/nersc/google-docs-qa/ask_document.py \
  <DOC_ID> "What were the main issues?"
```

---

## 📊 File Overview

### Core Files (Deploy These)
```
test_google_docs.py          - Google Docs API integration
ask_document.py              - Main Q&A engine ⭐
query_doc.py                 - Direct queries
list_docs.py                 - List documents
requirements.txt             - Python dependencies
```

### User Documentation (Deploy These)
```
README.md                    - Main user guide
NL_QA_GUIDE.md              - Comprehensive guide
QUICK_REFERENCE.md          - Quick reference card
```

### Setup Automation (Deploy These)
```
setup_user.sh               - Automated user setup
quick_ask.sh                - Convenience wrapper
```

### Deployment Tools (For You)
```
deploy_to_nersc.sh          - Automated deployment ⭐
NERSC_DEPLOYMENT_GUIDE.md   - Detailed deployment guide
DEPLOYMENT_SUMMARY.md       - Overview of options
USER_ANNOUNCEMENT.md        - Email template
```

---

## 🚦 Deployment Timeline

### Week 1: Preparation
- Day 1: Request shared directory from NERSC
- Day 2-3: Wait for approval
- Day 4: Test deployment in your directory
- Day 5: Review documentation

### Week 2: Beta Testing
- Day 1: Deploy to shared location
- Day 2: Invite 5-10 beta testers
- Day 3-5: Gather feedback, fix issues
- Day 6-7: Update documentation

### Week 3: General Release
- Day 1: Final testing
- Day 2: Send announcement email
- Day 3: Update NERSC docs
- Day 4-7: Support users, answer questions

### Ongoing
- Monitor usage
- Update based on feedback
- Keep dependencies current

---

## 💡 Pro Tips

1. **Start with beta testers** - Don't announce to everyone immediately
2. **Prepare FAQ** - Most common questions will be about authentication
3. **Create video** - Short demo video helps a lot
4. **Office hours** - Consider weekly drop-in sessions first month
5. **Gather feedback** - Users will suggest improvements

---

## 🆘 Common Issues & Solutions

### "I don't have admin access"
→ Use Option 3 (GitHub) or contact NERSC support

### "Users are confused by setup"
→ Offer training session or create video tutorial

### "Too many support requests"
→ Update FAQ, improve documentation

### "Authentication failing"
→ Users need to enable Google Docs API in their Google Cloud Console

---

## ✅ You're Ready!

Everything is prepared for deployment:

**Simplest path:**
1. Email support@nersc.gov (use template above)
2. Wait for shared directory
3. Run `./deploy_to_nersc.sh /global/common/software/nersc/google-docs-qa`
4. Send announcement (use USER_ANNOUNCEMENT.md)
5. Done! 🎉

**Test deployment first:**
```bash
# Deploy to your directory first to test
./deploy_to_nersc.sh ~/test-deployment
cd ~/test-deployment
cat README.md
```

---

## 📞 Need Help?

- **Deployment questions**: See NERSC_DEPLOYMENT_GUIDE.md
- **User documentation**: See NL_QA_GUIDE.md
- **NERSC support**: support@nersc.gov
- **Test it works**: `./quick_ask.sh <doc_id> "test"`

**You have everything you need to deploy this to all NERSC users!** 🚀
