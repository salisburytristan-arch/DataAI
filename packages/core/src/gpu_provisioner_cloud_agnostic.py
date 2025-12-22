"""
Cloud-Agnostic GPU Provisioner: Vast.ai, RunPod, AWS SageMaker

Abstracts GPU provisioning across multiple cloud providers.
Enterprise buyers can use their preferred cloud (no lock-in to Vast.ai).

Abstract Pattern:
  GPUProvider (base class)
  ├── VastAiProvider (peer-to-peer, cheapest)
  ├── RunPodProvider (community-friendly, middle ground)
  └── AWSProvider (enterprise, highest trust)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import json
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class CloudProvider(Enum):
    """Supported cloud GPU providers"""
    VAST_AI = "vast_ai"
    RUNPOD = "runpod"
    AWS_SAGEMAKER = "aws_sagemaker"


class GPUType(Enum):
    """GPU types available across clouds"""
    A100_80GB = "nvidia-a100-80gb"
    A100_40GB = "nvidia-a100-40gb"
    H100 = "nvidia-h100"
    RTX4090 = "nvidia-rtx4090"
    L40S = "nvidia-l40s"
    V100 = "nvidia-v100"


@dataclass
class GPUInstance:
    """Standardized GPU instance across all providers"""
    provider: CloudProvider
    instance_id: str
    gpu_type: GPUType
    gpu_count: int
    vram_per_gpu_gb: int
    hourly_rate_usd: float
    region: str
    status: str = "available"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def total_vram_gb(self) -> int:
        return self.gpu_count * self.vram_per_gpu_gb


@dataclass
class ProvisioningResult:
    """Result of provisioning a GPU instance"""
    success: bool
    instance: Optional[GPUInstance] = None
    ssh_host: Optional[str] = None
    ssh_port: int = 22
    ssh_key: Optional[str] = None
    error: Optional[str] = None
    provider_request_id: str = ""


# ============================================================================
# Abstract Base Class
# ============================================================================

class GPUProvider(ABC):
    """Abstract interface for GPU provisioning"""
    
    def __init__(self, provider_type: CloudProvider, api_key: Optional[str] = None):
        self.provider_type = provider_type
        self.api_key = api_key
        self.active_instances: Dict[str, GPUInstance] = {}
    
    @abstractmethod
    def list_available(self, gpu_type: Optional[GPUType] = None) -> List[GPUInstance]:
        """List available GPU instances"""
        pass
    
    @abstractmethod
    def provision(self, gpu_type: GPUType, gpu_count: int = 1, 
                 duration_hours: int = 1) -> ProvisioningResult:
        """Provision a GPU instance"""
        pass
    
    @abstractmethod
    def terminate(self, instance_id: str) -> bool:
        """Terminate a GPU instance"""
        pass
    
    @abstractmethod
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get status of instance"""
        pass
    
    @abstractmethod
    def get_connection_info(self, instance_id: str) -> Dict[str, str]:
        """Get SSH connection info for instance"""
        pass
    
    def verify_connectivity(self, instance: GPUInstance) -> bool:
        """Verify we can connect to the instance"""
        # Override in subclasses for actual verification
        return True


# ============================================================================
# Vast.ai Provider
# ============================================================================

class VastAiProvider(GPUProvider):
    """
    Vast.ai: Peer-to-peer GPU marketplace
    - Cheapest option
    - Good for: Cost-sensitive workloads, non-critical training
    - Risk: Less reliable than centralized providers
    """
    
    def __init__(self, api_key: str):
        super().__init__(CloudProvider.VAST_AI, api_key)
        self.base_url = "https://api.vast.ai/api/v0"
        self.session = self._init_session()
    
    def _init_session(self):
        """Initialize API session"""
        try:
            import requests
            session = requests.Session()
            session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            return session
        except ImportError:
            logger.warning("requests library required for Vast.ai")
            return None
    
    def list_available(self, gpu_type: Optional[GPUType] = None) -> List[GPUInstance]:
        """Get available Vast.ai instances"""
        if not self.session:
            return []
        
        try:
            # Vast.ai API call
            response = self.session.get(f"{self.base_url}/instances/", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            instances = []
            for item in data.get("instances", [])[:10]:  # Limit to 10
                if gpu_type and self._parse_gpu_type(item) != gpu_type:
                    continue
                
                instances.append(GPUInstance(
                    provider=CloudProvider.VAST_AI,
                    instance_id=str(item["id"]),
                    gpu_type=self._parse_gpu_type(item),
                    gpu_count=item.get("gpu_count", 1),
                    vram_per_gpu_gb=item.get("gpu_ram") // item.get("gpu_count", 1) // 1024,
                    hourly_rate_usd=item.get("dph", 0.0),
                    region=item.get("host_country", "unknown")
                ))
            
            logger.info(f"Found {len(instances)} Vast.ai instances")
            return instances
        
        except Exception as e:
            logger.error(f"Failed to fetch Vast.ai instances: {e}")
            return []
    
    def provision(self, gpu_type: GPUType, gpu_count: int = 1,
                 duration_hours: int = 1) -> ProvisioningResult:
        """Provision on Vast.ai"""
        try:
            # Find cheapest matching instance
            available = [i for i in self.list_available(gpu_type) if i.gpu_count >= gpu_count]
            
            if not available:
                return ProvisioningResult(
                    success=False,
                    error=f"No {gpu_type.value} instances available"
                )
            
            cheapest = min(available, key=lambda x: x.hourly_rate_usd)
            
            # Provision via API
            payload = {
                "instance_id": cheapest.instance_id,
                "duration": duration_hours * 3600,
                "image": "nvidia/cuda:12.1.0-devel-ubuntu22.04"
            }
            
            response = self.session.post(
                f"{self.base_url}/instances/launch/",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            instance = GPUInstance(
                provider=CloudProvider.VAST_AI,
                instance_id=result["instance_id"],
                gpu_type=gpu_type,
                gpu_count=gpu_count,
                vram_per_gpu_gb=cheapest.vram_per_gpu_gb,
                hourly_rate_usd=cheapest.hourly_rate_usd,
                region=cheapest.region
            )
            
            self.active_instances[instance.instance_id] = instance
            
            return ProvisioningResult(
                success=True,
                instance=instance,
                ssh_host=result.get("public_ip"),
                ssh_port=int(result.get("ssh_port", 22)),
                provider_request_id=instance.instance_id
            )
        
        except Exception as e:
            logger.error(f"Vast.ai provisioning failed: {e}")
            return ProvisioningResult(
                success=False,
                error=str(e)
            )
    
    def terminate(self, instance_id: str) -> bool:
        """Terminate Vast.ai instance"""
        try:
            self.session.post(
                f"{self.base_url}/instances/{instance_id}/terminate/",
                timeout=10
            )
            self.active_instances.pop(instance_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed to terminate {instance_id}: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get instance status"""
        try:
            response = self.session.get(f"{self.base_url}/instances/{instance_id}/", timeout=10)
            return response.json()
        except:
            return {}
    
    def get_connection_info(self, instance_id: str) -> Dict[str, str]:
        """Get connection info"""
        status = self.get_instance_status(instance_id)
        return {
            "host": status.get("public_ip", "unknown"),
            "port": str(status.get("ssh_port", 22)),
            "user": "root"
        }
    
    @staticmethod
    def _parse_gpu_type(item: Dict) -> GPUType:
        """Parse Vast.ai GPU type to standard type"""
        gpu_name = item.get("gpu_name", "").lower()
        if "a100" in gpu_name:
            return GPUType.A100_80GB
        elif "h100" in gpu_name:
            return GPUType.H100
        elif "rtx4090" in gpu_name or "4090" in gpu_name:
            return GPUType.RTX4090
        else:
            return GPUType.V100


# ============================================================================
# RunPod Provider
# ============================================================================

class RunPodProvider(GPUProvider):
    """
    RunPod: Community-friendly GPU platform
    - Good price/performance balance
    - Good for: Most training workloads, community support
    - Advantage: Simpler API than Vast, better reliability
    """
    
    def __init__(self, api_key: str):
        super().__init__(CloudProvider.RUNPOD, api_key)
        self.base_url = "https://api.runpod.io/graphql"
        self.session = self._init_session()
    
    def _init_session(self):
        """Initialize API session"""
        try:
            import requests
            session = requests.Session()
            return session
        except ImportError:
            logger.warning("requests library required for RunPod")
            return None
    
    def list_available(self, gpu_type: Optional[GPUType] = None) -> List[GPUInstance]:
        """Get available RunPod pods"""
        if not self.session:
            return []
        
        try:
            query = """
            query {
              podRentInterfaces {
                edges {
                  node {
                    id
                    gpuCount
                    gpuName
                    minBidPerGpu
                    podHostId
                  }
                }
              }
            }
            """
            
            response = self.session.post(
                self.base_url,
                json={"query": query},
                headers={"api_key": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            instances = []
            for edge in data.get("data", {}).get("podRentInterfaces", {}).get("edges", [])[:10]:
                node = edge["node"]
                gpu_type_parsed = self._parse_gpu_type(node["gpuName"])
                
                if gpu_type and gpu_type_parsed != gpu_type:
                    continue
                
                instances.append(GPUInstance(
                    provider=CloudProvider.RUNPOD,
                    instance_id=node["id"],
                    gpu_type=gpu_type_parsed,
                    gpu_count=node.get("gpuCount", 1),
                    vram_per_gpu_gb=self._get_vram(gpu_type_parsed),
                    hourly_rate_usd=node.get("minBidPerGpu", 0.0),
                    region="runpod-global"
                ))
            
            logger.info(f"Found {len(instances)} RunPod instances")
            return instances
        
        except Exception as e:
            logger.error(f"Failed to fetch RunPod instances: {e}")
            return []
    
    def provision(self, gpu_type: GPUType, gpu_count: int = 1,
                 duration_hours: int = 1) -> ProvisioningResult:
        """Provision on RunPod"""
        try:
            available = [i for i in self.list_available(gpu_type) if i.gpu_count >= gpu_count]
            
            if not available:
                return ProvisioningResult(
                    success=False,
                    error=f"No {gpu_type.value} instances available on RunPod"
                )
            
            cheapest = min(available, key=lambda x: x.hourly_rate_usd)
            
            # Provision mutation
            mutation = f"""
            mutation {{
              podRentInterfaces(input: {{
                podHostId: "{cheapest.instance_id}"
                gpuCount: {gpu_count}
                volumeInGb: 50
                containerDiskInGb: 50
                minMemoryInGb: 32
                gpuCountType: "INDIVIDUAL"
                storageAmount: 1
                storageSolution: "VOLUME"
                cloudType: "COMMUNITY"
                gpuId: "{gpu_type.value}"
              }}) {{
                podId
                containerStatus
                desiredStatus
              }}
            }}
            """
            
            response = self.session.post(
                self.base_url,
                json={"query": mutation},
                headers={"api_key": self.api_key},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            pod_data = data.get("data", {}).get("podRentInterfaces", {})
            
            instance = GPUInstance(
                provider=CloudProvider.RUNPOD,
                instance_id=pod_data.get("podId"),
                gpu_type=gpu_type,
                gpu_count=gpu_count,
                vram_per_gpu_gb=self._get_vram(gpu_type),
                hourly_rate_usd=cheapest.hourly_rate_usd,
                region="runpod-global"
            )
            
            self.active_instances[instance.instance_id] = instance
            
            return ProvisioningResult(
                success=True,
                instance=instance,
                ssh_host=f"{instance.instance_id}-ssh.runpod.io",
                ssh_port=22,
                provider_request_id=instance.instance_id
            )
        
        except Exception as e:
            logger.error(f"RunPod provisioning failed: {e}")
            return ProvisioningResult(
                success=False,
                error=str(e)
            )
    
    def terminate(self, instance_id: str) -> bool:
        """Terminate RunPod pod"""
        try:
            mutation = f"""
            mutation {{
              podStop(input: {{podId: "{instance_id}"}}) {{
                ok
              }}
            }}
            """
            
            self.session.post(
                self.base_url,
                json={"query": mutation},
                headers={"api_key": self.api_key},
                timeout=10
            )
            self.active_instances.pop(instance_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed to terminate {instance_id}: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get pod status"""
        try:
            query = f"""
            query {{
              pod(input: {{podId: "{instance_id}"}}) {{
                id
                desiredStatus
                containerStatus
                containerDiskInGb
                volumeInGb
              }}
            }}
            """
            
            response = self.session.post(
                self.base_url,
                json={"query": query},
                headers={"api_key": self.api_key},
                timeout=10
            )
            return response.json().get("data", {}).get("pod", {})
        except:
            return {}
    
    def get_connection_info(self, instance_id: str) -> Dict[str, str]:
        """Get connection info"""
        return {
            "host": f"{instance_id}-ssh.runpod.io",
            "port": "22",
            "user": "root"
        }
    
    @staticmethod
    def _parse_gpu_type(gpu_name: str) -> GPUType:
        """Parse RunPod GPU name"""
        gpu_name = gpu_name.lower()
        if "a100" in gpu_name:
            return GPUType.A100_80GB
        elif "h100" in gpu_name:
            return GPUType.H100
        elif "4090" in gpu_name:
            return GPUType.RTX4090
        elif "l40s" in gpu_name:
            return GPUType.L40S
        else:
            return GPUType.V100
    
    @staticmethod
    def _get_vram(gpu_type: GPUType) -> int:
        """Get VRAM in GB for GPU type"""
        vram_map = {
            GPUType.A100_80GB: 80,
            GPUType.A100_40GB: 40,
            GPUType.H100: 80,
            GPUType.RTX4090: 24,
            GPUType.L40S: 48,
            GPUType.V100: 32,
        }
        return vram_map.get(gpu_type, 32)


# ============================================================================
# AWS SageMaker Provider
# ============================================================================

class AWSProvider(GPUProvider):
    """
    AWS SageMaker + EC2: Enterprise GPU provision
    - Most reliable, highest SLA
    - Good for: Production workloads, enterprise compliance
    - Advantage: Integration with AWS services, VPC/security
    """
    
    def __init__(self, api_key: str, secret_key: str, region: str = "us-east-1"):
        super().__init__(CloudProvider.AWS_SAGEMAKER, api_key)
        self.secret_key = secret_key
        self.region = region
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize AWS client"""
        try:
            import boto3
            return boto3.client("ec2", region_name=self.region)
        except ImportError:
            logger.warning("boto3 required for AWS: pip install boto3")
            return None
    
    def list_available(self, gpu_type: Optional[GPUType] = None) -> List[GPUInstance]:
        """Get available AWS instance types"""
        if not self.client:
            return []
        
        try:
            # AWS on-demand instances
            instance_types = [
                ("p3.2xlarge", GPUType.V100, 8, 16),
                ("p3.8xlarge", GPUType.V100, 32, 16),
                ("g4dn.xlarge", GPUType.RTX4090, 1, 24),
                ("g4dn.12xlarge", GPUType.RTX4090, 8, 24),
            ]
            
            instances = []
            for itype, gtype, vram, count in instance_types:
                if gpu_type and gtype != gpu_type:
                    continue
                
                # Get pricing
                pricing_response = self.client.describe_reserved_instances_offerings(
                    Filters=[{"Name": "instance-type", "Values": [itype]}]
                )
                
                hourly_rate = 5.0  # Placeholder, would fetch from AWS pricing API
                
                instances.append(GPUInstance(
                    provider=CloudProvider.AWS_SAGEMAKER,
                    instance_id=itype,
                    gpu_type=gtype,
                    gpu_count=count,
                    vram_per_gpu_gb=vram,
                    hourly_rate_usd=hourly_rate,
                    region=self.region
                ))
            
            logger.info(f"Found {len(instances)} AWS instance types")
            return instances
        
        except Exception as e:
            logger.error(f"Failed to fetch AWS instances: {e}")
            return []
    
    def provision(self, gpu_type: GPUType, gpu_count: int = 1,
                 duration_hours: int = 1) -> ProvisioningResult:
        """Launch EC2 instance with GPU"""
        if not self.client:
            return ProvisioningResult(success=False, error="AWS client not initialized")
        
        try:
            # Find matching instance type
            available = [i for i in self.list_available(gpu_type) if i.gpu_count >= gpu_count]
            
            if not available:
                return ProvisioningResult(
                    success=False,
                    error=f"No {gpu_type.value} instances available in {self.region}"
                )
            
            instance_type = available[0].instance_id
            
            # Launch instance
            response = self.client.run_instances(
                ImageId="ami-0c55b159cbfafe1f0",  # Deep Learning AMI
                MinCount=1,
                MaxCount=1,
                InstanceType=instance_type,
                SecurityGroupIds=["sg-0123456789abcdef0"],  # Your security group
                KeyName="your-key-pair"
            )
            
            aws_instance = response["Instances"][0]
            
            instance = GPUInstance(
                provider=CloudProvider.AWS_SAGEMAKER,
                instance_id=aws_instance["InstanceId"],
                gpu_type=gpu_type,
                gpu_count=gpu_count,
                vram_per_gpu_gb=available[0].vram_per_gpu_gb,
                hourly_rate_usd=available[0].hourly_rate_usd,
                region=self.region
            )
            
            self.active_instances[instance.instance_id] = instance
            
            return ProvisioningResult(
                success=True,
                instance=instance,
                ssh_host=aws_instance.get("PublicIpAddress", ""),
                ssh_port=22,
                provider_request_id=instance.instance_id
            )
        
        except Exception as e:
            logger.error(f"AWS provisioning failed: {e}")
            return ProvisioningResult(
                success=False,
                error=str(e)
            )
    
    def terminate(self, instance_id: str) -> bool:
        """Terminate EC2 instance"""
        try:
            self.client.terminate_instances(InstanceIds=[instance_id])
            self.active_instances.pop(instance_id, None)
            return True
        except Exception as e:
            logger.error(f"Failed to terminate {instance_id}: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get instance status"""
        try:
            response = self.client.describe_instances(InstanceIds=[instance_id])
            return response["Reservations"][0]["Instances"][0]
        except:
            return {}
    
    def get_connection_info(self, instance_id: str) -> Dict[str, str]:
        """Get connection info"""
        status = self.get_instance_status(instance_id)
        return {
            "host": status.get("PublicIpAddress", ""),
            "port": "22",
            "user": "ec2-user"
        }


# ============================================================================
# Provider Factory
# ============================================================================

class GPUProviderFactory:
    """Factory for creating GPU providers"""
    
    @staticmethod
    def create(provider_type: CloudProvider, **kwargs) -> GPUProvider:
        """
        Create provider instance.
        
        Args:
            provider_type: Which cloud provider
            **kwargs: Provider-specific arguments (api_key, region, etc.)
        
        Returns:
            GPUProvider instance
        """
        if provider_type == CloudProvider.VAST_AI:
            return VastAiProvider(kwargs.get("api_key"))
        elif provider_type == CloudProvider.RUNPOD:
            return RunPodProvider(kwargs.get("api_key"))
        elif provider_type == CloudProvider.AWS_SAGEMAKER:
            return AWSProvider(
                kwargs.get("api_key"),
                kwargs.get("secret_key"),
                kwargs.get("region", "us-east-1")
            )
        else:
            raise ValueError(f"Unknown provider: {provider_type}")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Use any provider - no lock-in!
    
    # Option 1: Cheap option for dev
    vast = VastAiProvider(api_key="your-vast-api-key")
    result = vast.provision(gpu_type=GPUType.RTX4090, gpu_count=1, duration_hours=4)
    
    # Option 2: Community-friendly
    runpod = RunPodProvider(api_key="your-runpod-api-key")
    
    # Option 3: Enterprise
    aws = AWSProvider(
        api_key="your-aws-access-key",
        secret_key="your-aws-secret-key",
        region="us-west-2"
    )
    
    # Or use factory
    provider = GPUProviderFactory.create(
        CloudProvider.RUNPOD,
        api_key="your-runpod-api-key"
    )
    
    # Get available instances
    available = provider.list_available(gpu_type=GPUType.A100_80GB)
    print(f"Available instances: {len(available)}")
    
    for inst in available:
        print(f"  {inst.gpu_type.value} x{inst.gpu_count} @ ${inst.hourly_rate_usd}/hr")
    
    # Provision
    if available:
        result = provider.provision(GPUType.A100_80GB, gpu_count=1, duration_hours=8)
        if result.success:
            print(f"✅ Provisioned: {result.instance.instance_id}")
            print(f"   SSH: {result.ssh_host}:{result.ssh_port}")
