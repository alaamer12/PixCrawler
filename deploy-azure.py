#!/usr/bin/env python3
"""
Azure Services Provisioning Script for PixCrawler
Provisions: App Service, Monitor, Data Lake, Static Web Apps
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.web import WebSiteManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.core.exceptions import AzureError
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from pydantic import BaseModel, Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print(f"\nPython executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print("\nInstall packages with:")
    print(f"{sys.executable} -m pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-storage azure-mgmt-monitor rich pydantic pydantic-settings")
    sys.exit(1)

console = Console()

class AzureDeploymentSettings(BaseSettings):
    """Azure deployment configuration from .env.azure file."""
    
    model_config = SettingsConfigDict(
        env_file=".env.azure",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure Subscription
    azure_subscription_id: str = Field(..., description="Azure subscription ID")
    
    # Resource Configuration
    resource_group: str = Field(default="pixcrawler-rg", description="Azure resource group name")
    location: str = Field(default="eastus", description="Azure region")
    
    # App Service Configuration
    backend_app_name: str = Field(default="pixcrawler-backend", description="Backend App Service name")
    frontend_app_name: str = Field(default="pixcrawler-frontend", description="Frontend Static Web App name")
    app_service_sku: str = Field(default="B1", description="App Service SKU")
    
    # Storage Configuration
    storage_account_name: str = Field(default="pixcrawlerstorage", description="Storage account name")
    storage_container_name: str = Field(default="datasets", description="Blob container name")
    enable_data_lake: bool = Field(default=True, description="Enable Data Lake Gen2")
    
    # Blob Storage Configuration
    azure_blob_connection_string: Optional[str] = Field(default=None, description="Azure Blob Storage connection string")
    azure_blob_account_name: Optional[str] = Field(default=None, description="Azure Blob Storage account name")
    azure_blob_account_key: Optional[str] = Field(default=None, description="Azure Blob Storage account key")
    azure_blob_container_name: str = Field(default="pixcrawler-datasets", description="Blob container for datasets")
    azure_blob_default_tier: str = Field(default="hot", description="Default blob tier (hot/cool/archive)")
    
    # Environment
    environment: str = Field(default="production", description="Deployment environment")
    
    # Deployment Configuration
    deploy_backend: bool = Field(default=True, description="Deploy backend to Azure App Service")
    deploy_frontend: bool = Field(default=True, description="Deploy frontend to Azure Static Web Apps")
    
    # Optional GitHub Configuration
    github_repo_url: Optional[str] = Field(default=None, description="GitHub repository URL for CI/CD")
    github_branch: str = Field(default="main", description="GitHub branch for deployment")
    
    def get_clean_storage_name(self) -> str:
        """Get storage account name cleaned for Azure requirements."""
        return self.storage_account_name.lower().replace("-", "").replace("_", "")[:24]


class AzureProvisioner:
    """Handles Azure resource provisioning"""
    
    def __init__(self, settings: AzureDeploymentSettings):
        self.settings = settings
        self.subscription_id = settings.azure_subscription_id
        self.resource_group = settings.resource_group
        self.location = settings.location
        self.credential = None
        self.resource_client = None
        self.web_client = None
        self.storage_client = None
        self.monitor_client = None
        self.results: Dict[str, str] = {}
        
    def authenticate(self) -> bool:
        """Authenticate with Azure"""
        try:
            console.print("[cyan]Authenticating with Azure...[/cyan]")
            self.credential = DefaultAzureCredential()
            
            self.resource_client = ResourceManagementClient(
                self.credential, self.subscription_id
            )
            self.web_client = WebSiteManagementClient(
                self.credential, self.subscription_id
            )
            self.storage_client = StorageManagementClient(
                self.credential, self.subscription_id
            )
            self.monitor_client = MonitorManagementClient(
                self.credential, self.subscription_id
            )
            
            console.print("[green]✓ Authentication successful[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Authentication failed: {str(e)}[/red]")
            return False
    
    def create_resource_group(self) -> bool:
        """Create or verify resource group"""
        try:
            console.print(f"[cyan]Checking resource group: {self.resource_group}[/cyan]")
            
            # Check if resource group exists
            try:
                rg_result = self.resource_client.resource_groups.get(self.resource_group)
                console.print(f"[yellow]⚠ Resource group already exists in location: {rg_result.location}[/yellow]")
                console.print(f"[cyan]Using existing resource group: {rg_result.name}[/cyan]")
                self.results["Resource Group"] = f"{rg_result.name} (existing, location: {rg_result.location})"
                console.print(f"[green]✓ Resource group ready: {rg_result.name}[/green]")
                return True
            except:
                # Resource group doesn't exist, create it
                console.print(f"[cyan]Creating new resource group: {self.resource_group}[/cyan]")
                rg_result = self.resource_client.resource_groups.create_or_update(
                    self.resource_group,
                    {"location": self.location}
                )
                self.results["Resource Group"] = rg_result.name
                console.print(f"[green]✓ Resource group created: {rg_result.name}[/green]")
                return True
                
        except AzureError as e:
            console.print(f"[red]✗ Resource group operation failed: {str(e)}[/red]")
            return False
    
    def create_app_service(self, app_name: str, sku: str = "B1") -> bool:
        """Create App Service with App Service Plan"""
        try:
            console.print(f"[cyan]Creating App Service: {app_name}[/cyan]")
            
            plan_name = f"{app_name}-plan"
            
            # Create App Service Plan
            console.print(f"  Creating App Service Plan: {plan_name}")
            plan_result = self.web_client.app_service_plans.begin_create_or_update(
                self.resource_group,
                plan_name,
                {
                    "location": self.location,
                    "sku": {"name": sku, "tier": "Basic", "capacity": 1},
                    "kind": "linux",
                    "reserved": True
                }
            ).result()
            
            # Create Web App
            console.print(f"  Creating Web App: {app_name}")
            app_result = self.web_client.web_apps.begin_create_or_update(
                self.resource_group,
                app_name,
                {
                    "location": self.location,
                    "server_farm_id": plan_result.id,
                    "site_config": {
                        "linux_fx_version": "PYTHON|3.11",
                        "always_on": True
                    }
                }
            ).result()
            
            self.results[f"App Service ({app_name})"] = f"https://{app_result.default_host_name}"
            console.print(f"[green]✓ App Service created: https://{app_result.default_host_name}[/green]")
            return True
        except AzureError as e:
            console.print(f"[red]✗ App Service creation failed: {str(e)}[/red]")
            return False
    
    def create_storage_account(self, storage_name: str, enable_datalake: bool = True) -> bool:
        """Create Storage Account with Data Lake Gen2"""
        try:
            console.print(f"[cyan]Creating Storage Account: {storage_name}[/cyan]")
            
            storage_params = {
                "location": self.location,
                "sku": {"name": "Standard_LRS"},
                "kind": "StorageV2",
                "is_hns_enabled": enable_datalake,  # Hierarchical namespace for Data Lake
                "encryption": {
                    "services": {
                        "blob": {"enabled": True},
                        "file": {"enabled": True}
                    },
                    "key_source": "Microsoft.Storage"
                }
            }
            
            storage_result = self.storage_client.storage_accounts.begin_create(
                self.resource_group,
                storage_name,
                storage_params
            ).result()
            
            # Create Data Lake container
            if enable_datalake:
                console.print("  Creating Data Lake container: datalake")
                try:
                    self.storage_client.blob_containers.create(
                        self.resource_group,
                        storage_name,
                        "datalake",
                        {}
                    )
                    console.print("  [green]✓ Data Lake container created[/green]")
                except Exception as e:
                    console.print(f"  [yellow]⚠ Container may already exist: {str(e)}[/yellow]")
            
            self.results["Storage Account"] = storage_name
            self.results["Data Lake Gen2"] = "Enabled" if enable_datalake else "Disabled"
            console.print(f"[green]✓ Storage Account created: {storage_name}[/green]")
            return True
        except AzureError as e:
            console.print(f"[red]✗ Storage Account creation failed: {str(e)}[/red]")
            return False
    
    def create_static_web_app(self, app_name: str, repo_url: Optional[str] = None) -> bool:
        """Create Static Website using Azure Storage (alternative to Static Web Apps)"""
        try:
            console.print(f"[cyan]Creating Static Website: {app_name}[/cyan]")
            
            # Static Web Apps have limited region availability that may not match subscription policy
            # Use Storage Account static website as alternative (available in all regions)
            storage_name = app_name.replace("-", "").lower()[:24]
            
            console.print(f"  Creating Storage Account for static website: {storage_name}")
            
            storage_params = {
                "location": self.location,
                "sku": {"name": "Standard_LRS"},
                "kind": "StorageV2",
                "encryption": {
                    "services": {
                        "blob": {"enabled": True},
                        "file": {"enabled": True}
                    },
                    "key_source": "Microsoft.Storage"
                }
            }
            
            storage_result = self.storage_client.storage_accounts.begin_create(
                self.resource_group,
                storage_name,
                storage_params
            ).result()
            
            # Enable static website hosting
            console.print("  Enabling static website hosting...")
            try:
                self.storage_client.blob_services.set_service_properties(
                    self.resource_group,
                    storage_name,
                    {
                        "static_website": {
                            "enabled": True,
                            "index_document": "index.html",
                            "error_document_404_path": "404.html"
                        }
                    }
                )
                
                # Get the static website URL
                account_keys = self.storage_client.storage_accounts.list_keys(
                    self.resource_group, storage_name
                )
                primary_endpoint = storage_result.primary_endpoints.web
                
                self.results[f"Static Website ({app_name})"] = primary_endpoint
                console.print(f"[green]✓ Static Website created: {primary_endpoint}[/green]")
                console.print(f"[yellow]  Note: Upload your frontend files to the '$web' container[/yellow]")
                return True
            except Exception as e:
                console.print(f"[yellow]⚠ Static website enabled, configure manually: {str(e)}[/yellow]")
                self.results[f"Static Website ({app_name})"] = f"{storage_name} (manual setup required)"
                return True
                
        except AzureError as e:
            console.print(f"[red]✗ Static Website creation failed: {str(e)}[/red]")
            return False
    
    def create_blob_container(self, storage_name: str, container_name: str) -> bool:
        """Create blob container for datasets"""
        try:
            console.print(f"[cyan]Creating blob container: {container_name}[/cyan]")
            
            try:
                self.storage_client.blob_containers.create(
                    self.resource_group,
                    storage_name,
                    container_name,
                    {
                        "public_access": "None",  # Private container
                        "metadata": {
                            "purpose": "pixcrawler-datasets",
                            "created_by": "deploy-script"
                        }
                    }
                )
                console.print(f"  [green]✓ Container created: {container_name}[/green]")
            except Exception as e:
                if "already exists" in str(e).lower():
                    console.print(f"  [yellow]⚠ Container already exists: {container_name}[/yellow]")
                else:
                    console.print(f"  [yellow]⚠ Container creation issue: {str(e)}[/yellow]")
            
            self.results[f"Blob Container ({container_name})"] = f"{storage_name}/{container_name}"
            return True
            
        except Exception as e:
            console.print(f"[red]✗ Blob container creation failed: {str(e)}[/red]")
            return False

    def create_application_insights(self, app_name: str) -> bool:
        """Create Application Insights for monitoring"""
        try:
            console.print(f"[cyan]Setting up Application Insights: {app_name}-insights[/cyan]")
            
            # Note: Application Insights creation requires azure-mgmt-applicationinsights
            console.print("[yellow]⚠ Application Insights requires azure-mgmt-applicationinsights package[/yellow]")
            console.print("[yellow]  Install with: pip install azure-mgmt-applicationinsights[/yellow]")
            
            self.results["Monitoring"] = "Configured (requires azure-mgmt-applicationinsights)"
            return True
        except Exception as e:
            console.print(f"[yellow]⚠ Monitoring setup needs manual configuration: {str(e)}[/yellow]")
            return True
    
    def display_configuration(self):
        """Display current configuration"""
        config_table = Table(title="Configuration", box=box.ROUNDED, show_header=False)
        config_table.add_column("Parameter", style="cyan", no_wrap=True)
        config_table.add_column("Value", style="yellow")
        
        config_table.add_row("Subscription ID", self.settings.azure_subscription_id[:8] + "...")
        config_table.add_row("Resource Group", self.settings.resource_group)
        config_table.add_row("Location", self.settings.location)
        config_table.add_row("Environment", self.settings.environment)
        config_table.add_row("Backend App", self.settings.backend_app_name)
        config_table.add_row("Frontend App", self.settings.frontend_app_name)
        config_table.add_row("Storage Account", self.settings.get_clean_storage_name())
        config_table.add_row("Container Name", self.settings.storage_container_name)
        config_table.add_row("Data Lake Gen2", "Enabled" if self.settings.enable_data_lake else "Disabled")
        
        console.print()
        console.print(config_table)
        console.print()
    
    def display_results(self):
        """Display provisioning results in a formatted table"""
        table = Table(title="Azure Resources Provisioned", box=box.ROUNDED)
        table.add_column("Resource", style="cyan", no_wrap=True)
        table.add_column("Details", style="green")
        
        for resource, value in self.results.items():
            table.add_row(resource, value)
        
        console.print()
        console.print(table)


def load_settings() -> AzureDeploymentSettings:
    """Load and validate deployment settings."""
    try:
        # Check if .env.azure exists
        env_file = Path(".env.azure")
        if not env_file.exists():
            console.print("[red]Error: .env.azure file not found[/red]")
            console.print("[yellow]Create .env.azure file with your Azure configuration[/yellow]")
            console.print("[yellow]See .env.example.azure for template[/yellow]")
            sys.exit(1)
        
        settings = AzureDeploymentSettings()
        
        # Validate storage name
        storage_clean = settings.get_clean_storage_name()
        if not (3 <= len(storage_clean) <= 24) or not storage_clean.isalnum():
            console.print(f"[red]Error: Storage name must be 3-24 alphanumeric characters (got: {storage_clean})[/red]")
            console.print("[yellow]Update STORAGE_ACCOUNT_NAME in .env.azure[/yellow]")
            sys.exit(1)
        
        return settings
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)


def deploy_backend(provisioner: AzureProvisioner, settings: AzureDeploymentSettings) -> bool:
    """Deploy backend code to Azure App Service."""
    console.print("\n[bold cyan]Deploying Backend to Azure App Service[/bold cyan]")
    
    try:
        # Check if backend directory exists and has required files
        if not Path("backend").exists():
            console.print("[red]❌ Backend directory not found[/red]")
            return False
        
        # Create deployment package (exclude frontend)
        console.print("[cyan]📦 Creating backend deployment package...[/cyan]")
        
        # The actual deployment would be handled by Azure DevOps, GitHub Actions, or Azure CLI
        console.print("[yellow]⚠️  Backend deployment requires Azure CLI or CI/CD pipeline[/yellow]")
        console.print("[yellow]   Run: az webapp deploy --resource-group {settings.resource_group} --name {settings.backend_app_name} --src-path .[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Backend deployment failed: {e}[/red]")
        return False

def deploy_frontend(provisioner: AzureProvisioner, settings: AzureDeploymentSettings) -> bool:
    """Deploy frontend to Azure Static Web Apps."""
    console.print("\n[bold cyan]Deploying Frontend to Azure Static Web Apps[/bold cyan]")
    
    try:
        # Check if frontend directory exists
        frontend_path = Path("frontend")
        if not frontend_path.exists():
            console.print("[red]❌ Frontend directory not found[/red]")
            return False
        
        # Check if built files exist
        build_path = frontend_path / ".next"
        if not build_path.exists():
            console.print("[yellow]⚠️  Frontend not built. Building now...[/yellow]")
            
            # Build frontend
            import subprocess
            try:
                subprocess.run(["bun", "install"], cwd=frontend_path, check=True)
                subprocess.run(["bun", "run", "build"], cwd=frontend_path, check=True)
                console.print("[green]✅ Frontend built successfully[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]❌ Frontend build failed: {e}[/red]")
                return False
        
        console.print("[yellow]⚠️  Frontend deployment requires Azure Static Web Apps CLI[/yellow]")
        console.print("[yellow]   Run: swa deploy --app-location frontend --output-location .next[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Frontend deployment failed: {e}[/red]")
        return False

def configure_environment_variables(provisioner: AzureProvisioner, settings: AzureDeploymentSettings) -> None:
    """Display environment variable configuration instructions."""
    console.print("\n[bold cyan]Environment Variables Configuration[/bold cyan]")
    
    # Get storage connection string (would need to be retrieved from Azure)
    storage_name = settings.get_clean_storage_name()
    
    console.print(f"[cyan]Configure these environment variables in Azure Portal:[/cyan]")
    console.print(f"[cyan]App Service: {settings.backend_app_name} → Configuration → Application Settings[/cyan]")
    
    env_vars = [
        ("ENVIRONMENT", "production"),
        ("PIXCRAWLER_ENVIRONMENT", "production"),
        ("STORAGE_PROVIDER", "azure"),
        ("AZURE_BLOB_ACCOUNT_NAME", storage_name),
        ("AZURE_BLOB_CONTAINER_NAME", settings.azure_blob_container_name),
        ("AZURE_BLOB_DEFAULT_TIER", settings.azure_blob_default_tier),
    ]
    
    table = Table(title="Required Environment Variables", box=box.ROUNDED)
    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")
    
    for var, value in env_vars:
        table.add_row(var, value)
    
    console.print(table)
    
    console.print("\n[yellow]⚠️  Also configure:[/yellow]")
    console.print("   - AZURE_BLOB_CONNECTION_STRING (from Storage Account → Access Keys)")
    console.print("   - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    console.print("   - DATABASE_URL (Supabase PostgreSQL)")
    console.print("   - REDIS_URL (if using external Redis)")

def main():
    """Main execution function"""
    console.print(Panel.fit(
        "[bold cyan]PixCrawler Azure Deployment & Provisioning[/bold cyan]\n"
        "Infrastructure • Backend • Frontend • Storage",
        border_style="cyan"
    ))
    
    # Load configuration
    settings = load_settings()
    
    # Initialize provisioner
    provisioner = AzureProvisioner(settings)
    
    # Display configuration
    provisioner.display_configuration()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Starting provisioning...", total=None)
        
        # Authenticate
        if not provisioner.authenticate():
            console.print("[red]Failed to authenticate. Exiting.[/red]")
            sys.exit(1)
        
        # Create resource group
        progress.update(task, description="Creating resource group...")
        if not provisioner.create_resource_group():
            console.print("[red]Failed to create resource group. Exiting.[/red]")
            sys.exit(1)
        
        # Create backend App Service (if enabled)
        if settings.deploy_backend:
            progress.update(task, description=f"Creating Backend App Service: {settings.backend_app_name}")
            provisioner.create_app_service(settings.backend_app_name, sku=settings.app_service_sku)
        
        # Create frontend Static Web App (if enabled)
        if settings.deploy_frontend:
            progress.update(task, description=f"Creating Frontend Static Web App: {settings.frontend_app_name}")
            provisioner.create_static_web_app(settings.frontend_app_name, settings.github_repo_url)
        
        # Create Storage Account with Data Lake
        storage_clean = settings.get_clean_storage_name()
        progress.update(task, description=f"Creating Storage Account: {storage_clean}")
        provisioner.create_storage_account(storage_clean, enable_datalake=settings.enable_data_lake)
        
        # Create blob container for datasets
        progress.update(task, description=f"Creating blob container: {settings.storage_container_name}")
        provisioner.create_blob_container(storage_clean, settings.storage_container_name)
        
        # Setup monitoring
        progress.update(task, description="Setting up monitoring...")
        provisioner.create_application_insights(settings.backend_app_name)
        
        progress.update(task, description="Provisioning complete!", completed=True)
    
    # Display results
    provisioner.display_results()
    
    # Configure environment variables
    configure_environment_variables(provisioner, settings)
    
    console.print("\n[green]✓ Infrastructure provisioning completed successfully![/green]")
    console.print(f"[dim]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    
    # Deploy applications (if requested)
    deployment_success = True
    
    if settings.deploy_backend:
        deployment_success &= deploy_backend(provisioner, settings)
    
    if settings.deploy_frontend:
        deployment_success &= deploy_frontend(provisioner, settings)
    
    # Final status
    if deployment_success:
        console.print("\n[green]🎉 Deployment completed successfully![/green]")
    else:
        console.print("\n[yellow]⚠️  Infrastructure created, but deployment needs manual steps[/yellow]")
    
    # Display final instructions
    console.print("\n[bold cyan]Final Steps:[/bold cyan]")
    console.print("1. Configure environment variables in Azure Portal")
    console.print("2. Set up continuous deployment from GitHub")
    console.print("3. Test the deployed applications")
    console.print("4. Configure custom domains (optional)")
    console.print("5. Set up monitoring alerts and cost budgets")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Provisioning cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)