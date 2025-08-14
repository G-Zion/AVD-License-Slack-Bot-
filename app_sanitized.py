from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureNamedKeyCredential
from rapidfuzz import fuzz, process

# ---------- CONFIG ----------
KEY_VAULT_NAME = "<YOUR_KEY_VAULT_NAME>"
ACCOUNT_NAME = "<YOUR_STORAGE_ACCOUNT_NAME>"
TABLE_NAME = "<YOUR_TABLE_NAME>"
UTILITY_COL = "Utility"
USED_COL = "ActiveUsers"
TOTAL_COL = "PurchasedLicenses"
FUZZY_THRESHOLD = 70  # similarity score threshold
# Acronym map — keys must be lowercase
ACRONYM_MAP = {
    "<YOUR_ACRONYM>": "<FULL_NAME>",
    "<ANOTHER_ACRONYM>": "<ANOTHER_FULL_NAME>"
}
# ----------------------------

# Connect to Key Vault
KVUri = f"https://{KEY_VAULT_NAME}.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)

# Fetch secrets from Key Vault
SLACK_BOT_TOKEN = client.get_secret("<SLACK_BOT_USER_TOKEN_SECRET_NAME>").value     
SLACK_APP_TOKEN = client.get_secret("<SLACK_APP_LEVEL_TOKEN_SECRET_NAME>").value    
STORAGE_KEY = client.get_secret("<AZURE_STORAGE_ACCESS_KEY_SECRET_NAME>").value.strip()

# Create Azure Tables client with proper credential type
table_credential = AzureNamedKeyCredential(ACCOUNT_NAME, STORAGE_KEY)
table_service = TableServiceClient(
    endpoint=f"https://{ACCOUNT_NAME}.table.core.windows.net",
    credential=table_credential
)
table_client = table_service.get_table_client(table_name=TABLE_NAME)

# Function to look up license usage with acronym + fuzzy match
def get_license_usage(utility_name: str):
    # Expand acronyms if matched
    normalized_input = utility_name.strip().lower()
    if normalized_input in ACRONYM_MAP:
        utility_name = ACRONYM_MAP[normalized_input]

    entities = list(table_client.list_entities())
    utility_list = [entity[UTILITY_COL] for entity in entities]

    # Exact match (case-insensitive)
    for entity in entities:
        if entity[UTILITY_COL].strip().lower() == utility_name.strip().lower():
            return entity[UTILITY_COL], entity[USED_COL], entity[TOTAL_COL]

    # Fuzzy match if no exact match
    match = process.extractOne(
        utility_name,
        utility_list,
        scorer=fuzz.WRatio
    )
    if match and match[1] >= FUZZY_THRESHOLD:
        matched_name = match[0]
        for entity in entities:
            if entity[UTILITY_COL] == matched_name:
                return entity[UTILITY_COL], entity[USED_COL], entity[TOTAL_COL]

    # No match found
    return None, None, None

# Slack app setup
app = App(token=SLACK_BOT_TOKEN)

@app.command("/availablelicenses")
def available_licenses(ack, respond, command):
    ack()
    util = (command.get("text") or "").strip()

    if not util:
        respond("Usage: `/availablelicenses <UTILITY NAME>`")
        return

    matched_name, used, total = get_license_usage(util)

    if matched_name is None:
        respond(f"I couldn’t find **{util}** in the license table.")
    else:
        respond(f"*{matched_name}* is using *{used}* of *{total}* AVD Licenses.")

if __name__ == "__main__":
    print("Starting Slack bot in Socket Mode...")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()

