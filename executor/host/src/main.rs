use alloy::{
    network::EthereumWallet,
    providers::ProviderBuilder,
    signers::local::PrivateKeySigner,
};
use alloy_primitives::{Address, FixedBytes};
use anyhow::Result;
use clap::Parser;
use methods::GUEST_ELF;
use risc0_ethereum_contracts::encode_seal;
use risc0_zkvm::{default_prover, ExecutorEnv, ProverOpts, VerifierContext};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::{fs, path::PathBuf};
use url::Url;

pub mod rollup_abi {
    alloy::sol!(
        #[sol(rpc, all_derives)]
        interface IRollup {
            function submitBatch(
                uint32 batchId,
                bytes calldata txData,
                bytes32 journalHash,
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

#[derive(Deserialize, Serialize, Clone)]
struct LeafData {
    balance: u64,
    nonce: u64,
}

#[derive(Deserialize, Serialize, Clone)]
struct TransactionSignature {
    #[serde(rename = "pubKey")]
    pub_key: String,
    signature: String,
}

#[derive(Deserialize, Serialize, Clone)]
struct Transaction {
    from: String,
    to: String,
    amount: u64,
    nonce: u64,
    signature: TransactionSignature,
}

#[derive(Deserialize, Serialize, Clone)]
struct DepositInfo {
    deposit_id: u64,
    user: String,     
    amount: u64,     
}

#[derive(Deserialize, Serialize, Clone)]
struct Batch {
    old_merkle_root: String,
    new_merkle_root: String,
    leaf_data: Vec<LeafData>,
    transactions: Vec<Transaction>,
    deposits: Vec<DepositInfo>, 
    badge_id: u32,
    addresses: Vec<String>,
}

fn hex_to_bytes(hex_str: &str) -> Vec<u8> {
    let clean = hex_str.strip_prefix("0x").unwrap_or(hex_str);
    hex::decode(clean).expect("Invalid hex string")
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
        
        // Amount (8 bytes - big endian u64)
        calldata.extend_from_slice(&tx.amount.to_be_bytes());
        
        // Nonce (8 bytes - big endian u64)
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

    println!("Loading batch from: {:?}", args.batch_path);
    let batch_json = fs::read_to_string(&args.batch_path)?;
    let batch: Batch = serde_json::from_str(&batch_json)?;

    // Generate the proof in a blocking task to avoid Tokio runtime issues
    let batch_clone = batch.clone();
    let receipt = tokio::task::spawn_blocking(move || {
        let env = ExecutorEnv::builder()
            .write(&batch_clone)?
            .build()?;

        default_prover()
            .prove_with_ctx(
                env,
                &VerifierContext::default(),
                GUEST_ELF,
                &ProverOpts::groth16(),
            )
    }).await??;

    let receipt = receipt.receipt;

    // Extract the proof result from the journal
    // The guest commits a tuple: (bool, [u8; 32], [u8; 32], u32, u32, Vec<u64>)
    let verification_data: (bool, [u8; 32], [u8; 32], u32, u32, Vec<u64>) = receipt.journal.decode()?;
    
    let (success, old_root_bytes, new_root_bytes, badge_id, transactions_processed, processed_deposit_ids) = verification_data;
    
    // Convert bytes back to hex strings for display
    let computed_old_root = format!("0x{}", hex::encode(old_root_bytes));
    let computed_new_root = format!("0x{}", hex::encode(new_root_bytes));

    // Validate the proof
    if !success {
        panic!("❌ Proof verification failed!");
    }

    if transactions_processed != batch.transactions.len() as u32 {
        panic!("❌ Not all transactions were processed!");
    }

    if processed_deposit_ids.len() != batch.deposits.len() {
        panic!("❌ Not all deposits were processed!");
    }

    if computed_old_root != batch.old_merkle_root {
        panic!("❌ Computed old root doesn't match batch: expected {}, got {}", 
               batch.old_merkle_root, computed_old_root);
    }

    if computed_new_root != batch.new_merkle_root {
        panic!("❌ Computed new root doesn't match batch: expected {}, got {}", 
               batch.new_merkle_root, computed_new_root);
    }

    // Encode the seal for on-chain verification
    let seal = encode_seal(&receipt)?;
    
    // Compute the journal hash from the raw journal bytes
    let journal_bytes = &receipt.journal.bytes;
    let journal_hash = Sha256::digest(journal_bytes);
    let journal_hash_bytes32: FixedBytes<32> = FixedBytes::from_slice(&journal_hash);
    
    let tx_calldata = create_transaction_calldata(&batch.transactions);
    
    // Set up Ethereum connection
    let wallet = EthereumWallet::from(args.eth_wallet_private_key);
    let provider = ProviderBuilder::new()
        .wallet(wallet)
        .connect_http(args.rpc_url);

    let contract = IRollup::new(args.contract, provider);

    // Submit the batch on-chain 
    let call = contract.submitBatch(
        badge_id,                  
        tx_calldata.into(),        
        journal_hash_bytes32,      
        seal.into(),        
    );

    let pending_tx = call.send().await?;
    let receipt = pending_tx.get_receipt().await?;

    println!("\n✅ Batch published successfully!");
    println!("Transaction receipt:");
    println!("  Hash: {:?}", receipt.transaction_hash);
    println!("  Block: {:?}", receipt.block_number);
    println!("  Gas used: {:?}", receipt.gas_used);
    
    if receipt.status() {
        println!("✅ Transaction succeeded!");
        println!("{} deposits settled", processed_deposit_ids.len());
        println!("State transition settled: {} -> {}", computed_old_root, computed_new_root);
    } else {
        println!("❌ Transaction failed!");
    }

    Ok(())
}