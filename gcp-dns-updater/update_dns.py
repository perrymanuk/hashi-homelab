
import os
import requests
import logging
import sys
import base64
import json
import time  # Moved import to top

# Import GCP specific libraries
from google.cloud import dns
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env_vars():
    """Reads required environment variables and returns them."""
    project_id = os.environ.get('GCP_PROJECT_ID')
    zone_name = os.environ.get('GCP_DNS_ZONE_NAME') # This will be the TLD like "demonsafe.com"
    record_name = os.environ.get('GCP_DNS_RECORD_NAME')
    key_b64 = os.environ.get('GCP_SERVICE_ACCOUNT_KEY_B64') # Changed variable name

    if not all([project_id, zone_name, record_name, key_b64]): # Check for key_b64
        missing = [var for var, val in [
            ('GCP_PROJECT_ID', project_id),
            ('GCP_DNS_ZONE_NAME', zone_name),
            ('GCP_DNS_RECORD_NAME', record_name),
            ('GCP_SERVICE_ACCOUNT_KEY_B64', key_b64) # Updated missing check
        ] if not val]
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    return project_id, zone_name, record_name, key_b64 # Return key_b64

def get_public_ip():
    """Fetches the public IPv4 address."""
    try:
        response = requests.get('https://v4.ifconfig.me/ip', timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        ip_address = response.text.strip()
        logging.info(f"Successfully fetched public IP: {ip_address}")
        return ip_address
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        sys.exit(1) # Exit if IP cannot be fetched

def get_dns_client(key_b64: str, project_id: str): # Changed key_path to key_b64 and added project_id
    """Creates and returns a DNS client authenticated with a base64 encoded service account key."""
    try:
        # Decode the base64 string
        logging.info("Decoding base64 service account key...")
        decoded_key = base64.b64decode(key_b64)
        logging.info("Base64 key decoded successfully.")

        # Parse the decoded JSON key
        logging.info("Parsing service account key JSON...")
        key_info = json.loads(decoded_key)
        logging.info("Service account key JSON parsed successfully.")

        # Create credentials from the parsed key info
        credentials = service_account.Credentials.from_service_account_info(key_info)

        # Use the provided project_id, not the one from credentials, to ensure consistency
        client = dns.Client(project=project_id, credentials=credentials)
        logging.info(f"Successfully created DNS client for project {project_id}")
        return client

    except base64.binascii.Error as e:
        logging.error(f"Failed to decode base64 service account key: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse service account key JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to create DNS client from service account info: {e}")
        sys.exit(1)

def update_dns_record(client: dns.Client, project_id: str, zone_name: str, record_name: str, ip_address: str):
    """
    Checks and updates/creates an A record for the given name in the specified zone,
    replacing a CNAME if necessary.

    Args:
        client: Authenticated DNS client.
        project_id: GCP project ID.
        zone_name: The domain TLD (e.g., "demonsafe.com"). This will be converted
                   to the GCP zone name format (e.g., "demonsafe-com").
        record_name: The specific record to update (e.g., "*.demonsafe.com").
        ip_address: The public IP address to set.
    """
    try:
        # Convert the TLD zone name (e.g., "demonsafe.com") to GCP zone name format (e.g., "demonsafe-com")
        gcp_zone_name = zone_name.replace('.', '-')
        logging.info(f"Targeting GCP DNS Zone: {gcp_zone_name}")

        zone = client.zone(gcp_zone_name, project_id)
        if not zone.exists():
            logging.error(f"DNS zone '{gcp_zone_name}' not found in project '{project_id}'.")
            return # Cannot proceed without the zone

        # Ensure record_name ends with a dot for FQDN matching
        fqdn = record_name if record_name.endswith('.') else f"{record_name}."
        logging.info(f"Checking DNS records for: {fqdn} in zone {gcp_zone_name}")

        record_sets = list(zone.list_resource_record_sets(filter_=f"name={fqdn}"))

        existing_a_record = None
        existing_cname_record = None

        for record_set in record_sets:
            if record_set.record_type == 'A' and record_set.name == fqdn:
                existing_a_record = record_set
                logging.info(f"Found existing A record: {existing_a_record.name} -> {existing_a_record.rrdatas}")
            elif record_set.record_type == 'CNAME' and record_set.name == fqdn:
                existing_cname_record = record_set
                logging.info(f"Found existing CNAME record: {existing_cname_record.name} -> {existing_cname_record.rrdatas}")

        changes = zone.changes()
        needs_update = False

        # Handle existing CNAME (delete it to replace with A)
        if existing_cname_record:
            logging.warning(f"Deleting existing CNAME record {fqdn} to replace with A record.")
            changes.delete_record_set(existing_cname_record)
            needs_update = True
            # Ensure we don't try to delete an A record if we just deleted a CNAME
            existing_a_record = None

        # Define the new A record we want
        new_a_record = zone.resource_record_set(fqdn, "A", 300, [ip_address])

        # Handle existing A record
        if existing_a_record:
            if existing_a_record.rrdatas == [ip_address]:
                logging.info(f"Existing A record {fqdn} already points to {ip_address}. No update needed.")
                return # Nothing to do
            else:
                logging.info(f"Existing A record {fqdn} points to {existing_a_record.rrdatas}. Updating to {ip_address}.")
                changes.delete_record_set(existing_a_record)
                changes.add_record_set(new_a_record)
                needs_update = True
        # Handle case where no A record (and no CNAME was found/deleted)
        elif not existing_cname_record: # Only add if we didn't already decide to replace CNAME
            logging.info(f"No existing A or CNAME record found for {fqdn}. Creating new A record pointing to {ip_address}.")
            changes.add_record_set(new_a_record)
            needs_update = True
        # Handle case where CNAME was found and deleted - we still need to add the A record
        elif existing_cname_record:
             logging.info(f"Adding A record for {fqdn} pointing to {ip_address} after CNAME deletion.")
             changes.add_record_set(new_a_record)
             # needs_update should already be True

        # Execute the changes if any were queued
        if needs_update:
            logging.info(f"Executing DNS changes for {fqdn} in zone {gcp_zone_name}...")
            changes.create()
            # Wait until the changes are finished.
            while changes.status != 'done':
                logging.info(f"Waiting for DNS changes to complete (status: {changes.status})...")
                time.sleep(5) # Wait 5 seconds before checking again
                changes.reload()
            logging.info(f"Successfully updated DNS record {fqdn} to {ip_address} in zone {gcp_zone_name}.")
        else:
            # This case should only be hit if an A record existed and was correct
            logging.info("No DNS changes were necessary.")

    except GoogleAPIError as e:
        logging.error(f"GCP API Error updating DNS record {fqdn} in zone {gcp_zone_name}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during DNS update for {fqdn} in zone {gcp_zone_name}: {e}")


if __name__ == "__main__":
    logging.info("Starting DNS update script.")
    # Update variable name received from get_env_vars
    # zone_name here is the TLD (e.g., "demonsafe.com")
    project_id, zone_name, record_name, key_b64 = get_env_vars()
    public_ip = get_public_ip()

    if public_ip:
        # Pass key_b64 and project_id to get_dns_client
        dns_client = get_dns_client(key_b64, project_id)
        if dns_client:
            # Pass the TLD zone_name here; conversion happens inside update_dns_record
            update_dns_record(dns_client, project_id, zone_name, record_name, public_ip)
            logging.info("DNS update script finished.")
        else:
            # Error handled in get_dns_client, it exits
            logging.error("Exiting due to DNS client initialization failure.")
            sys.exit(1) # Explicit exit for clarity
    else:
        # Error handled in get_public_ip, it exits
        logging.error("Exiting due to inability to fetch public IP.")
        sys.exit(1) # Explicit exit for clarity
