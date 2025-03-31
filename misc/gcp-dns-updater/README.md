# GCP Dynamic DNS Updater Service

This service periodically checks the public IPv4 address of the node it's running on and updates a specified A record in a Google Cloud DNS managed zone. It's designed to run as a Nomad job within the Hashi-Homelab environment, utilizing a **pre-built Docker image**.

## Features

*   Fetches the current public IPv4 address from `https://v4.ifconfig.co/ip`.
*   Uses the `google-cloud-dns` Python SDK to interact with Google Cloud DNS.
*   Authenticates using a GCP Service Account key provided via an environment variable.
*   Checks the specified DNS record:
    *   If it's a CNAME, it deletes the CNAME record.
    *   If it's an A record, it updates the IP address if it has changed.
    *   If it doesn't exist (or after deleting a CNAME), it creates the A record with the specified TTL.
*   Runs periodically via a Nomad job, executing the Python script within the pre-built Docker container.

## Prerequisites

1.  **Docker:** Docker must be installed locally to build the service image.
2.  **GCP Service Account:** You need a Google Cloud Platform service account with the necessary permissions to manage DNS records.
    *   Go to the GCP Console -> IAM & Admin -> Service Accounts.
    *   Create a new service account (e.g., `gcp-dns-updater-sa`).
    *   Grant this service account the `DNS Administrator` role (`roles/dns.admin`) on the project containing your managed zone.
    *   Create a JSON key file for this service account and download it securely. You will need the *contents* of this file, not the file itself.
3.  **Nomad Environment:** A running Nomad cluster where this job can be scheduled. The Nomad clients must have Docker installed and configured.

## Configuration

The service is configured via environment variables passed to the Nomad task, which are then consumed by the `update_dns.py` script running inside the Docker container:

*   `GCP_DNS_ZONE_NAME`: The name of the managed zone in GCP DNS (e.g., `demonsafe-com`). The script derives the Project ID from the credentials.
*   `GCP_DNS_RECORD_NAME`: The DNS record name to update (e.g., `*.demonsafe.com`). **Note:** The script expects the base name; the trailing dot is handled internally if needed by the SDK.
*   `RECORD_TTL`: (Optional) The Time-To-Live (in seconds) for the created/updated A record. Defaults to 300 if not set.
*   `GCP_PROJECT_ID`: The Google Cloud Project ID containing the DNS zone.
*   `GCP_SERVICE_ACCOUNT_KEY_B64`: **Required.** The base64-encoded *content* of the GCP service account JSON key file.

**Generating the Base64 Key:**

You need to encode the *content* of your downloaded JSON key file into a single-line base64 string.

On Linux/macOS, you can use:
```bash
base64 -w 0 < /path/to/your/gcp_key.json
```
*(Ensure you use `-w 0` or an equivalent flag for your `base64` command to prevent line wrapping)*

Copy the resulting string.

**Setting Environment Variables in Nomad:**

These variables are defined within the `env` block of the `nomad.job` file using Go templating to read runtime environment variables provided by the Nomad agent (which in turn are often sourced from the deployment mechanism, like GitHub Actions):

```hcl
# Example within nomad.job task config
env {
  GCP_DNS_ZONE_NAME = <<EOH
{{ env "NOMAD_VAR_tld" | replace "." "-" }}
EOH
  GCP_DNS_RECORD_NAME = <<EOH
*.{{ env "NOMAD_VAR_tld" }}
EOH
  GCP_SERVICE_ACCOUNT_KEY_B64 = <<EOH
{{ env "NOMAD_VAR_gcp_dns_admin" }}
EOH
  GCP_PROJECT_ID = <<EOH
{{ env "NOMAD_VAR_gcp_project_id" }}
EOH
  # RECORD_TTL = "300" # Optional, defaults to 300 in the script
}
```

**Important:** The actual values for `NOMAD_VAR_tld`, `NOMAD_VAR_gcp_dns_admin`, and `NOMAD_VAR_gcp_project_id` **must** be provided securely to the Nomad agent's environment during deployment (e.g., via GitHub Actions secrets mapped in the workflow, or using Vault integration), not hardcoded directly in the job file.

## Deployment

1.  **Ensure Prerequisites:** Verify the service account is created, you have the base64 encoded key, and Docker is running.
2.  **Build the Docker Image:** From the root of the `hashi-homelab` repository, run the make target:
    ```bash
    make build-gcp-dns-updater
    ```
    This builds the required Docker image tagged `gcp-dns-updater:latest` using the `gcp-dns-updater/Dockerfile`.
3.  **Deploy the Nomad Job:**
    *   Ensure the required environment variables (`NOMAD_VAR_tld`, `NOMAD_VAR_gcp_dns_admin`, `NOMAD_VAR_gcp_project_id`) are available to the Nomad agent running the job. This is typically handled by the CI/CD pipeline (like the GitHub Actions workflow in this repo) or Vault integration.
    *   Deploy using the Nomad CLI (ensure you are in the repository root or adjust paths). This job will use the `gcp-dns-updater:latest` image built in the previous step:
        ```bash
        # The job will read variables from its environment
        nomad job run gcp-dns-updater/nomad.job
        ```
    *   Alternatively, if using the project's Makefile structure:
        ```bash
        # Assumes the Makefile's deploy target doesn't need extra vars
        # and that required env vars are set in the deployment runner
        make deploy-gcp-dns-updater
        ```

## Files

*   `update_dns.py`: The core Python script for updating DNS (runs inside the container).
*   `requirements.txt`: Python dependencies (installed during Docker build).
*   `Dockerfile`: Defines how to build the service's Docker image.
*   `nomad.job`: Nomad job definition for periodic execution using the `gcp-dns-updater:latest` Docker image.
*   `README.md`: This documentation file.
