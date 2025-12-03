FROM nginx:1.25-alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directory for DASH content
RUN mkdir -p /usr/share/nginx/html/dash/segments

# Copy manifest.mpd (required - this file should always exist)
COPY segments/manifest.mpd /usr/share/nginx/html/dash/manifest.mpd

# Note: Segment files (.m4s, .mp4, etc.) are provided via volume mount
# in docker-compose.yaml. This keeps the image small and allows
# updating content without rebuilding the image.

# Expose port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

