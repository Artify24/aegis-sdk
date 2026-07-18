import os
import json
import smtplib
import imaplib
import email
from email.message import EmailMessage
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from github import Github
from supabase import create_client, Client
from datetime import datetime

# ==============================================================================
# GITHUB TOOLS
# ==============================================================================

def get_github_client() -> Github:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return Github(token)

@tool
def github_read_repos() -> str:
    """Read all repositories accessible by the authenticated user."""
    try:
        g = get_github_client()
        repos = [repo.full_name for repo in g.get_user().get_repos()]
        return json.dumps({"status": "success", "repositories": repos})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def github_read_issues(repo_name: str, state: str = "open") -> str:
    """Read issues from a specific GitHub repository. State can be 'open' or 'closed'."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        issues = []
        for issue in repo.get_issues(state=state)[:10]:
            if not issue.pull_request:
                issues.append({
                    "id": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "url": issue.html_url
                })
        return json.dumps({"status": "success", "issues": issues})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def github_read_prs(repo_name: str, state: str = "open") -> str:
    """Read pull requests from a specific GitHub repository."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        prs = []
        for pr in repo.get_pulls(state=state)[:10]:
            prs.append({
                "id": pr.number,
                "title": pr.title,
                "state": pr.state,
                "url": pr.html_url
            })
        return json.dumps({"status": "success", "pull_requests": prs})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def github_create_issue(repo_name: str, title: str, body: str) -> str:
    """Create a new issue in a GitHub repository."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body)
        return json.dumps({"status": "success", "issue_url": issue.html_url})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def github_search_commits(repo_name: str, query: str) -> str:
    """Search commits in a GitHub repository. Query can be an author name or keyword."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        commits = repo.get_commits()
        results = []
        for c in commits[:20]:
            if query.lower() in c.commit.message.lower() or (c.commit.author and query.lower() in c.commit.author.name.lower()):
                results.append({
                    "sha": c.sha,
                    "message": c.commit.message,
                    "author": c.commit.author.name if c.commit.author else "Unknown"
                })
        return json.dumps({"status": "success", "commits": results})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

# ==============================================================================
# EMAIL TOOLS (IMAP/SMTP)
# ==============================================================================

def get_email_creds():
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")
    imap_server = os.environ.get("IMAP_SERVER", "imap.gmail.com")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    if not user or not password:
        raise ValueError("EMAIL_USER and EMAIL_PASSWORD must be set in .env")
    return user, password, imap_server, smtp_server

@tool
def email_read_inbox(limit: int = 5) -> str:
    """Read the latest emails from the inbox."""
    try:
        user, password, imap_server, _ = get_email_creds()
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(user, password)
        mail.select("inbox")
        
        _, search_data = mail.search(None, "ALL")
        mail_ids = search_data[0].split()
        
        emails = []
        for i in mail_ids[-limit:]:
            _, data = mail.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            
            # Simple payload extraction
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')

            emails.append({
                "id": i.decode(),
                "subject": msg["subject"],
                "from": msg["from"],
                "date": msg["date"],
                "snippet": body[:200] + "..." if len(body) > 200 else body
            })
        mail.logout()
        return json.dumps({"status": "success", "emails": emails})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def email_send(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    try:
        user, password, _, smtp_server = get_email_creds()
        
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to
        
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return json.dumps({"status": "success", "message": f"Email sent to {to}"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def email_reply(to: str, subject: str, body: str, in_reply_to: str) -> str:
    """Reply to a specific email by providing the original Message-ID in 'in_reply_to'."""
    try:
        user, password, _, smtp_server = get_email_creds()
        
        msg = EmailMessage()
        msg.set_content(body)
        if not subject.startswith("Re:"):
            subject = "Re: " + subject
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = to
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = in_reply_to
        
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        return json.dumps({"status": "success", "message": f"Reply sent to {to}"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

# ==============================================================================
# DATABASE TOOLS (SUPABASE)
# ==============================================================================

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables not set in .env")
    return create_client(url, key)

@tool
def db_query(table: str, match_column: str = None, match_value: str = None, limit: int = 100) -> str:
    """Query data from a Supabase table. Optionally filter by a column/value match."""
    try:
        sb = get_supabase_client()
        query = sb.table(table).select("*").limit(limit)
        if match_column and match_value:
            # Use ilike for case-insensitive matching just in case the LLM capitalizes it
            query = query.ilike(match_column, f"{match_value}")
            
        res = query.execute()
        
        # Log to terminal for debugging
        print(f"--- DB QUERY DEBUG ---")
        print(f"Table: {table}, Column: {match_column}, Value: {match_value}")
        print(f"Results returned: {len(res.data)}")
        print(f"----------------------")
        
        return json.dumps({"status": "success", "data": res.data})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def db_insert(table: str, data_json: str) -> str:
    """Insert data into a Supabase table. data_json must be a JSON string of a dictionary."""
    try:
        sb = get_supabase_client()
        data_dict = json.loads(data_json)
        res = sb.table(table).insert(data_dict).execute()
        return json.dumps({"status": "success", "inserted": res.data})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def db_update(table: str, match_column: str, match_value: str, updates_json: str) -> str:
    """Update rows in a Supabase table matching the column/value. updates_json is a JSON string of new values."""
    try:
        sb = get_supabase_client()
        updates_dict = json.loads(updates_json)
        res = sb.table(table).update(updates_dict).eq(match_column, match_value).execute()
        return json.dumps({"status": "success", "updated": res.data})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def db_backup_table(table: str) -> str:
    """Backup a Supabase table by reading all its rows into a JSON structure."""
    try:
        sb = get_supabase_client()
        res = sb.table(table).select("*").execute()
        backup_data = res.data
        return json.dumps({
            "status": "success", 
            "backup_summary": f"Backed up {len(backup_data)} rows from {table}",
            "data": backup_data
        })
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

@tool
def db_restore_table(table: str, backup_json: str) -> str:
    """Restore a Supabase table from a backup JSON string containing an array of row objects."""
    try:
        sb = get_supabase_client()
        rows = json.loads(backup_json)
        # Upsert helps prevent conflicts on existing primary keys
        res = sb.table(table).upsert(rows).execute()
        return json.dumps({"status": "success", "restored_rows": len(res.data)})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
