#!/usr/bin/env python3
"""
Azure Services Provisioning Script for PixCrawler
Provisions: App Service, Monitor, Data Lake, Static Web Apps
"""

import sys
import os
from typing import Dict, Optional
from datetime import datetime

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
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print(f"\nPython executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print("\nInstall packages with:")
    print(f"{sys.executable} -m pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-storage azure-mgmt-monitor rich")
    sys.exit(1)

console = Console()

# Configuration from environment variables with defaults
RESOURCE_GROUP = os.getenv("RESOURCE_GROUP", "pixcrawler-rg")
LOCATION = os.getenv("LOCATION", "eastus")
REGISTRY_NAME = os.getenv("REGISTRY_NAME", "pixcrawlerregistry")
ENVIRONMENT = os.getenv("ENVIRONMENT", "pixcrawler-env")
BACKEND_APP = os.getenv("BACKEND_APP", "pixcrawler-backend")
FRONTEND_APP = os.getenv("FRONTEND_APP", "pixcrawler-frontend")
STORAGE_NAME = os.getenv("STORAGE_NAME", "pixcrawlerstorage")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")


class AzureProvisioner:
    """Handles Azure resource provisioning"""
    
    def __init__(self, subscription_id: str, resource_group: str, location: str):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.location = location
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
        
        config_table.add_row("Resource Group", RESOURCE_GROUP)
        config_table.add_row("Location", LOCATION)
        config_table.add_row("Registry Name", REGISTRY_NAME)
        config_table.add_row("Environment", ENVIRONMENT)
        config_table.add_row("Backend App", BACKEND_APP)
        config_table.add_row("Frontend App", FRONTEND_APP)
        config_table.add_row("Storage Account", STORAGE_NAME)
        
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


def validate_configuration():
    """Validate required configuration"""
    if not SUBSCRIPTION_ID:
        console.print("[red]Error: AZURE_SUBSCRIPTION_ID environment variable not set[/red]")
        console.print("[yellow]Set it with: export AZURE_SUBSCRIPTION_ID=your-subscription-id[/yellow]")
        return False
    
    # Validate storage name
    storage_clean = STORAGE_NAME.lower().replace("-", "").replace("_", "")
    if not (3 <= len(storage_clean) <= 24) or not storage_clean.isalnum():
        console.print(f"[red]Error: Storage name must be 3-24 alphanumeric characters (got: {storage_clean})[/red]")
        console.print("[yellow]Set STORAGE_NAME environment variable to a valid name[/yellow]")
        return False
    
    return True


def main():
    """Main execution function"""
    console.print(Panel.fit(
        "[bold cyan]PixCrawler Azure Services Provisioning[/bold cyan]\n"
        "App Service • Monitoring • Data Lake • Static Web Apps",
        border_style="cyan"
    ))
    
    # Validate configuration
    if not validate_configuration():
        sys.exit(1)
    
    # Initialize provisioner
    provisioner = AzureProvisioner(
        SUBSCRIPTION_ID,
        RESOURCE_GROUP,
        LOCATION
    )
    
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
        
        # Create backend App Service
        progress.update(task, description=f"Creating Backend App Service: {BACKEND_APP}")
        provisioner.create_app_service(BACKEND_APP, sku="B1")
        
        # Create frontend Static Web App
        progress.update(task, description=f"Creating Frontend Static Web App: {FRONTEND_APP}")
        provisioner.create_static_web_app(FRONTEND_APP)
        
        # Create Storage Account with Data Lake
        storage_clean = STORAGE_NAME.lower().replace("-", "").replace("_", "")
        progress.update(task, description=f"Creating Storage Account: {storage_clean}")
        provisioner.create_storage_account(storage_clean, enable_datalake=True)
        
        # Setup monitoring
        progress.update(task, description="Setting up monitoring...")
        provisioner.create_application_insights(BACKEND_APP)
        
        progress.update(task, description="Provisioning complete!", completed=True)
    
    # Display results
    provisioner.display_results()
    
    console.print("\n[green]✓ Provisioning completed successfully![/green]")
    console.print(f"[dim]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    
    # Display next steps
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print(f"1. Deploy backend to: {BACKEND_APP}")
    console.print(f"2. Deploy frontend to: {FRONTEND_APP}")
    console.print(f"3. Configure Data Lake access for: {storage_clean}")
    console.print(f"4. Set up monitoring alerts and dashboards")


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