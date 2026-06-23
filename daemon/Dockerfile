# Build a static ~10 MB daemon binary.
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY daemon/go.mod daemon/go.sum ./
RUN go mod download
COPY daemon/ ./
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /out/moufida-daemon ./cmd

FROM alpine:3.20
RUN adduser -D -u 10001 moufida
USER moufida
COPY --from=build /out/moufida-daemon /usr/local/bin/moufida-daemon
ENTRYPOINT ["/usr/local/bin/moufida-daemon"]
