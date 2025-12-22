    # Base Image: UBI8 Node.js 18
    FROM registry.access.redhat.com/ubi8/nodejs-18

    # Metadata as labels
    LABEL io.k8s.description="Frontend UI for OCP TaskMaster" \
        io.k8s.display-name="TaskMaster Frontend" \
        io.openshift.tags="nodejs,frontend,web" \
        io.openshift.expose-services="8080:http" \
        maintainer="Aly Esmaeil"

    # Set work directory (Standard UBI path)
    WORKDIR /opt/app-root/src

    # Switch to root to fix permissions and install
    USER 0

    # Copy package.json and install dependencies
    COPY package.json ./
    RUN npm install

    # Copy application source code
    COPY . .

    # IMPORTANT: Fix permissions for OpenShift (User 1001 compat)
    # OpenShift runs containers with a random UID, but always in GID 0 (root group).
    # We must ensure that the application directory is writable by GID 0.
    RUN chown -R 1001:0 /opt/app-root/src && \
        chmod -R g+w /opt/app-root/src

    # Switch to non-root user
    USER 1001

    # Expose port 8080
    EXPOSE 8080

    # Start the application
    CMD ["npm", "start"]
