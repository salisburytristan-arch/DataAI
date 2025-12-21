"""Tests for Vast.ai provisioning and instance management."""

import unittest
import os
from unittest.mock import patch, MagicMock
from packages.core.src.vast_provisioner import (
    VastInstance,
    VastProvisioner,
    VastInstanceManager,
)


class TestVastInstance(unittest.TestCase):
    """Test VastInstance dataclass."""
    
    def test_instance_creation(self):
        """Test creating a Vast instance."""
        instance = VastInstance(
            instance_id="12345",
            machine_id="67890",
            gpu_type="A100",
            provider_name="TestProvider",
            ssh_host="1.2.3.4",
            ssh_port=22,
            hourly_rate=0.5
        )
        
        self.assertEqual(instance.instance_id, "12345")
        self.assertEqual(instance.gpu_type, "A100")
        self.assertEqual(instance.hourly_rate, 0.5)
        self.assertEqual(instance.status, "pending")
    
    def test_instance_defaults(self):
        """Test default values."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="RTX 4090",
            provider_name="Provider",
            ssh_host="host",
            ssh_port=22
        )
        
        self.assertEqual(instance.ssh_user, "root")
        self.assertEqual(instance.local_port, 8000)
        self.assertEqual(instance.ssh_tunnel_pid, None)


class TestVastProvisioner(unittest.TestCase):
    """Test Vast.ai provisioner."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.api_key = "test-api-key-12345"
        self.provisioner = VastProvisioner(api_key=self.api_key)
    
    def test_provisioner_initialization(self):
        """Test provisioner initialization."""
        self.assertEqual(self.provisioner.api_key, self.api_key)
        self.assertTrue(self.provisioner.base_url.startswith("https://api.vast.ai"))
        self.assertEqual(self.provisioner.budget_limit, 100.0)
    
    def test_provisioner_missing_api_key(self):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                VastProvisioner()
            self.assertIn("VAST_API_KEY", str(ctx.exception))
    
    def test_search_instances_builds_filter(self):
        """Test that search builds correct filter query."""
        provisioner = VastProvisioner(api_key="test-key")
        
        # Mock the vastai command execution
        with patch.object(provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = json.dumps([
                {
                    "id": 1001,
                    "gpu_name": "A100",
                    "dph_total": 0.5,
                    "inet_up": 150,
                }
            ])
            
            results = provisioner.search_instances(min_vram=40, max_price=1.0)
            
            # Verify command was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            
            # Check that filter contains key components
            cmd_str = " ".join(call_args)
            self.assertIn("search", cmd_str)
            self.assertIn("gpu_ram", cmd_str)
            self.assertIn("40", cmd_str)  # min_vram
    
    def test_provision_instance(self):
        """Test instance provisioning."""
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = json.dumps({
                "new_contract": 9999,
                "gpu_name": "RTX 4090",
                "provider_name": "TestProvider",
                "public_ipaddr": "1.2.3.4",
                "ssh_port": 22,
                "dph_total": 0.4,
            })
            
            instance = self.provisioner.provision(
                machine_id=5000,
                vllm_model="deepseek-ai/deepseek-7b"
            )
            
            self.assertIsNotNone(instance)
            self.assertEqual(instance.instance_id, "9999")
            self.assertEqual(instance.gpu_type, "RTX 4090")
            self.assertEqual(instance.ssh_host, "1.2.3.4")
            self.assertEqual(instance.hourly_rate, 0.4)
            
            # Check instance stored (string key "9999" in dict)
            self.assertIn("9999", self.provisioner.instances)
    
    def test_provision_instance_failure(self):
        """Test provisioning failure handling."""
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = None  # Simulate failure
            
            instance = self.provisioner.provision(machine_id=5000)
            
            self.assertIsNone(instance)
    
    def test_setup_ssh_tunnel(self):
        """Test SSH tunnel setup."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        
        # Create mock SSH key
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process
                
                result = self.provisioner.setup_ssh_tunnel(instance, local_port=8000)
                
                self.assertTrue(result)
                self.assertEqual(instance.ssh_tunnel_pid, 12345)
                self.assertEqual(instance.local_port, 8000)
                mock_popen.assert_called_once()
    
    def test_setup_ssh_tunnel_missing_key(self):
        """Test SSH tunnel setup with missing key."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False  # Key doesn't exist
            
            result = self.provisioner.setup_ssh_tunnel(instance)
            
            self.assertFalse(result)
            self.assertIsNone(instance.ssh_tunnel_pid)
    
    def test_close_ssh_tunnel(self):
        """Test closing SSH tunnel."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22,
            ssh_tunnel_pid=12345
        )
        
        with patch("os.kill") as mock_kill:
            result = self.provisioner.close_ssh_tunnel(instance)
            
            self.assertTrue(result)
            self.assertIsNone(instance.ssh_tunnel_pid)
            mock_kill.assert_called_once_with(12345, 9)
    
    def test_close_ssh_tunnel_no_pid(self):
        """Test closing tunnel when no tunnel exists."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        
        result = self.provisioner.close_ssh_tunnel(instance)
        self.assertFalse(result)
    
    def test_stop_instance(self):
        """Test stopping instance."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        self.provisioner.instances["123"] = instance
        
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = "{}"
            
            result = self.provisioner.stop_instance("123")
            
            self.assertTrue(result)
            self.assertEqual(instance.status, "stopped")
    
    def test_destroy_instance(self):
        """Test destroying instance."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        self.provisioner.instances["123"] = instance
        
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = "{}"
            
            result = self.provisioner.destroy_instance("123")
            
            self.assertTrue(result)
            self.assertNotIn("123", self.provisioner.instances)
    
    def test_get_instance_status(self):
        """Test getting instance status."""
        instance = VastInstance(
            instance_id="123",
            machine_id="456",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.2.3.4",
            ssh_port=22
        )
        self.provisioner.instances["123"] = instance
        
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = json.dumps({"status": "running"})
            
            status = self.provisioner.get_instance_status("123")
            
            self.assertIsNotNone(status)
            self.assertEqual(status["status"], "running")
            self.assertEqual(instance.status, "running")
    
    def test_get_account_balance(self):
        """Test getting account balance."""
        with patch.object(self.provisioner, "_run_vastai_cmd") as mock_run:
            mock_run.return_value = json.dumps({"balance_usd": 42.50})
            
            balance = self.provisioner.get_account_balance()
            
            self.assertEqual(balance, 42.50)
    
    def test_estimate_cost(self):
        """Test cost estimation."""
        cost = self.provisioner.estimate_cost(hourly_rate=0.5, hours=10)
        self.assertEqual(cost, 5.0)


class TestVastInstanceManager(unittest.TestCase):
    """Test Vast instance manager."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.provisioner = VastProvisioner(api_key="test-key")
        self.manager = VastInstanceManager(self.provisioner)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager.provisioner)
        self.assertEqual(len(self.manager.active_instances), 0)
        self.assertEqual(len(self.manager.lifecycle_log), 0)
    
    def test_provision_teacher_pool(self):
        """Test provisioning multiple teacher instances."""
        instance1 = VastInstance(
            instance_id="101",
            machine_id="1001",
            gpu_type="A100",
            provider_name="Provider1",
            ssh_host="1.1.1.1",
            ssh_port=22
        )
        
        instance2 = VastInstance(
            instance_id="102",
            machine_id="1002",
            gpu_type="A100",
            provider_name="Provider2",
            ssh_host="2.2.2.2",
            ssh_port=22
        )
        
        with patch.object(self.provisioner, "search_instances") as mock_search:
            with patch.object(self.provisioner, "provision") as mock_provision:
                with patch.object(self.provisioner, "setup_ssh_tunnel") as mock_tunnel:
                    
                    # Setup side effects
                    mock_search.side_effect = [
                        [{"id": 1001, "dph_total": 0.5}],
                        [{"id": 1002, "dph_total": 0.5}],
                    ]
                    mock_provision.side_effect = [instance1, instance2]
                    mock_tunnel.return_value = True
                    
                    instances = self.manager.provision_teacher_pool(pool_size=2)
                    
                    self.assertEqual(len(instances), 2)
                    self.assertEqual(len(self.manager.active_instances), 2)
                    self.assertGreater(len(self.manager.lifecycle_log), 0)
    
    def test_cleanup_all(self):
        """Test cleaning up all instances."""
        instance1 = VastInstance(
            instance_id="101",
            machine_id="1001",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.1.1.1",
            ssh_port=22,
            ssh_tunnel_pid=1234
        )
        instance2 = VastInstance(
            instance_id="102",
            machine_id="1002",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="2.2.2.2",
            ssh_port=22
        )
        
        self.manager.active_instances["101"] = instance1
        self.manager.active_instances["102"] = instance2
        
        with patch.object(self.provisioner, "stop_instance") as mock_stop:
            with patch.object(self.provisioner, "destroy_instance") as mock_destroy:
                
                self.manager.cleanup_all()
                
                self.assertEqual(len(self.manager.active_instances), 0)
                self.assertEqual(mock_stop.call_count, 2)
                self.assertEqual(mock_destroy.call_count, 2)
    
    def test_get_total_cost(self):
        """Test calculating total cost."""
        instance1 = VastInstance(
            instance_id="101",
            machine_id="1001",
            gpu_type="A100",
            provider_name="Provider",
            ssh_host="1.1.1.1",
            ssh_port=22,
            hourly_rate=0.5
        )
        instance2 = VastInstance(
            instance_id="102",
            machine_id="1002",
            gpu_type="RTX 4090",
            provider_name="Provider",
            ssh_host="2.2.2.2",
            ssh_port=22,
            hourly_rate=0.3
        )
        
        self.manager.active_instances["101"] = instance1
        self.manager.active_instances["102"] = instance2
        
        total_cost = self.manager.get_total_cost()
        self.assertEqual(total_cost, 0.8)


import json  # Add at top if not already there

if __name__ == "__main__":
    unittest.main()
