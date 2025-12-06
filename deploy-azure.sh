#!/bin/bash
# ============================================================================
# PixCrawler Azure Deployment Script (Bash)
# ============================================================================
# Usage: ./deploy-azure.sh
# Prerequisites: Azure CLI installed and logged in (az login)
# ============================================================================

set -e

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-pixcrawler-rg}"
LOCATION="${LOCATION:-eastus}"
REGISTRY_NAME="${REGISTRY_NAME:-pixcrawlerregistry}"
ENVIRONMENT="${ENVIRONMENT:-pixcrawler-env}"
BACKEND_APP="${BACKEND_APP:-pixcrawler-backend}"
FRONTEND_APP="${FRONTEND_APP:-pixcrawler-frontend}"

echo "🚀 PixCrawler Azure Deployment Script"
echo "======================================="
echo ""

# ============================================================================
# 1. Check Prerequisites
# ============================================================================
echo "📋 Step 1: Checking prerequisites..."

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Running 'az login'..."
    az login
fi

ACCOUNT_NAME=$(az account show --query user.name -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo "✅ Logged in as: $ACCOUNT_NAME"
echo "✅ Subscription: $SUBSCRIPTION_NAME"
echo ""
 
# ============================================================================
# 2. Create Azure Resources
# ============================================================================
echo "🏗️  Step 2: Creating Azure resources..."

# Create Resource Group
echo "Creating resource group: $RESOURCE_GROUP..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
echo "✅ Resource group created"

# Create Container Registry
echo "Creating container registry: $REGISTRY_NAME..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none
echo "✅ Container registry created"

# Get registry credentials
REGISTRY_SERVER=$(az acr show --name $REGISTRY_NAME --query loginServer -o tsv)
REGISTRY_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
REGISTRY_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv)

echo "✅ Registry server: $REGISTRY_SERVER"

# Create Container Apps Environment
echo "Creating Container Apps environment: $ENVIRONMENT..."
az containerapp env create \
    --name $ENVIRONMENT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output none
echo "✅ Container Apps environment created"
echo ""

# ============================================================================
# 3. Build and Push Docker Images
# ============================================================================
echo "🐳 Step 3: Building and pushing Docker images..."

# Login to ACR
echo "Logging in to Azure Container Registry..."
az acr login --name $REGISTRY_NAME

# Build and push backend
echo "Building backend image..."
docker build -t "${REGISTRY_SERVER}/pixcrawler-backend:latest" -f Dockerfile --target runtime .
echo "Pushing backend image..."
docker push "${REGISTRY_SERVER}/pixcrawler-backend:latest"
echo "✅ Backend image pushed"

# Build and push frontend
echo "Building frontend image..."
docker build -t "${REGISTRY_SERVER}/pixcrawler-frontend:latest" -f frontend/Dockerfile ./frontend
echo "Pushing frontend image..."
docker push "${REGISTRY_SERVER}/pixcrawler-frontend:latest"
echo "✅ Frontend image pushed"
echo ""

# ============================================================================
# 4. Deploy Backend Container App
# ============================================================================
echo "🚢 Step 4: Deploying backend container app..."

# Read environment variables from .env.example.azure (if exists)
ENV_VARS=""
if [ -f .env.example.azure ]; then
    echo "Loading environment variables from .env.example.azure..."
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] && continue
        [[ -z $key ]] && continue
        
        # Skip placeholder values
        [[ $value =~ ^your-.* ]] && continue
        [[ $value =~ ^https://your-.* ]] && continue
        
        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        if [ -n "$key" ] && [ -n "$value" ]; then
            ENV_VARS="$ENV_VARS $key=$value"
        fi
    done < .env.example.azure
fi

# Add essential environment variables
ENV_VARS="$ENV_VARS ENVIRONMENT=production PORT=8000 HOST=0.0.0.0"

# Create backend container app
az containerapp create \
    --name $BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --image "${REGISTRY_SERVER}/pixcrawler-backend:latest" \
    --target-port 8000 \
    --ingress external \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --registry-server $REGISTRY_SERVER \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --env-vars $ENV_VARS \
    --output none

BACKEND_URL=$(az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
echo "✅ Backend deployed: https://$BACKEND_URL"
echo ""

# ============================================================================
# 5. Deploy Frontend Container App
# ============================================================================
echo "🌐 Step 5: Deploying frontend container app..."

# Create frontend container app
az containerapp create \
    --name $FRONTEND_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT \
    --image "${REGISTRY_SERVER}/pixcrawler-frontend:latest" \
    --target-port 3000 \
    --ingress external \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --registry-server $REGISTRY_SERVER \
    --registry-username $REGISTRY_USERNAME \
    --registry-password $REGISTRY_PASSWORD \
    --env-vars "NEXT_PUBLIC_API_URL=https://$BACKEND_URL" \
    --output none

FRONTEND_URL=$(az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
echo "✅ Frontend deployed: https://$FRONTEND_URL"
echo ""

# ============================================================================
# 6. Update Backend CORS
# ============================================================================
echo "🔧 Step 6: Updating backend CORS settings..."

az containerapp update \
    --name $BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars "ALLOWED_ORIGINS=https://$FRONTEND_URL" \
    --output none

echo "✅ CORS updated"
echo ""

# ============================================================================
# 7. Deployment Complete
# ============================================================================
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📍 Resource Group: $RESOURCE_GROUP"
echo "📦 Container Registry: $REGISTRY_SERVER"
echo ""
echo "🔗 Your Application URLs:"
echo "   Backend API:  https://$BACKEND_URL"
echo "   Frontend App: https://$FRONTEND_URL"
echo ""
echo "💡 Next Steps:"
echo "   1. Update Supabase credentials via Azure Portal"
echo "      → Container Apps → $BACKEND_APP → Configuration → Environment Variables"
echo "   2. Set SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL"
echo "   3. Test your backend: https://$BACKEND_URL/health"
echo "   4. Access your frontend: https://$FRONTEND_URL"
echo ""
echo "📚 View logs:"
echo "   az containerapp logs show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --follow"
echo ""
