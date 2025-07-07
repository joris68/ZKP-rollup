use alloy::{
    network::EthereumWallet,
    providers::ProviderBuilder,
    signers::local::PrivateKeySigner,
};
use alloy_primitives::{Address, FixedBytes, U256};
use anyhow::Result;
use clap::Parser;
use methods::GUEST_ELF;
use risc0_ethereum_contracts::encode_seal;
use risc0_zkvm::{default_prover, ExecutorEnv, ProverOpts, VerifierContext};
use serde::{Deserialize, Serialize};
use std::{fs, path::PathBuf};
use url::Url;

pub mod rollup_abi {
    alloy::sol!(
        #[sol(rpc, all_derives)]
        interface IRollup {
            function submitBatch(
                bytes32 oldRoot,
                bytes32 newRoot,
                uint32 batchId,
                bytes calldata txData,
                bytes calldata seal
            ) external;
        }
    );
}

use rollup_abi::IRollup;

#[derive(Parser, Debug)]
struct Args {
    #[clap(long)]
    chain_id: u64,

    #[clap(long, env)]
    eth_wallet_private_key: PrivateKeySigner,

    #[clap(long)]
    rpc_url: Url,

    #[clap(long)]
    contract: Address,

    #[clap(long)]
    batch_path: PathBuf,
}

// Input batch format (from your batch generator)
#[derive(Deserialize, Serialize)]  // Added Serialize here
struct LeafData {
    balance: u64,
    nonce: u64,
}

#[derive(Deserialize, Serialize)]  // Added Serialize here
struct TransactionSignature {
    #[serde(rename = "pubKey")]
    pub_key: String,
    signature: String,
}

#[derive(Deserialize, Serialize)]  // Added Serialize here
struct Transaction {
    from: String,
    to: String,
    amount: u64,
    nonce: u64,
    signature: TransactionSignature,
}

#[derive(Deserialize, Serialize)]  // Added Serialize here
struct Batch {
    old_merkle_root: String,
    new_merkle_root: String,
    leaf_data: Vec<LeafData>,
    transactions: Vec<Transaction>,
    badge_id: u32,
    addresses: Vec<String>,
}

// Output from guest program
#[derive(Serialize, Deserialize)]
struct BatchProof {
    old_root_verified: bool,
    new_root_verified: bool,
    signatures_verified: bool,
    old_root: String,
    new_root: String,
    badge_id: u32,
    transactions_processed: usize,
}

fn hex_to_bytes(hex_str: &str) -> Vec<u8> {
    let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    hex::decode(clean).expect("Invalid hex string")
}

fn hex_to_bytes32(hex_str: &str) -> [u8; 32] {
    let bytes = hex_to_bytes(hex_str);
    if bytes.len() != 32 {
        panic!("Expected 32 bytes, got {}", bytes.len());
    }
    let mut result = [0u8; 32];
    result.copy_from_slice(&bytes);
    result
}

fn create_transaction_calldata(transactions: &[Transaction]) -> Vec<u8> {
    let mut calldata = Vec::new();
    
    // Encode number of transactions
    calldata.extend_from_slice(&(transactions.len() as u32).to_be_bytes());
    
    for tx in transactions {
        // From address (20 bytes)
        let from_bytes = hex_to_bytes(&tx.from);
        calldata.extend_from_slice(&from_bytes[..20]);
        
        // To address (20 bytes)
        let to_bytes = hex_to_bytes(&tx.to);
        calldata.extend_from_slice(&to_bytes[..20]);
        
        // Amount (32 bytes - big endian)
        calldata.extend_from_slice(&tx.amount.to_be_bytes());
        
        // Nonce (32 bytes - big endian)
        calldata.extend_from_slice(&tx.nonce.to_be_bytes());
        
        // Signature (65 bytes)
        let sig_bytes = hex_to_bytes(&tx.signature.signature);
        calldata.extend_from_slice(&sig_bytes);
        
        // PubKey (20 bytes - address format)
        let pubkey_bytes = hex_to_bytes(&tx.signature.pub_key);
        calldata.extend_from_slice(&pubkey_bytes[..20]);
    }
    
    calldata
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    let args = Args::parse();

    println!("🔄 Loading batch from: {:?}", args.batch_path);
    let batch_json = fs::read_to_string(&args.batch_path)?;
    let batch: Batch = serde_json::from_str(&batch_json)?;

    println!("📊 Batch details:");
    println!("  Badge ID: {}", batch.badge_id);
    println!("  Transactions: {}", batch.transactions.len());
    println!("  Addresses: {}", batch.addresses.len());
    println!("  Old Root: {}", batch.old_merkle_root);
    println!("  Expected New Root: {}", batch.new_merkle_root);

    // Build the environment for the guest program
    let env = ExecutorEnv::builder()
        .write(&batch)?
        .build()?;

    println!("\n🔄 Generating ZK proof...");
    
    // Generate the proof
    let receipt = default_prover()
        .prove_with_ctx(
            env,
            &VerifierContext::default(),
            GUEST_ELF,
            &ProverOpts::groth16(),
        )?
        .receipt;

    // Extract the proof result from the journal
    let proof_result: BatchProof = receipt.journal.decode()?;
    
    println!("\n✅ ZK Proof generated!");
    println!("📋 Proof verification results:");
    println!("  Old root verified: {}", proof_result.old_root_verified);
    println!("  New root verified: {}", proof_result.new_root_verified);
    println!("  Signatures verified: {}", proof_result.signatures_verified);
    println!("  Transactions processed: {}", proof_result.transactions_processed);
    println!("  Computed old root: {}", proof_result.old_root);
    println!("  Computed new root: {}", proof_result.new_root);

    // Validate the proof
    if !proof_result.old_root_verified || !proof_result.new_root_verified || !proof_result.signatures_verified {
        panic!("❌ Proof verification failed!");
    }

    if proof_result.transactions_processed != batch.transactions.len() {
        panic!("❌ Not all transactions were processed!");
    }

    // Encode the seal for on-chain verification
    let seal = encode_seal(&receipt)?;
    
    // Create transaction calldata
    let tx_calldata = create_transaction_calldata(&batch.transactions);
    
    println!("\n📦 Calldata created: {} bytes", tx_calldata.len());
    
    // Convert roots to bytes32 format
    let old_root_bytes32: FixedBytes<32> = FixedBytes::from_slice(&hex_to_bytes32(&batch.old_merkle_root));
    let new_root_bytes32: FixedBytes<32> = FixedBytes::from_slice(&hex_to_bytes32(&batch.new_merkle_root));

    println!("\n🚀 Publishing to blockchain...");
    println!("  Contract: {}", args.contract);
    println!("  Chain ID: {}", args.chain_id);
    println!("  RPC URL: {}", args.rpc_url);

    // Set up Ethereum connection
    let wallet = EthereumWallet::from(args.eth_wallet_private_key);
    let provider = ProviderBuilder::new()
        .wallet(wallet)
        .connect_http(args.rpc_url);  // Fixed: changed from on_http to connect_http

    let contract = IRollup::new(args.contract, provider);

    // Submit the batch on-chain
    let call = contract.submitBatch(
        old_root_bytes32,
        new_root_bytes32,
        batch.badge_id,
        tx_calldata.into(),
        seal.into(),
    );

    let pending_tx = call.send().await?;
    let receipt = pending_tx.get_receipt().await?;

    println!("\n✅ Batch published successfully!");
    println!("📄 Transaction receipt:");
    println!("  Hash: {:?}", receipt.transaction_hash);
    println!("  Block: {:?}", receipt.block_number);
    println!("  Gas used: {:?}", receipt.gas_used);
    
    if receipt.status() {
        println!("🎉 Transaction succeeded!");
    } else {
        println!("❌ Transaction failed!");
    }

    Ok(())
}