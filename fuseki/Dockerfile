# Fuseki Dockerfile
FROM openjdk:11-jre-slim

# Set Fuseki version
ENV FUSEKI_VERSION=4.10.0
ENV FUSEKI_HOME=/fuseki
ENV FUSEKI_BASE=/fuseki-base

# Install wget and unzip
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and install Fuseki
RUN wget -q https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz && \
    tar -xzf apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz && \
    mv apache-jena-fuseki-${FUSEKI_VERSION} ${FUSEKI_HOME} && \
    rm apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz

# Create Fuseki base directory
RUN mkdir -p ${FUSEKI_BASE}/databases ${FUSEKI_BASE}/configuration

# Set working directory
WORKDIR ${FUSEKI_HOME}

# Copy configuration
COPY config.ttl ${FUSEKI_BASE}/configuration/

# Expose Fuseki port
EXPOSE 3030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3030/$/ping || exit 1

# Set environment variable for Fuseki base
ENV FUSEKI_BASE=${FUSEKI_BASE}

# Run Fuseki
CMD ["java", "-Xmx2g", "-jar", "fuseki-server.jar", "--config=/fuseki-base/configuration/config.ttl"]