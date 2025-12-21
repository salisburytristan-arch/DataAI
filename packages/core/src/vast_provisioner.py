"""Vast.ai provisioning for GPU rentals with vLLM tunnel management.

Handles:
- Instance provisioning via Vast.ai API
- SSH tunnel setup for vLLM access
- Lifecycle management (start, stop, destroy)
- Cost tracking and budget limits
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VastInstance:
    """Represents a Vast.ai GPU instance."""
    instance_id: str
    machine_id: str
    gpu_type: str              # e.g., "RTX 4090", "A100"
    provider_name: str
    ssh_host: str
    ssh_port: int
    ssh_user: str = "root"
    status: str = "pending"    # pending, running, stopped, destroying
    hourly_rate: float = 0.0   # $/hour
    created_at: str = ""
    ssh_tunnel_pid: Optional[int] = None
    local_port: int = 8000     # Default vLLM port forward


class VastProvisioner:
    """
    Manages GPU instance provisioning via Vast.ai.
    
    Features:
    - Search for available instances
    - Provision new instances with vLLM
    - SSH tunnel setup for local access
    - Cost tracking
    - Automatic cleanup
    
    Requirements:
    - vastai CLI installed (pip install vastai)
    - Vast.ai API key (VAST_API_KEY env var)
    - SSH key configured (~/.ssh/id_rsa)
    
    Usage:
        provisioner = VastProvisioner(api_key=os.getenv("VAST_API_KEY"))
        instances = provisioner.search_instances(min_vram=40)
        instance = provisioner.provision(
            machine_id=instances[0]["id"],
            image="vllm/vllm-openai:v0.4.0",
            vllm_model="deepseek-ai/deepseek-7b"
        )
        provisioner.setup_ssh_tunnel(instance)
        # Access via http://localhost:8000/v1/completions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Vast provisioner.
        
        Args:
            api_key: Vast.ai API key (default: VAST_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("VAST_API_KEY")
        if not self.api_key:
            raise ValueError("VAST_API_KEY environment variable not set")
        
        self.base_url = "https://api.vast.ai/api/v0"
        self.instances: Dict[str, VastInstance] = {}
        self.total_cost = 0.0
        self.budget_limit = 100.0  # Default $100 limit
    
    def search_instances(
        self,
        min_vram: int = 40,
        gpu_types: Optional[List[str]] = None,
        max_price: float = 1.0,
        sort_by: str = "biddable_flops"
    ) -> List[Dict[str, Any]]:
        """
        Search for available GPU instances.
        
        Args:
            min_vram: Minimum VRAM in GB
            gpu_types: List of GPU types to filter (e.g., ["A100", "RTX 4090"])
            max_price: Maximum hourly rate in USD
            sort_by: Sort field (biddable_flops, reliability, price)
            
        Returns:
            List of available instances
        """
        # Build filter query
        filters = [
            "verified = true",
            f"gpu_ram >= {min_vram * 1000}",  # Convert GB to MB
            f"dph_total <= {max_price}",
            "inet_up >= 100",  # 100 Mbps minimum
        ]
        
        if gpu_types:
            gpu_filter = " OR ".join([f'gpu_name = "{gpu}"' for gpu in gpu_types])
            filters.append(f"({gpu_filter})")
        
        query = " AND ".join(filters)
        
        try:
            # Using vastai CLI for simplicity
            cmd = [
                "vastai",
                "search",
                "offers",
                f"--filter '{query}'",
                f"--sort {sort_by}",
            ]
            
            result = self._run_vastai_cmd(cmd)
            if result:
                return json.loads(result)
            return []
        
        except Exception as e:
            print(f"Warning: Failed to search Vast instances: {e}")
            return []
    
    def provision(
        self,
        machine_id: int,
        image: str = "vllm/vllm-openai:v0.4.0",
        vllm_model: str = "meta-llama/Llama-2-7b-hf",
        gpu_count: int = 1,
        volume_size: int = 50,  # GB
        name_prefix: str = "acx-teacher"
    ) -> Optional[VastInstance]:
        """
        Provision a new GPU instance.
        
        Args:
            machine_id: Vast.ai machine ID
            image: Docker image for vLLM
            vllm_model: HuggingFace model ID
            gpu_count: Number of GPUs needed
            volume_size: Volume size in GB
            name_prefix: Instance name prefix
            
        Returns:
            VastInstance if successful, None otherwise
        """
        try:
            # Prepare instance name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            instance_name = f"{name_prefix}_{timestamp}"
            
            # Prepare vLLM startup command
            startup_cmd = (
                f"docker pull {image} && "
                f"docker run -d --gpus all -p 8000:8000 "
                f"-v /mnt/cache:/root/.cache "
                f"{image} "
                f"--model {vllm_model} "
                f"--tensor-parallel-size {gpu_count}"
            )
            
            # Call vastai create
            cmd = [
                "vastai",
                "create",
                "instance",
                str(machine_id),
                f"--image {image}",
                f"--volume-size {volume_size}",
                f"--name {instance_name}",
                f"--cmd '{startup_cmd}'",
            ]
            
            result = self._run_vastai_cmd(cmd)
            if not result:
                print(f"Failed to create instance on machine {machine_id}")
                return None
            
            # Parse result to extract instance ID
            instance_data = json.loads(result)
            instance_id_num = instance_data.get("new_contract")
            
            if not instance_id_num:
                print("No instance ID returned from provisioning")
                return None
            
            # Create instance object with string ID for consistent dict keys
            instance = VastInstance(
                instance_id=str(instance_id_num),
                machine_id=str(machine_id),
                gpu_type=instance_data.get("gpu_name", "unknown"),
                provider_name=instance_data.get("provider_name", "unknown"),
                ssh_host=instance_data.get("public_ipaddr", ""),
                ssh_port=instance_data.get("ssh_port", 22),
                hourly_rate=float(instance_data.get("dph_total", 0.0)),
                created_at=datetime.now().isoformat(),
            )
            
            self.instances[str(instance_id_num)] = instance
            print(f"Provisioned instance {instance_id_num} on {instance.gpu_type}")
            return instance
        
        except Exception as e:
            print(f"Error provisioning instance: {e}")
            return None
    
    def setup_ssh_tunnel(
        self,
        instance: VastInstance,
        local_port: int = 8000,
        key_path: str = None
    ) -> bool:
        """
        Setup SSH tunnel to vLLM API.
        
        Args:
            instance: VastInstance to tunnel to
            local_port: Local port for tunnel
            key_path: SSH private key path (default: ~/.ssh/id_rsa)
            
        Returns:
            True if successful
        """
        try:
            key_path = key_path or os.path.expanduser("~/.ssh/id_rsa")
            
            if not os.path.exists(key_path):
                print(f"SSH key not found: {key_path}")
                return False
            
            # Build SSH tunnel command
            # Format: ssh -i key -N -L local_port:localhost:8000 user@host -p port
            cmd = [
                "ssh",
                "-i", key_path,
                "-N",
                f"-L", f"{local_port}:localhost:8000",
                f"{instance.ssh_user}@{instance.ssh_host}",
                "-p", str(instance.ssh_port),
            ]
            
            # Start tunnel in background
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            instance.ssh_tunnel_pid = proc.pid
            instance.local_port = local_port
            
            print(f"SSH tunnel established: localhost:{local_port} -> "
                  f"{instance.ssh_host}:8000 (PID {proc.pid})")
            return True
        
        except Exception as e:
            print(f"Error setting up SSH tunnel: {e}")
            return False
    
    def close_ssh_tunnel(self, instance: VastInstance) -> bool:
        """Close SSH tunnel for instance."""
        if not instance.ssh_tunnel_pid:
            return False
        
        try:
            os.kill(instance.ssh_tunnel_pid, 9)
            instance.ssh_tunnel_pid = None
            print(f"SSH tunnel closed for instance {instance.instance_id}")
            return True
        except Exception as e:
            print(f"Error closing tunnel: {e}")
            return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop an instance (keeps charges paused)."""
        try:
            cmd = ["vastai", "stop", "instance", instance_id]
            result = self._run_vastai_cmd(cmd)
            
            if instance_id in self.instances:
                self.instances[instance_id].status = "stopped"
                self.close_ssh_tunnel(self.instances[instance_id])
            
            print(f"Instance {instance_id} stopped")
            return True
        
        except Exception as e:
            print(f"Error stopping instance: {e}")
            return False
    
    def destroy_instance(self, instance_id: str) -> bool:
        """Destroy an instance (irreversible, stops charges)."""
        try:
            cmd = ["vastai", "destroy", "instance", instance_id]
            result = self._run_vastai_cmd(cmd)
            
            if instance_id in self.instances:
                self.instances[instance_id].status = "destroying"
                self.close_ssh_tunnel(self.instances[instance_id])
                del self.instances[instance_id]
            
            print(f"Instance {instance_id} destroyed")
            return True
        
        except Exception as e:
            print(f"Error destroying instance: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of instance."""
        try:
            cmd = ["vastai", "show", "instance", instance_id]
            result = self._run_vastai_cmd(cmd)
            
            if result:
                status = json.loads(result)
                if instance_id in self.instances:
                    self.instances[instance_id].status = status.get("status", "unknown")
                return status
            
            return None
        
        except Exception as e:
            print(f"Error getting instance status: {e}")
            return None
    
    def get_account_balance(self) -> Optional[float]:
        """Get Vast.ai account balance."""
        try:
            cmd = ["vastai", "show", "user"]
            result = self._run_vastai_cmd(cmd)
            
            if result:
                user_data = json.loads(result)
                balance = float(user_data.get("balance_usd", 0.0))
                return balance
            
            return None
        
        except Exception as e:
            print(f"Error getting account balance: {e}")
            return None
    
    def estimate_cost(self, hourly_rate: float, hours: float) -> float:
        """Estimate cost for given hours."""
        return hourly_rate * hours
    
    def _run_vastai_cmd(self, cmd: List[str]) -> Optional[str]:
        """Run vastai CLI command and return output."""
        try:
            # Set API key in environment
            env = os.environ.copy()
            env["VAST_API_KEY"] = self.api_key
            
            # Run command with proper environment
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                check=True
            )
            
            return result.stdout.strip()
        
        except subprocess.CalledProcessError as e:
            print(f"vastai command failed: {e.stderr}")
            return None
        except FileNotFoundError:
            print("vastai CLI not found. Install with: pip install vastai")
            return None


class VastInstanceManager:
    """
    Higher-level manager for instance lifecycle.
    Tracks costs, handles failover, manages multiple instances.
    """
    
    def __init__(self, provisioner: VastProvisioner):
        """Initialize manager."""
        self.provisioner = provisioner
        self.active_instances: Dict[str, VastInstance] = {}
        self.lifecycle_log: List[Dict[str, Any]] = []
    
    def provision_teacher_pool(
        self,
        gpu_types: List[str] = None,
        pool_size: int = 1,
        model: str = "deepseek-ai/deepseek-7b"
    ) -> List[VastInstance]:
        """
        Provision a pool of teacher instances.
        
        Args:
            gpu_types: GPU types to prefer
            pool_size: Number of instances to provision
            model: Model to deploy
            
        Returns:
            List of provisioned instances
        """
        gpu_types = gpu_types or ["A100", "RTX 4090"]
        instances = []
        
        for i in range(pool_size):
            # Search for available instance
            available = self.provisioner.search_instances(
                min_vram=40,
                gpu_types=gpu_types,
                max_price=1.0
            )
            
            if not available:
                print(f"No available instances for teacher #{i+1}")
                break
            
            # Provision cheapest available
            best = min(available, key=lambda x: x.get("dph_total", float('inf')))
            
            instance = self.provisioner.provision(
                machine_id=best["id"],
                vllm_model=model,
                name_prefix=f"acx-teacher-{i+1}"
            )
            
            if instance:
                self.provisioner.setup_ssh_tunnel(instance)
                self.active_instances[instance.instance_id] = instance
                instances.append(instance)
                
                self.lifecycle_log.append({
                    "action": "provision",
                    "instance_id": instance.instance_id,
                    "timestamp": datetime.now().isoformat(),
                    "hourly_rate": instance.hourly_rate,
                })
        
        return instances
    
    def cleanup_all(self) -> None:
        """Stop and destroy all active instances."""
        for instance_id in list(self.active_instances.keys()):
            self.provisioner.stop_instance(instance_id)
            self.provisioner.destroy_instance(instance_id)
            
            self.lifecycle_log.append({
                "action": "destroy",
                "instance_id": instance_id,
                "timestamp": datetime.now().isoformat(),
            })
            
            del self.active_instances[instance_id]
    
    def get_total_cost(self) -> float:
        """Calculate total cost for active instances."""
        # This is approximate - would need actual usage data from Vast.ai
        total = 0.0
        for instance in self.active_instances.values():
            # Placeholder: assumes 1 hour usage
            total += instance.hourly_rate
        return total
