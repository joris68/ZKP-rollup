use crate::HelloWorld::helloworld::*;
use anyhow::Chain;
use ethers::prelude::Abigen;
use ethers::{
    core::types::Address,
    providers::{Provider, Ws},
};
use eyre::Result;
use std::sync::Arc;

const WS_URL: &str = "ws://127.0.0.1:8545";
const WETH_ADDRESS: &str = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";

pub fn rust_file_generation() -> Result<()> {
    print!("ltessssss");
    let abi_source = "./HelloWorld.json";
    let out_file = "./src/HelloWorld.rs";
    Abigen::new("Helloworld", abi_source)?
        .generate()?
        .write_to_file(out_file)?;
    Ok(())
}

struct ChainListener {
    contract_provider: Helloworld<Provider<Ws>>,
}

impl ChainListener {
    async fn new() -> Result<ChainListener> {
        let provider = Provider::<Ws>::connect(WS_URL).await?;
        let client = Arc::new(provider);
        let address: Address = WETH_ADDRESS.parse()?;
        let contract_provider = Helloworld::new(address, client);
        Ok(ChainListener { contract_provider })
    }

    async fn listen_to_events() -> Result<()> {
        // let events = contract.events();
        let mut stream = events.stream().await?.take(1);
        while let Some(Ok(evt)) = stream.next().await {
            match evt {}
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn try_snippet() {
        let listener = ChainListener::new();
        //listener.
    }
}
