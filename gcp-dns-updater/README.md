# GCP Dynamic DNS Updater Service

This service periodically checks the public IPv4 address of the node it's running on and updates a specified A record in a Google Cloud DNS managed zone. It's designed to run as a Nomad job within the Hashi-Homelab environment.

## Features

*   Fetches the current public IPv4 address from `https://v4.ifconfig.co/ip`.
*   Uses the `google-cloud-dns` Python SDK to interact with Google Cloud DNS.
*   Authenticates using a GCP Service Account key provided via an environment variable.
*   Checks the specified DNS record:
    *   If it's a CNAME, it deletes the CNAME record.
    *   If it's an A record, it updates the IP address if it has changed.
    *   If it doesn't exist (or after deleting a CNAME), it creates the A record with the specified TTL.
*   Runs periodically via a Nomad job.

## Prerequisites

1.  **GCP Service Account:** You need a Google Cloud Platform service account with the necessary permissions to manage DNS records.
    *   Go to the GCP Console -> IAM & Admin -> Service Accounts.
    *   Create a new service account (e.g., `gcp-dns-updater-sa`).
    *   Grant this service account the `DNS Administrator` role (`roles/dns.admin`) on the project containing your managed zone.
    *   Create a JSON key file for this service account and download it securely. You will need the *contents* of this file, not the file itself on the Nomad clients.
2.  **Nomad Environment:** A running Nomad cluster where this job can be scheduled.

## Configuration

The service is configured via environment variables passed to the Nomad task:

*   `GCP_DNS_ZONE_NAME`: The name of the managed zone in GCP DNS (e.g., `demonsafe-com`). The script derives the Project ID from the credentials.
*   `GCP_DNS_RECORD_NAME`: The DNS record name to update (e.g., `*.demonsafe.com`). **Note:** The script expects the base name; the trailing dot is handled internally if needed by the SDK.
*   `RECORD_TTL`: (Optional) The Time-To-Live (in seconds) for the created/updated A record. Defaults to 300 if not set.
*   `GCP_SERVICE_ACCOUNT_KEY_B64`: **Required.** The base64-encoded *content* of the GCP service account JSON key file.

**Generating the Base64 Key:**

You need to encode the *content* of your downloaded JSON key file into a single-line base64 string.

On Linux/macOS, you can use:
```bash
base64 -w 0 < /path/to/your/gcp_key.json
```
*(Ensure you use `-w 0` or an equivalent flag for your `base64` command to prevent line wrapping)*

Copy the resulting string.

**Setting the Environment Variable:**

These variables need to be set within the `env` block of the `nomad.job` file.

```hcl
# Example within nomad.job task config
env {
  GCP_DNS_ZONE_NAME         = "your-zone-name"      # e.g., demonsafe-com
  GCP_DNS_RECORD_NAME       = "your.record.name"    # e.g., *.demonsafe.com
  RECORD_TTL                = "300"                 # Optional, defaults to 300
  # GCP_SERVICE_ACCOUNT_KEY_B64 = "PASTE_YOUR_BASE64_ENCODED_KEY_HERE" # Set via Nomad vars/secrets
}
```

**Important:** For production use, the `GCP_SERVICE_ACCOUNT_KEY_B64` value **must** be provided securely using Nomad variables or Vault integration, not hardcoded directly in the job file. The `nomad.job` file contains a placeholder that should be populated during deployment.

## Deployment

Assuming the main project `Makefile` is updated or you deploy manually:

1.  **Ensure Prerequisites:** Verify the service account is created and you have generated the base64 encoded key string.
2.  **Configure Job:** Edit `gcp-dns-updater/nomad.job`:
    *   Update the placeholder values in the `env` block for `GCP_DNS_ZONE_NAME`, `GCP_DNS_RECORD_NAME`, and optionally `RECORD_TTL`.
    *   **Do not** hardcode the base64 key in the file. Ensure your deployment process (e.g., using `nomad job run -var ...` or CI/CD pipeline) supplies the `GCP_SERVICE_ACCOUNT_KEY_B64` variable.
3.  **Deploy:**
    *   If a `make deploy-gcp-dns-updater` target exists in the root `Makefile` (ensure it handles variable injection):
        ```bash
        # Example assuming make target uses environment variables or prompts
        export TF_VAR_gcp_service_account_key_b64="YOUR_B64_KEY" # Or however the Makefile expects it
        make deploy-gcp-dns-updater
        ```
    *   Otherwise, deploy manually using the Nomad CLI, providing the variable (ensure you are in the repository root or adjust paths):
        ```bash
        # Example using -var flag
        nomad job run -var "gcp_service_account_key_b64=YOUR_B64_KEY" gcp-dns-updater/nomad.job

        # Example using -var-file flag
        # Create a file e.g., gcp-dns-updater.vars.hcl
        # gcp_service_account_key_b64 = "YOUR_B64_KEY"
        nomad job run -var-file=gcp-dns-updater.vars.hcl gcp-dns-updater/nomad.job
        ```

## Files

*   `update_dns.py`: The core Python script for updating DNS.
*   `requirements.txt`: Python dependencies.
*   `nomad.job`: Nomad job definition for periodic execution.
*   `README.md`: This documentation file.
