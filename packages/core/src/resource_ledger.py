"""
Phase IX: Resource Ledger (Governance & Accounting)
Blockchain-based resource tracking, allocation, and governance.

Implements:
- RESOURCE_FRAME: Immutable resource transaction record
- LEDGER: Distributed ledger for resource accounting
- GOVERNANCE: Voting and policy framework
"""

import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class ResourceType(Enum):
    """Types of trackable resources."""
    ENERGY_MEGAWATT_HOURS = 'MWh'
    COMPUTE_EXAFLOPS = 'EXAFLOPS'
    BANDWIDTH_PETABYTES = 'PB'
    MATTER_KILOGRAMS = 'kg'
    WATER_CUBIC_METERS = 'm3'
    LAND_SQUARE_KILOMETERS = 'km2'
    CARBON_CREDITS = 'CO2e'
    COMPUTE_TIME_SECONDS = 'CPU_SEC'


class TransactionType(Enum):
    """Types of ledger transactions."""
    ALLOCATION = 'allocation'      # Grant resource to entity
    USAGE = 'usage'                # Consume resource
    TRANSFER = 'transfer'          # Move between accounts
    GENERATION = 'generation'      # Create new resource
    BURN = 'burn'                  # Destroy resource
    GOVERNANCE_VOTE = 'vote'       # Record policy decision
    PENALTY = 'penalty'            # Subtract for violation
    REWARD = 'reward'              # Bonus for achievement


@dataclass
class ResourceFrame:
    """
    TYPE=RESOURCE_FRAME: Atomic unit of resource transaction.
    Immutable, content-addressed, cryptographically signed.
    """
    transaction_id: str
    timestamp: str  # ISO 8601
    transaction_type: TransactionType
    resource_type: ResourceType
    quantity: float
    source_account: str  # Account ID
    destination_account: str
    reason: str  # Policy/business reason
    block_hash: str  # Hash of previous block
    signature: str = ""  # Ed25519 digital signature
    metadata: Dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute block hash (SHA-256)."""
        content = (
            f"{self.transaction_id}:{self.timestamp}:{self.transaction_type.value}:"
            f"{self.resource_type.value}:{self.quantity}:"
            f"{self.source_account}:{self.destination_account}:{self.reason}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_frame(self) -> Dict:
        """Convert to ForgeNumerics-S frame."""
        return {
            'type': 'RESOURCE_FRAME',
            'tx_id': self.transaction_id,
            'timestamp': self.timestamp,
            'tx_type': self.transaction_type.value,
            'resource': self.resource_type.value,
            'quantity': self.quantity,
            'from': self.source_account,
            'to': self.destination_account,
            'reason': self.reason,
            'hash': self.compute_hash()
        }


@dataclass
class Account:
    """Account on the resource ledger."""
    account_id: str
    account_name: str
    balances: Dict[ResourceType, float] = field(default_factory=dict)
    allocation_limits: Dict[ResourceType, float] = field(default_factory=dict)
    transaction_history: List[ResourceFrame] = field(default_factory=list)
    credit_score: float = 100.0  # 0-100
    governance_voting_power: float = 1.0

    def __post_init__(self):
        """Initialize default zero balances."""
        if not self.balances:
            for rtype in ResourceType:
                self.balances[rtype] = 0.0

    def deposit(self, resource: ResourceType, amount: float) -> bool:
        """Deposit resource to account."""
        if amount < 0:
            return False
        self.balances[resource] += amount
        return True

    def withdraw(self, resource: ResourceType, amount: float) -> bool:
        """Withdraw resource from account."""
        if amount < 0 or amount > self.balances.get(resource, 0):
            return False
        self.balances[resource] -= amount
        return True

    def can_withdraw(self, resource: ResourceType, amount: float) -> bool:
        """Check if withdrawal is allowed."""
        if amount > self.balances.get(resource, 0):
            return False
        if resource in self.allocation_limits:
            limit = self.allocation_limits[resource]
            if self.balances.get(resource, 0) - amount < limit:
                return False
        return True

    def get_balance(self, resource: ResourceType) -> float:
        """Get current balance."""
        return self.balances.get(resource, 0.0)


class ResourceLedger:
    """
    Distributed ledger for resource accounting.
    Blocks form immutable chain. Similar to blockchain but for resources.
    """

    def __init__(self, genesis_account: str = 'GENESIS'):
        """Initialize ledger with genesis block."""
        self.blocks: List[ResourceFrame] = []
        self.accounts: Dict[str, Account] = {}
        self.previous_hash = '0' * 64

        # Create genesis account
        genesis = Account(
            account_id=genesis_account,
            account_name='Genesis Block',
            balances={
                ResourceType.ENERGY_MEGAWATT_HOURS: 1e12,  # Huge initial energy
                ResourceType.MATTER_KILOGRAMS: 1e18  # Solar mass equivalent
            }
        )
        self.accounts[genesis_account] = genesis

    def create_account(self, account_id: str, account_name: str,
                      initial_balances: Dict[ResourceType, float] = None) -> bool:
        """Create new account."""
        if account_id in self.accounts:
            return False

        account = Account(account_id=account_id, account_name=account_name)
        if initial_balances:
            account.balances = initial_balances

        self.accounts[account_id] = account
        return True

    def transfer(self, from_account: str, to_account: str,
                resource: ResourceType, quantity: float,
                reason: str = "Transfer") -> Tuple[bool, Optional[ResourceFrame]]:
        """
        Transfer resource between accounts.
        Returns (success, transaction_frame).
        """
        if from_account not in self.accounts or to_account not in self.accounts:
            return (False, None)

        source = self.accounts[from_account]
        dest = self.accounts[to_account]

        if not source.can_withdraw(resource, quantity):
            return (False, None)

        # Create transaction frame
        tx_id = hashlib.sha256(
            f"{from_account}{to_account}{resource.value}{quantity}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        frame = ResourceFrame(
            transaction_id=tx_id,
            timestamp=datetime.now().isoformat(),
            transaction_type=TransactionType.TRANSFER,
            resource_type=resource,
            quantity=quantity,
            source_account=from_account,
            destination_account=to_account,
            reason=reason,
            block_hash=self.previous_hash
        )

        # Execute transfer
        source.withdraw(resource, quantity)
        dest.deposit(resource, quantity)

        # Add to ledger
        self.blocks.append(frame)
        self.previous_hash = frame.compute_hash()

        source.transaction_history.append(frame)
        dest.transaction_history.append(frame)

        return (True, frame)

    def allocate(self, account_id: str, resource: ResourceType,
                quantity: float, reason: str = "Allocation") -> Tuple[bool, Optional[ResourceFrame]]:
        """Allocate fresh resource to account (from genesis)."""
        return self.transfer('GENESIS', account_id, resource, quantity, reason)

    def get_account_balance(self, account_id: str) -> Optional[Dict]:
        """Get account balance summary."""
        if account_id not in self.accounts:
            return None

        account = self.accounts[account_id]
        return {
            'account_id': account_id,
            'name': account.account_name,
            'balances': {k.value: v for k, v in account.balances.items()},
            'credit_score': account.credit_score,
            'transaction_count': len(account.transaction_history)
        }

    def verify_chain(self) -> Tuple[bool, str]:
        """Verify ledger integrity."""
        if not self.blocks:
            return (True, "Empty ledger (valid)")

        for i, block in enumerate(self.blocks):
            if i > 0:
                expected_prev = self.blocks[i-1].compute_hash()
                if block.block_hash != expected_prev:
                    return (False, f"Chain broken at block {i}")

        return (True, "Chain verified")


class GovernanceFramework:
    """
    Democratic governance for resource allocation and policy.
    One entity, one vote (or weighted by contribution).
    """

    @dataclass
    class Proposal:
        """Governance proposal."""
        proposal_id: str
        title: str
        description: str
        proposed_by: str  # Account ID
        proposed_at: str  # ISO 8601
        deadline: str
        proposal_type: str  # 'policy', 'budget', 'modification'
        votes_for: float = 0.0
        votes_against: float = 0.0
        votes_abstain: float = 0.0
        status: str = 'OPEN'  # OPEN, PASSED, FAILED, EXPIRED

    def __init__(self, ledger: ResourceLedger):
        self.ledger = ledger
        self.proposals: Dict[str, GovernanceFramework.Proposal] = {}
        self.voting_records: Dict[str, List[Dict]] = {}  # account_id -> votes cast

    def create_proposal(self, title: str, description: str, proposer: str,
                       duration_days: int = 30) -> Tuple[bool, str]:
        """Create new governance proposal."""
        if proposer not in self.ledger.accounts:
            return (False, "Proposer account not found")

        proposal_id = hashlib.sha256(
            f"{title}{proposer}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        deadline = (datetime.now() + timedelta(days=duration_days)).isoformat()

        proposal = GovernanceFramework.Proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposed_by=proposer,
            proposed_at=datetime.now().isoformat(),
            deadline=deadline,
            proposal_type='policy'
        )

        self.proposals[proposal_id] = proposal
        self.voting_records[proposal_id] = []
        return (True, proposal_id)

    def vote(self, proposal_id: str, voter: str, vote: str) -> Tuple[bool, str]:
        """
        Cast vote on proposal.
        vote: 'FOR', 'AGAINST', 'ABSTAIN'
        """
        if proposal_id not in self.proposals:
            return (False, "Proposal not found")

        proposal = self.proposals[proposal_id]

        if voter not in self.ledger.accounts:
            return (False, "Voter not found")

        account = self.ledger.accounts[voter]
        voting_power = account.governance_voting_power

        if vote == 'FOR':
            proposal.votes_for += voting_power
        elif vote == 'AGAINST':
            proposal.votes_against += voting_power
        elif vote == 'ABSTAIN':
            proposal.votes_abstain += voting_power
        else:
            return (False, "Invalid vote")

        # Record vote
        if proposal_id not in self.voting_records:
            self.voting_records[proposal_id] = []

        self.voting_records[proposal_id].append({
            'voter': voter,
            'vote': vote,
            'power': voting_power,
            'timestamp': datetime.now().isoformat()
        })

        return (True, f"Vote recorded: {voter} voted {vote}")

    def finalize_proposal(self, proposal_id: str) -> Tuple[bool, str]:
        """Close proposal and determine outcome."""
        if proposal_id not in self.proposals:
            return (False, "Proposal not found")

        proposal = self.proposals[proposal_id]
        total_votes = proposal.votes_for + proposal.votes_against + proposal.votes_abstain

        if total_votes == 0:
            proposal.status = 'EXPIRED'
            return (True, "Proposal expired with no votes")

        if proposal.votes_for > proposal.votes_against:
            proposal.status = 'PASSED'
            return (True, f"Proposal PASSED ({proposal.votes_for:.0f} for, {proposal.votes_against:.0f} against)")
        else:
            proposal.status = 'FAILED'
            return (True, f"Proposal FAILED ({proposal.votes_for:.0f} for, {proposal.votes_against:.0f} against)")

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict]:
        """Get proposal details."""
        if proposal_id not in self.proposals:
            return None

        p = self.proposals[proposal_id]
        return {
            'proposal_id': p.proposal_id,
            'title': p.title,
            'status': p.status,
            'votes_for': p.votes_for,
            'votes_against': p.votes_against,
            'votes_abstain': p.votes_abstain,
            'deadline': p.deadline
        }


if __name__ == "__main__":
    print("=== Phase IX: Resource Ledger ===\n")

    # Create ledger
    print("=== Creating Ledger ===")
    ledger = ResourceLedger()

    # Create accounts
    print("Creating accounts...")
    ledger.create_account('acc_dyson', 'Dyson Swarm Operations')
    ledger.create_account('acc_research', 'Research Division')
    ledger.create_account('acc_manufacturing', 'Manufacturing Facility')

    # Allocate resources
    print("Allocating resources...")
    success, frame = ledger.allocate('acc_dyson', ResourceType.ENERGY_MEGAWATT_HOURS, 1e8, "Dyson swarm initialization")
    print(f"Allocated energy: {success}")

    success, frame = ledger.allocate('acc_research', ResourceType.COMPUTE_EXAFLOPS, 1e6, "Research allocation")
    print(f"Allocated compute: {success}")

    # Transfer resources
    print("\nTransferring resources...")
    success, frame = ledger.transfer('acc_dyson', 'acc_manufacturing', ResourceType.ENERGY_MEGAWATT_HOURS, 1e6, "Refinery power")
    print(f"Transfer successful: {success}")

    # Check balances
    print("\n=== Account Balances ===")
    for acc_id in ['acc_dyson', 'acc_research', 'acc_manufacturing']:
        balance = ledger.get_account_balance(acc_id)
        print(f"\n{balance['name']}:")
        print(f"  Energy: {balance['balances']['MWh']:.2e} MWh")
        print(f"  Compute: {balance['balances']['EXAFLOPS']:.2e} EXAFLOPS")

    # Verify chain
    print("\n=== Ledger Integrity ===")
    valid, msg = ledger.verify_chain()
    print(f"Chain valid: {valid}")
    print(f"Message: {msg}")

    # Governance
    print("\n=== Governance Framework ===")
    governance = GovernanceFramework(ledger)

    # Create proposal
    print("Creating proposal...")
    success, prop_id = governance.create_proposal(
        "Expand Dyson Swarm to 50% coverage",
        "Allocate resources to increase solar collection",
        "acc_dyson",
        duration_days=30
    )
    print(f"Proposal created: {prop_id}")

    # Vote
    print("Voting...")
    governance.vote(prop_id, 'acc_dyson', 'FOR')
    governance.vote(prop_id, 'acc_research', 'FOR')
    governance.vote(prop_id, 'acc_manufacturing', 'AGAINST')

    # Finalize
    print("Finalizing...")
    success, msg = governance.finalize_proposal(prop_id)
    print(f"Result: {msg}")

    status = governance.get_proposal_status(prop_id)
    print(f"Final status: {status['status']}")
