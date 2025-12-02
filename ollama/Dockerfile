FROM ollama/ollama:latest

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
