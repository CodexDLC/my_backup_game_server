# game_server/Logic/CoreServices/services/random_service.py

import random
import secrets
import os
import numpy as np
from typing import List, Any, Optional

class RandomService:
    def __init__(self, crypto_mode: bool = False):
        """
        :param crypto_mode: If True, uses cryptographically secure generators.
        """
        self.crypto_mode = crypto_mode
        self._init_generators()
        
    def _init_generators(self):
        """Initializes generators when the service is created."""
        # Generating 256 bits of entropy as a byte string
        byte_seed = os.urandom(32) 
        
        # Convert the byte string to an integer for NumPy's PCG64
        # 'big' endian is used to interpret bytes as a large integer
        # The first argument must be bytes or a bytearray
        numeric_seed = int.from_bytes(byte_seed, 'big')
        
        # Main generator for game logic (accepts byte strings)
        self.main_rng = random.Random(byte_seed) 
        
        # Cryptographically secure generator (does not accept seed)
        self.crypto_rng = secrets.SystemRandom()
        
        # Fast generator for bulk operations (requires integer seed)
        # Pass the converted numeric_seed to PCG64
        self.fast_rng = np.random.Generator(np.random.PCG64(numeric_seed))
    
    def reseed(self, new_seed: Optional[bytes] = None):
        """Re-initializes generators."""
        # If no new_seed is provided, generate a new one
        byte_seed = new_seed or os.urandom(32)
        
        # Convert the byte string to an integer for NumPy's PCG64
        numeric_seed = int.from_bytes(byte_seed, 'big')

        self.main_rng.seed(byte_seed)
        # Pass the converted numeric_seed to PCG64
        self.fast_rng = np.random.Generator(np.random.PCG64(numeric_seed))
    
    # --- Core methods ---
    def randint(self, a: int, b: int) -> int:
        """Random integer in range [a, b]."""
        if self.crypto_mode:
            return self.crypto_rng.randint(a, b)
        return self.main_rng.randint(a, b)
    
    def choice(self, seq: List[Any]) -> Any:
        """Random element from a sequence."""
        if self.crypto_mode:
            return self.crypto_rng.choice(seq)
        return self.main_rng.choice(seq)
    
    def uniform(self, a: float, b: float) -> float:
        """Uniform distribution."""
        return self.main_rng.uniform(a, b)
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Normal distribution."""
        return self.main_rng.gauss(mu, sigma)
    
    def choice(self, seq: List[Any], entity_id: Optional[str] = None) -> Any:
        """Random element from a sequence."""
        rng = self._select_rng(entity_id)
        return rng.choice(seq)
    
    def weighted_choice(self, items: List[Any], weights: List[float]) -> Any:
        """Weighted random selection."""
        return self.main_rng.choices(items, weights=weights, k=1)[0]
    
    def shuffle(self, seq: List[Any], entity_id: Optional[str] = None) -> None:
        """Shuffles a sequence."""
        rng = self._select_rng(entity_id)
        rng.shuffle(seq)
    
    # --- Optimized methods for bulk operations ---
    def fast_rand_array(self, shape: tuple, dtype=np.float32):
        """Fast generation of random number array."""
        return self.fast_rng.random(shape, dtype=dtype)
    
    def fast_randint(self, low: int, high: int, size: int) -> np.ndarray:
        """Fast generation of integers."""
        return self.fast_rng.integers(low, high, size)
    
    # --- Specialized game methods ---
    def critical_hit(self, base_chance: float, luck_factor: float = 1.0) -> bool:
        """Determines a critical hit."""
        return self.main_rng.random() < (base_chance * luck_factor)
    
    def loot_drop(self, drop_table: dict) -> Optional[dict]:
        """Determines loot drop."""
        rand_val = self.main_rng.random()
        cumulative = 0.0
        for item, prob in drop_table.items():
            cumulative += prob
            if rand_val <= cumulative:
                return item
        return None
    
    # --- Internal methods ---
    def _select_rng(self, entity_id: Optional[str] = None) -> random.Random:
        """Selects a generator based on context."""
        if entity_id:
            # Create a deterministic generator for the entity
            # Ensure the seed is an integer or hashable (like a string for random.Random)
            # For random.Random, f"{entity_id}-{self.main_rng.random()}" is fine.
            # If a deterministic NumPy generator were needed, a conversion to int would be necessary.
            return random.Random(f"{entity_id}-{self.main_rng.random()}".encode())
        return self.main_rng
