#![cfg_attr(not(feature = "std"), no_std)]
extern crate alloc;
use alloc::vec::Vec;
use core::convert::TryInto;
use k256::ecdsa::{SigningKey, VerifyingKey, Signature};
use k256::EncodedPoint;
use sha2::{Sha256, Digest};

#[cfg(feature = "std")]
use k256::elliptic_curve::rand_core::OsRng;

#[cfg(feature = "std")]
use k256::ecdsa::signature::Signer;

use k256::ecdsa::signature::Verifier;

// Re-export types for convenience
pub use k256::ecdsa::{SigningKey as PrivateKey, VerifyingKey as PublicKey};
pub use k256::ecdsa::Signature as EcdsaSignature;

/// Transaction data structure
#[derive(Clone, Debug)]
pub struct TransactionData {
    pub from: [u8; 20],      // Ethereum address (20 bytes)
    pub to: [u8; 20],        // Ethereum address (20 bytes)
    pub amount: u64,
    pub nonce: u64,
}

impl TransactionData {
    /// Create a new transaction
    pub fn new(from: [u8; 20], to: [u8; 20], amount: u64, nonce: u64) -> Self {
        Self { from, to, amount, nonce }
    }
    
    /// Serialize transaction data for hashing
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        bytes.extend_from_slice(&self.from);
        bytes.extend_from_slice(&self.to);
        bytes.extend_from_slice(&self.amount.to_le_bytes());
        bytes.extend_from_slice(&self.nonce.to_le_bytes());
        bytes
    }
    
    /// Hash the transaction data using SHA-256
    pub fn hash(&self) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(&self.to_bytes());
        hasher.finalize().into()
    }
}

/// Generate a random private key (only available with std feature)
#[cfg(feature = "std")]
pub fn generate_private_key() -> PrivateKey {
    SigningKey::random(&mut OsRng)
}

/// Get public key from private key
pub fn get_public_key(private_key: &PrivateKey) -> PublicKey {
    *private_key.verifying_key()
}

/// Convert public key to compressed bytes (33 bytes)
pub fn public_key_to_bytes(public_key: &PublicKey) -> [u8; 33] {
    public_key.to_encoded_point(true).as_bytes().try_into()
        .expect("Compressed public key should be 33 bytes")
}

/// Convert bytes to public key
pub fn bytes_to_public_key(bytes: &[u8; 33]) -> Result<PublicKey, &'static str> {
    let encoded_point = EncodedPoint::from_bytes(bytes)
        .map_err(|_| "Invalid encoded point")?;
    VerifyingKey::from_encoded_point(&encoded_point)
        .map_err(|_| "Invalid public key")
}

/// Convert signature to bytes (64 bytes)
pub fn signature_to_bytes(signature: &EcdsaSignature) -> [u8; 64] {
    signature.to_bytes().into()
}

/// Convert bytes to signature
pub fn bytes_to_signature(bytes: &[u8; 64]) -> Result<EcdsaSignature, &'static str> {
    Signature::from_bytes(bytes.into())
        .map_err(|_| "Invalid signature format")
}

/// Sign transaction data with a private key
#[cfg(feature = "std")]
pub fn sign_tx(tx_data: &TransactionData, private_key: &PrivateKey) -> EcdsaSignature {
    let tx_hash = tx_data.hash();
    private_key.sign(&tx_hash)
}

/// Sign a message hash with a private key (more general)
#[cfg(feature = "std")]
pub fn sign_hash(message_hash: &[u8; 32], private_key: &PrivateKey) -> EcdsaSignature {
    private_key.sign(message_hash)
}

/// Verify a signature against transaction data and public key
pub fn verify_tx_signature(
    tx_data: &TransactionData, 
    signature: &EcdsaSignature, 
    public_key: &PublicKey
) -> bool {
    let tx_hash = tx_data.hash();
    verify_signature(&tx_hash, signature, public_key)
}

/// Verify a signature against a message hash and public key (more general)
pub fn verify_signature(
    message_hash: &[u8; 32], 
    signature: &EcdsaSignature, 
    public_key: &PublicKey
) -> bool {
    public_key.verify(message_hash, signature).is_ok()
}

/// Create a transaction signature structure for JSON serialization
#[derive(Clone, Debug)]
pub struct TransactionSignature {
    pub signature: [u8; 64],
    pub public_key: [u8; 33],
}

impl TransactionSignature {
    pub fn new(signature: EcdsaSignature, public_key: PublicKey) -> Self {
        Self {
            signature: signature_to_bytes(&signature),
            public_key: public_key_to_bytes(&public_key),
        }
    }
    
    /// Verify this signature against transaction data
    pub fn verify(&self, tx_data: &TransactionData) -> bool {
        let signature = match bytes_to_signature(&self.signature) {
            Ok(sig) => sig,
            Err(_) => return false,
        };
        
        let public_key = match bytes_to_public_key(&self.public_key) {
            Ok(pk) => pk,
            Err(_) => return false,
        };
        
        verify_tx_signature(tx_data, &signature, &public_key)
    }
}

/// Helper function to convert Ethereum address string to bytes
pub fn address_from_hex(hex_str: &str) -> Result<[u8; 20], &'static str> {
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

/// Helper function to convert bytes to hex string
pub fn bytes_to_hex(bytes: &[u8]) -> alloc::string::String {
    use alloc::string::String;
    use alloc::format;
    
    let mut result = String::new();
    for byte in bytes {
        result.push_str(&format!("{:02x}", byte));
    }
    format!("0x{}", result)
}