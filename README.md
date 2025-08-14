AVD License Slack Bot – Technical Reference

## Overview
The **AVD License Slack Bot** provides an internal `/availablelicenses` command in Slack to query Azure Table Storage and return current AVD license usage for a given utility.  
Results are **ephemeral** — only the requesting user sees them.

---

## Functionality

### Command

```/availablelicenses <UTILITY NAME>```

### Features
- **Exact match** (case-insensitive) search on utility name.
- **Acronym support**:
- **Fuzzy matching** for misspellings and partial matches (similarity threshold 70%).
- **Key Vault integration** for secure storage of credentials.
- **Azure Table Storage query** for real-time license data.
- **Ephemeral responses** to keep results private.

---

## How It Works

1. **Slack Command Trigger**
   - User types `/availablelicenses <utility name>` in Slack.
   - Slack sends request to the bot’s Socket Mode listener.

2. **Input Processing**
   - Expands acronyms if input matches `ACRONYM_MAP`.
   - Attempts exact match against `Utility` column in the table.
   - If no match, performs fuzzy match (`WRatio` scoring, threshold 70%).

3. **Data Retrieval**
   - Bot queries `ADActiveUsersTable` via Azure Table Storage SDK using the access key from Key Vault.

4. **Response**
   - If a match is found, bot returns the license usage.
   - If no match, bot notifies the user.
   - Response is **ephemeral**.

---

## Security Considerations

- No credentials are hardcoded — all tokens and keys are pulled at runtime from Azure Key Vault using `DefaultAzureCredential`.
- Access is restricted to authorized identities via Azure RBAC and Key Vault policies.
- Slack bot only responds to authenticated `/availablelicenses` commands from users in the workspace.

---

## Dependencies

**Python Packages**
- `slack_bolt`
- `azure-identity`
- `azure-keyvault-secrets`
- `azure-data-tables`
- `rapidfuzz`
