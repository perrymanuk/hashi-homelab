FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY update_dns.py .

# Define the command to run the application
CMD ["python", "update_dns.py"]
