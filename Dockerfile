# ==============================
# STAGE 1: BUILDER
# ==============================
ARG BASE_IMAGE=debian:13-slim
FROM ${BASE_IMAGE} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install build dependencies (includes all native build requirements)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    cmake \
    clang \
    build-essential \
    libssl-dev \
    libcurl4-openssl-dev \
    liblmdb-dev \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build_space

# Copy source code
COPY ./src /build_space/src
COPY ./third_party /build_space/third_party
COPY ./CMakeLists.txt /build_space/CMakeLists.txt
COPY ./install.sh /build_space/install.sh

# Build arguments with safe defaults
ARG BUILD_ARCH=avx2
ARG DEBUG=false

ENV BUILD_ARCH=${BUILD_ARCH}
ENV DEBUG=${DEBUG}

# Ensure AVX2 compilation works on slim toolchain
ENV CXXFLAGS="-mavx2"
ENV CFLAGS="-mavx2"

# Run build script
RUN chmod +x ./install.sh && \
    ARCH_FLAG="--${BUILD_ARCH}" && \
    if [ "$DEBUG" = "true" ]; then \
    ./install.sh $ARCH_FLAG --debug_all --skip-deps; \
    else \
    ./install.sh $ARCH_FLAG --release --skip-deps; \
    fi && \
    echo "Build output:" && \
    find ./build -type f || true && \
    cp $(find ./build -type f -name "ndd*" | head -n 1) ./ndd-server


# ==============================
# STAGE 2: RUNTIME
# ==============================
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=/usr/local/bin:$PATH

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libcurl4 \
    liblmdb0 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r -g 1000 endee && \
    useradd -r -u 1000 -g endee -s /bin/false -d /home/endee endee && \
    mkdir -p /data /home/endee && \
    chown -R endee:endee /data /home/endee && \
    chmod 755 /data

# Copy compiled binary
COPY --from=builder /build_space/ndd-server /usr/local/bin/ndd-server
RUN chmod +x /usr/local/bin/ndd-server

# Copy frontend if produced during build
COPY --from=builder /build_space/frontend /usr/local/frontend

USER endee
WORKDIR /home/endee

# App environment variables
ENV NDD_DATA_DIR=/data \
    NDD_SERVER_PORT=8080 \
    NDD_LOG_LEVEL=info \
    NDD_NUM_THREADS=0

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

LABEL org.opencontainers.image.title="endee-oss"
LABEL org.opencontainers.image.description="Endee Open Source"
LABEL org.opencontainers.image.url="https://endee.io/"
LABEL org.opencontainers.image.documentation="https://docs.endee.io/"
LABEL org.opencontainers.image.vendor="Endee Labs"
LABEL org.opencontainers.image.source=""

ENTRYPOINT ["/usr/local/bin/ndd-server"]
CMD []
