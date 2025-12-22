    # Base Image: UBI8 Python 3.9
    FROM registry.access.redhat.com/ubi8/python-39

    # Metadata as labels
    LABEL io.k8s.description="Backend API for OCP TaskMaster" \
        io.k8s.description="Backend API... Requires: DATABASE_URL" \
        io.k8s.display-name="TaskMaster Backend" \
        io.openshift.tags="python,flask,backend" \
        io.openshift.expose-services="5000:http" \
        maintainer="Aly Esmaeil"

    # Environment variables
    ENV PYTHONUNBUFFERED=1

    # Set work directory (Standard UBI path)
    WORKDIR /opt/app-root/src

    # Switch to root to install dependencies and fix permissions
    USER 0

    # Copy requirements and install dependencies
    COPY requirements.txt .
    RUN pip install --upgrade pip && \
        pip install -r requirements.txt

    # Copy application source code
    COPY app.py .

    # IMPORTANT: Fix permissions for OpenShift (User 1001 compat)
    # OpenShift runs containers with a random UID, but always in GID 0 (root group).
    # We must ensure that the application directory is writable by GID 0.
    RUN chown -R 1001:0 /opt/app-root/src && \
        chmod -R g+w /opt/app-root/src

    # Switch to non-root user
    USER 1001

    # Expose port 5000
    EXPOSE 5000

    # Run the application
    CMD ["python", "app.py"]
