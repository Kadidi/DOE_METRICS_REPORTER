cd ~/MAGENT
git switch mayur/agent-updates
git status
git add .
git commit -m "your message"
git push


# GitHub SSH and Branch Workflow Cheat Sheet

Use this guide when working from Perlmutter or another remote machine.

## 1. Login to Perlmutter

Run this from your local terminal.

```bash
ssh username@perlmutter.nersc.gov
```

Go to your home directory.

```bash
cd ~
```

## 2. Set Git name and email

Run this one time on the machine.

```bash
git config --global user.name "username"
git config --global user.email "your_github_email@example.com"
```

Check the saved settings.

```bash
git config --global --list
```

## 3. Check whether an SSH key already exists

```bash
ls -al ~/.ssh
```

Look for these files.

```text
id_ed25519
id_ed25519.pub
```

The `.pub` file is the public key. This is the only key you copy to GitHub.

Never share this file.

```text
id_ed25519
```

## 4. Create an SSH key

Run this only if the key does not already exist.

```bash
ssh-keygen -t ed25519 -C "your_github_email@example.com"
```

When it asks this:

```text
Enter file in which to save the key (/global/homes/m/maddy/.ssh/id_ed25519):
```

Press Enter.

When it asks this:

```text
Enter passphrase (empty for no passphrase):
```

Press Enter, or enter a passphrase.

When it asks this:

```text
Enter same passphrase again:
```

Press Enter again.

## 5. Print the public key

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the full output.

Do not run or share this private key command.

```bash
cat ~/.ssh/id_ed25519
```

## 6. Add the SSH key to GitHub

In your browser, go to:

```text
GitHub → Settings → SSH and GPG keys → New SSH key
```

Suggested title:

```text
Perlmutter NERSC
```

Paste the output from:

```bash
cat ~/.ssh/id_ed25519.pub
```

Then save it.

## 7. Test GitHub SSH access

```bash
ssh -T git@github.com
```

The first time, GitHub may ask:

```text
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type:

```text
yes
```

A successful result should look like this:

```text
Hi <github-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

## 8. Clone the repository using SSH

```bash
cd ~
git clone repo dest
cd ~/dest
```

Check that this is a Git repository.

```bash
git status
git remote -v
```

The remote should look like this.

```text
git@github.com:Kadidi/DOE_METRICS_REPORTER.git
```

## 9. Create your branch

Run this only one time when creating the branch.

```bash
git switch -c new beanch
```

Check the current branch.

```bash
git branch --show-current
```

Expected output:

```text
mayur/agent-updates
```

## 10. Commit and push your branch for the first time

After editing files:

```bash
git status
git add .
git commit -m "Update agent code"
git push -u origin new branch
```

The `-u` is needed only the first time. It connects your local branch to the GitHub branch.

## 11. Regular workflow after the branch already exists



After making code changes:

```bash
git add .
git commit -m "Write your message here"
git push
```

## 12. Useful check commands

Check current branch:

```bash
git branch --show-current
```

Check changed files:

```bash
git status
```

Check recent commits:

```bash
git log --oneline -5
```

Check remote repo:

```bash
git remote -v
```

Check all branches:

```bash
git branch -a
```

## 13. If you get “not a git repository”

Do not run `git init`.

Check the folder contents.

```bash
ls -la
```

If there is no `.git` folder, then the folder is not a cloned Git repository.

Save your current folder first.

```bash
cd ~
mv MAGENT MAGENT_updated_backup
```

Clone the real repository.



Copy your updated files into the real cloned repository.

```bash
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' ~/MAGENT_updated_backup/ ~/MAGENT/
```

Then commit and push.

```bash
git status
git add .
git commit -m "Update agent code"
git push -u origin branch
```

## 14. Commands to avoid

Do not push to main.

```bash
git push origin main
```

Do not create the same branch again.

```bash
git switch -c branch
```

Use this instead after the branch already exists.

```bash
git switch branch
```

## 15. Create a Pull Request

Open this repo in your browser.

```text
https://github.com/Kadidi/DOE_METRICS_REPORTER
```

Create a Pull Request from:

```text
branch-updates → main
```

## 16. Quick daily command set

Use this when you simply want to continue working on your branch.



After editing files:

```bash
git add .
git commit -m "Your commit message"
git push
```
