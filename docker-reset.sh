#!/bin/bash

echo "🧹 Cleaning up Docker containers and volumes..."

# Stop and remove containers
docker-compose down

# Remove volumes (complete clean slate)
docker volume rm smartcity-fuseki-data 2>/dev/null || true

echo "🏗️  Building images..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

echo "📋 Showing logs..."
docker-compose logs -f