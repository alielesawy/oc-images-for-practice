# Base image
FROM registry.access.redhat.com/ubi8/python-39

# Set work directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application source code
COPY app.py .

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
