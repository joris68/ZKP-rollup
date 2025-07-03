#![cfg_attr(not(feature = "std"), no_std)]
extern crate alloc;
use alloc::vec::Vec;
use core::convert::TryInto;
use sha2::{Sha256, Digest};
use sha3::{Keccak256, Digest as Keccak256Digest};
use sparse_merkle_tree::{
    blake2b::Blake2bHasher,
    default_store::DefaultStore,
    SparseMerkleTree,
    traits::Value,
    H256,
};

/// Shared account data type for your SMT
#[derive(Clone, Default)]
pub struct AccountData {
    pub balance: u64,
    pub nonce: u64,
}

impl Value for AccountData {
    fn to_h256(&self) -> H256 {
        // empty leaf optimization
        if self.balance == 0 && self.nonce == 0 {
            return H256::zero();
        }
        // pack LE bytes: balance||nonce
        let mut data = [0u8; 16];
        data[0..8].copy_from_slice(&self.balance.to_le_bytes());
        data[8..16].copy_from_slice(&self.nonce.to_le_bytes());
        // R0-optimized SHA256 precompile
        let mut hasher = Sha256::new();
        hasher.update(&data);
        let hash = hasher.finalize();
        let mut buf = [0u8; 32];
        buf.copy_from_slice(&hash);
        H256::from(buf)
    }
    
    fn zero() -> Self {
        Default::default()
    }
}

/// A 2^256-ary sparse Merkle tree over your AccountData
pub type SMT = SparseMerkleTree<Blake2bHasher, AccountData, DefaultStore<AccountData>>;

/// Instantiate a fresh empty tree (all-zero leaves)
pub fn new_smt() -> SMT {
    SMT::default()
}

/// Read the current root
pub fn root(tree: &SMT) -> H256 {
    *tree.root()
}

/// Update one leaf at `key` to `value`
pub fn update(tree: &mut SMT, key: H256, value: AccountData) {
    tree.update(key, value).expect("SMT update failed");
}

/// Compute the 256-bit path key by Keccak256(address_bytes)
pub fn address_to_tree_key(address: &[u8; 20]) -> H256 {
    let mut hasher = Keccak256::new();
    hasher.update(address);
    let hash = hasher.finalize();
    let bytes: [u8; 32] = hash.as_slice().try_into().unwrap();
    H256::from(bytes)
}

/// Helper functions for converting between different formats
/// Convert hex string to 20-byte array (for Ethereum addresses)
pub fn hex_to_address(hex_str: &str) -> Result<[u8; 20], &'static str> {
    let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    if clean.len() != 40 {
        return Err("Address must be 40 hex characters");
    }
    
    let mut result = [0u8; 20];
    for i in 0..20 {
        let byte_str = &clean[i*2..i*2+2];
        result[i] = u8::from_str_radix(byte_str, 16).map_err(|_| "Invalid hex character")?;
    }
    Ok(result)
}

/// Convert 32-byte array to hex string
pub fn h256_to_hex(hash: &H256) -> alloc::string::String {
    use alloc::string::String;
    use alloc::format;
    format!("0x{}", hex_encode(hash.as_slice()))
}

/// Convert bytes to hex string (no_std compatible)
fn hex_encode(bytes: &[u8]) -> alloc::string::String {
    use alloc::string::String;
    use alloc::format;
    
    let mut result = String::new();
    for byte in bytes {
        result.push_str(&format!("{:02x}", byte));
    }
    result
}

// Optional: Simple merkle proof functions (simplified for now)
/// Get a simple inclusion proof for debugging
pub fn get_simple_proof(tree: &SMT, key: H256) -> Option<AccountData> {
    tree.get(&key).ok()
}

/// Verify that a key-value pair exists in the tree
pub fn verify_inclusion(tree: &SMT, key: H256, expected_value: &AccountData) -> bool {
    match tree.get(&key) {
        Ok(value) => value.balance == expected_value.balance && value.nonce == expected_value.nonce,
        Err(_) => false,
    }
}