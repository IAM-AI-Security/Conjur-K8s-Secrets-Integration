FROM alpine:3.18
RUN apk add --no-cache curl bash
WORKDIR /app
COPY app.py .
CMD ["sh", "-c", "echo Container started && sleep 3600"]
