
use ethers::{
    prelude::{abigen, Abigen},
    providers::{Http, Provider},
    types::Address,
};
use std::sync::Arc;
use ethers::providers::{Provider, Ws};


fn rust_file_generation() -> Result<()> {
    let abi_source = "./src/HelloWorld.json";
    let out_file = std::env::temp_dir().join("HelloWorld.rs")
    if out_file.exists() {
        std::fs::remove_file(&out_file)?;
    }
    Abigen::new("HelloWorld", abi_source)?.generate()?.write_to_file(out_file)?
    Ok(())
}


#[tokio::main]
async fn main() -> eyre::Result<()> {
    rust_file_generation()
    let provider = Provider::<Ws>::connect("ws://127.0.0.1:8545").await?;
    let client = Arc::new(provider);

    // Your deployed contract address
    let contract_address: Address = "0x5FbDB2315678afecb367f032d93F642f64180aa3".parse()?;

    // Instantiate contract
    let contract = HelloWorld::new(contract_address, client);

    // Create event stream
    let mut stream = contract
        .events()
        .from_block(BlockNumber::Latest)
        .stream()
        .await?;

    println!("Listening for MyEvent...");

    // Listen to the events
    while let Some(Ok(event)) = stream.next().await {
        println!("New event: {:?}", event);
    }


    Ok(())
}