---
title: CyberPanel Integration
description: Managing CyberPanel servers with Cyberzard
---

# CyberPanel Integration

Cyberzard provides comprehensive integration with CyberPanel's REST API for managing websites, databases, email, DNS, SSL, and more.

## Configuration

Set environment variables for CyberPanel access:

```bash
export CYBERPANEL_HOST=https://your-server:8090
export CYBERPANEL_USER=admin
export CYBERPANEL_PASS=your-password
```

Or configure programmatically:

```python
from cyberzard.cyberpanel import CyberPanelClient

client = CyberPanelClient(
    host="https://your-server:8090",
    username="admin",
    password="your-password",
)
```

## Python API

### Website Management

```python
from cyberzard.cyberpanel import CyberPanelClient

async def manage_websites():
    client = CyberPanelClient()
    
    # List all websites
    websites = await client.list_websites()
    
    # Create a new website
    await client.create_website(
        domain="example.com",
        email="admin@example.com",
        package="Default",
        php_version="8.1",
    )
    
    # Delete a website
    await client.delete_website("old-site.com")
    
    # Suspend/unsuspend
    await client.suspend_website("problem-site.com")
    await client.unsuspend_website("problem-site.com")
```

### Database Management

```python
# List databases
databases = await client.list_databases()

# Create a database
await client.create_database(
    db_name="myapp_db",
    db_user="myapp_user",
    db_password="secure_password",
    website="example.com",
)

# Delete a database
await client.delete_database("old_db")
```

### Email Management

```python
# List email accounts
accounts = await client.list_email_accounts("example.com")

# Create email account
await client.create_email_account(
    email="user@example.com",
    password="secure_password",
)

# Create email forwarder
await client.create_email_forwarder(
    email="alias@example.com",
    destination="real@example.com",
)
```

### SSL Certificates

```python
# Issue Let's Encrypt SSL
await client.issue_ssl("example.com")

# Check SSL status
status = await client.ssl_status("example.com")
```

### DNS Management

```python
# List DNS records
records = await client.list_dns_records("example.com")

# Add DNS record
await client.add_dns_record(
    domain="example.com",
    name="www",
    record_type="A",
    value="192.168.1.1",
    ttl=3600,
)

# Delete DNS record
await client.delete_dns_record(record_id=123)
```

### Firewall (CSF)

```python
# Get firewall status
status = await client.firewall_status()

# Add firewall rule
await client.add_firewall_rule(
    ip="192.168.1.100",
    action="allow",
    comment="Trusted IP",
)

# Block an IP
await client.block_ip("10.0.0.1")

# Unblock an IP
await client.unblock_ip("10.0.0.1")
```

### Backups

```python
# Create backup
await client.create_backup("example.com")

# List backups
backups = await client.list_backups("example.com")

# Restore backup
await client.restore_backup(backup_id="backup_123")
```

## CLI Usage

Use CyberPanel features via the chat mode:

```bash
cyberzard chat
```

Example conversations:

```
You: List all websites on this server
Cyberzard: I found 3 websites...

You: Create a new website called myapp.com
Cyberzard: I'll create the website. What email should I use for the admin?

You: Check the SSL status for myapp.com
Cyberzard: The SSL certificate for myapp.com is valid until...

You: Block IP 10.0.0.50 in the firewall
Cyberzard: I've added a firewall rule to block 10.0.0.50.
```

## Available Tools

When using via MCP or the AI agent, these tools are available:

| Tool | Description |
|------|-------------|
| `cyberpanel_list_websites` | List all hosted websites |
| `cyberpanel_create_website` | Create a new website |
| `cyberpanel_delete_website` | Delete a website |
| `cyberpanel_suspend_website` | Suspend a website |
| `cyberpanel_unsuspend_website` | Unsuspend a website |
| `cyberpanel_list_databases` | List all databases |
| `cyberpanel_create_database` | Create a new database |
| `cyberpanel_delete_database` | Delete a database |
| `cyberpanel_list_email_accounts` | List email accounts |
| `cyberpanel_create_email_account` | Create email account |
| `cyberpanel_issue_ssl` | Issue/renew SSL certificate |
| `cyberpanel_list_dns_records` | List DNS records |
| `cyberpanel_add_dns_record` | Add DNS record |
| `cyberpanel_firewall_status` | Get firewall status |
| `cyberpanel_add_firewall_rule` | Add firewall rule |
| `cyberpanel_create_backup` | Create website backup |

## Error Handling

The client handles common errors gracefully:

```python
from cyberzard.cyberpanel import CyberPanelClient, CyberPanelError

try:
    await client.create_website("example.com", ...)
except CyberPanelError as e:
    print(f"CyberPanel error: {e.message}")
    print(f"Status code: {e.status_code}")
```

## Security Notes

- Store credentials securely using environment variables
- Use HTTPS for CyberPanel connections
- Consider IP whitelisting in CyberPanel settings
- Audit API usage in CyberPanel logs
