# moufida-signal — interpretability microservice (CBM scoring + axis probe).
# Multi-stage: compile a release binary, then ship it on a slim runtime.
FROM rust:1-slim AS build
WORKDIR /build
# Cache dependencies: copy manifests first, build a stub, then the real sources.
COPY signal/Cargo.toml ./Cargo.toml
RUN mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release && rm -rf src
COPY signal/src ./src
# Touch main so cargo rebuilds with the real sources.
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim
WORKDIR /srv
RUN useradd --system --uid 10001 moufida
COPY --from=build /build/target/release/moufida-signal /usr/local/bin/moufida-signal
# Committed assets (prior CBM weights). Probe directions are installed at runtime
# via POST /probe/install and persisted to this dir.
COPY signal/assets /srv/assets
RUN chown -R moufida:moufida /srv/assets
USER moufida
ENV SIGNAL_ASSETS_DIR=/srv/assets SIGNAL_PORT=8010
EXPOSE 8010
CMD ["moufida-signal"]
