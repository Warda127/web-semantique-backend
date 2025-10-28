# Custom Fuseki Dockerfile
FROM eclipse-temurin:17-jre-alpine

# Set Fuseki version and directories
ENV FUSEKI_VERSION=5.2.0
ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/fuseki

# Install required packages
RUN apk add --no-cache \
    bash \
    curl \
    wget

# Create directories
RUN mkdir -p ${FUSEKI_HOME} ${FUSEKI_BASE}

WORKDIR /tmp

# Download and install Fuseki with fallback URLs
RUN echo "Downloading Apache Jena Fuseki ${FUSEKI_VERSION}..." && \
    (wget --timeout=30 -t 3 \
        https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz || \
     wget --timeout=30 -t 3 \
        https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz || \
     wget --timeout=30 -t 3 \
        http://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz) && \
    echo "Download complete, extracting..." && \
    tar -xzf apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz && \
    mv apache-jena-fuseki-${FUSEKI_VERSION}/* ${FUSEKI_HOME}/ && \
    rm -rf apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz apache-jena-fuseki-${FUSEKI_VERSION}

# Create Fuseki base structure
RUN mkdir -p ${FUSEKI_BASE}/databases ${FUSEKI_BASE}/configuration ${FUSEKI_BASE}/system ${FUSEKI_BASE}/backups

# Set working directory
WORKDIR ${FUSEKI_HOME}

# Expose port
EXPOSE 3030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3030/$$/ping || exit 1

# Set environment
ENV FUSEKI_BASE=${FUSEKI_BASE}
ENV JVM_ARGS="-Xmx2g"

# Run Fuseki server
CMD ["java", "-Xmx2g", "-jar", "fuseki-server.jar", "--update", "--mem", "/smartcity"]