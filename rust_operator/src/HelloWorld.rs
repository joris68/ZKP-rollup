pub use helloworld::*;
/// This module was auto-generated with ethers-rs Abigen.
/// More information at: <https://github.com/gakonst/ethers-rs>
#[allow(
    clippy::enum_variant_names,
    clippy::too_many_arguments,
    clippy::upper_case_acronyms,
    clippy::type_complexity,
    dead_code,
    non_camel_case_types,
)]
pub mod helloworld {
    const _: () = {
        ::core::include_bytes!(
            "/Users/I762666/Documents/zk-Rollup/rust_operator/HelloWorld.json",
        );
    };
    #[allow(deprecated)]
    fn __abi() -> ::ethers::core::abi::Abi {
        ::ethers::core::abi::ethabi::Contract {
            constructor: ::core::option::Option::None,
            functions: ::core::convert::From::from([
                (
                    ::std::borrow::ToOwned::to_owned("sayHello"),
                    ::std::vec![
                        ::ethers::core::abi::ethabi::Function {
                            name: ::std::borrow::ToOwned::to_owned("sayHello"),
                            inputs: ::std::vec![],
                            outputs: ::std::vec![],
                            constant: ::core::option::Option::None,
                            state_mutability: ::ethers::core::abi::ethabi::StateMutability::NonPayable,
                        },
                    ],
                ),
            ]),
            events: ::core::convert::From::from([
                (
                    ::std::borrow::ToOwned::to_owned("HelloWorldEvent"),
                    ::std::vec![
                        ::ethers::core::abi::ethabi::Event {
                            name: ::std::borrow::ToOwned::to_owned("HelloWorldEvent"),
                            inputs: ::std::vec![
                                ::ethers::core::abi::ethabi::EventParam {
                                    name: ::std::borrow::ToOwned::to_owned("sender"),
                                    kind: ::ethers::core::abi::ethabi::ParamType::Address,
                                    indexed: true,
                                },
                                ::ethers::core::abi::ethabi::EventParam {
                                    name: ::std::borrow::ToOwned::to_owned("message"),
                                    kind: ::ethers::core::abi::ethabi::ParamType::String,
                                    indexed: false,
                                },
                            ],
                            anonymous: false,
                        },
                    ],
                ),
            ]),
            errors: ::std::collections::BTreeMap::new(),
            receive: false,
            fallback: false,
        }
    }
    ///The parsed JSON ABI of the contract.
    pub static HELLOWORLD_ABI: ::ethers::contract::Lazy<::ethers::core::abi::Abi> = ::ethers::contract::Lazy::new(
        __abi,
    );
    #[rustfmt::skip]
    const __BYTECODE: &[u8] = b"`\x80`@R4\x80\x15`\x0EW__\xFD[Pa\x01&\x80a\0\x1C_9_\xF3\xFE`\x80`@R4\x80\x15`\x0EW__\xFD[P`\x046\x10`&W_5`\xE0\x1C\x80c\xEF_\xB0[\x14`*W[__\xFD[`0`2V[\0[3s\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x16\x7F\xF4\x1C\xFE\xF2\xD4nD\xF6\x18}\xAB$%\r\xB5\xF86\n\xD4\x14\xBD9\xAA\xFC\x87\x1C\x06\xA2\x96\xA3T#`@Q`t\x90`\xD4V[`@Q\x80\x91\x03\x90\xA2V[_\x82\x82R` \x82\x01\x90P\x92\x91PPV[\x7FHello, world from Anvil!\0\0\0\0\0\0\0\0_\x82\x01RPV[_`\xC0`\x18\x83`~V[\x91P`\xC9\x82`\x8EV[` \x82\x01\x90P\x91\x90PV[_` \x82\x01\x90P\x81\x81\x03_\x83\x01R`\xE9\x81`\xB6V[\x90P\x91\x90PV\xFE\xA2dipfsX\"\x12 >\xCF\x07\xA0x\x7F\xDF \x81\xC9\xDF\x19-/\x081|\xAE^\xB7\x96\xD5T\x88\xFA\xF4\x0B\xEEiB\xF7wdsolcC\0\x08\x1E\x003";
    /// The bytecode of the contract.
    pub static HELLOWORLD_BYTECODE: ::ethers::core::types::Bytes = ::ethers::core::types::Bytes::from_static(
        __BYTECODE,
    );
    #[rustfmt::skip]
    const __DEPLOYED_BYTECODE: &[u8] = b"`\x80`@R4\x80\x15`\x0EW__\xFD[P`\x046\x10`&W_5`\xE0\x1C\x80c\xEF_\xB0[\x14`*W[__\xFD[`0`2V[\0[3s\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x16\x7F\xF4\x1C\xFE\xF2\xD4nD\xF6\x18}\xAB$%\r\xB5\xF86\n\xD4\x14\xBD9\xAA\xFC\x87\x1C\x06\xA2\x96\xA3T#`@Q`t\x90`\xD4V[`@Q\x80\x91\x03\x90\xA2V[_\x82\x82R` \x82\x01\x90P\x92\x91PPV[\x7FHello, world from Anvil!\0\0\0\0\0\0\0\0_\x82\x01RPV[_`\xC0`\x18\x83`~V[\x91P`\xC9\x82`\x8EV[` \x82\x01\x90P\x91\x90PV[_` \x82\x01\x90P\x81\x81\x03_\x83\x01R`\xE9\x81`\xB6V[\x90P\x91\x90PV\xFE\xA2dipfsX\"\x12 >\xCF\x07\xA0x\x7F\xDF \x81\xC9\xDF\x19-/\x081|\xAE^\xB7\x96\xD5T\x88\xFA\xF4\x0B\xEEiB\xF7wdsolcC\0\x08\x1E\x003";
    /// The deployed bytecode of the contract.
    pub static HELLOWORLD_DEPLOYED_BYTECODE: ::ethers::core::types::Bytes = ::ethers::core::types::Bytes::from_static(
        __DEPLOYED_BYTECODE,
    );
    pub struct Helloworld<M>(::ethers::contract::Contract<M>);
    impl<M> ::core::clone::Clone for Helloworld<M> {
        fn clone(&self) -> Self {
            Self(::core::clone::Clone::clone(&self.0))
        }
    }
    impl<M> ::core::ops::Deref for Helloworld<M> {
        type Target = ::ethers::contract::Contract<M>;
        fn deref(&self) -> &Self::Target {
            &self.0
        }
    }
    impl<M> ::core::ops::DerefMut for Helloworld<M> {
        fn deref_mut(&mut self) -> &mut Self::Target {
            &mut self.0
        }
    }
    impl<M> ::core::fmt::Debug for Helloworld<M> {
        fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::fmt::Result {
            f.debug_tuple(::core::stringify!(Helloworld)).field(&self.address()).finish()
        }
    }
    impl<M: ::ethers::providers::Middleware> Helloworld<M> {
        /// Creates a new contract instance with the specified `ethers` client at
        /// `address`. The contract derefs to a `ethers::Contract` object.
        pub fn new<T: Into<::ethers::core::types::Address>>(
            address: T,
            client: ::std::sync::Arc<M>,
        ) -> Self {
            Self(
                ::ethers::contract::Contract::new(
                    address.into(),
                    HELLOWORLD_ABI.clone(),
                    client,
                ),
            )
        }
        /// Constructs the general purpose `Deployer` instance based on the provided constructor arguments and sends it.
        /// Returns a new instance of a deployer that returns an instance of this contract after sending the transaction
        ///
        /// Notes:
        /// - If there are no constructor arguments, you should pass `()` as the argument.
        /// - The default poll duration is 7 seconds.
        /// - The default number of confirmations is 1 block.
        ///
        ///
        /// # Example
        ///
        /// Generate contract bindings with `abigen!` and deploy a new contract instance.
        ///
        /// *Note*: this requires a `bytecode` and `abi` object in the `greeter.json` artifact.
        ///
        /// ```ignore
        /// # async fn deploy<M: ethers::providers::Middleware>(client: ::std::sync::Arc<M>) {
        ///     abigen!(Greeter, "../greeter.json");
        ///
        ///    let greeter_contract = Greeter::deploy(client, "Hello world!".to_string()).unwrap().send().await.unwrap();
        ///    let msg = greeter_contract.greet().call().await.unwrap();
        /// # }
        /// ```
        pub fn deploy<T: ::ethers::core::abi::Tokenize>(
            client: ::std::sync::Arc<M>,
            constructor_args: T,
        ) -> ::core::result::Result<
            ::ethers::contract::builders::ContractDeployer<M, Self>,
            ::ethers::contract::ContractError<M>,
        > {
            let factory = ::ethers::contract::ContractFactory::new(
                HELLOWORLD_ABI.clone(),
                HELLOWORLD_BYTECODE.clone().into(),
                client,
            );
            let deployer = factory.deploy(constructor_args)?;
            let deployer = ::ethers::contract::ContractDeployer::new(deployer);
            Ok(deployer)
        }
        ///Calls the contract's `sayHello` (0xef5fb05b) function
        pub fn say_hello(&self) -> ::ethers::contract::builders::ContractCall<M, ()> {
            self.0
                .method_hash([239, 95, 176, 91], ())
                .expect("method not found (this should never happen)")
        }
        ///Gets the contract's `HelloWorldEvent` event
        pub fn hello_world_event_filter(
            &self,
        ) -> ::ethers::contract::builders::Event<
            ::std::sync::Arc<M>,
            M,
            HelloWorldEventFilter,
        > {
            self.0.event()
        }
        /// Returns an `Event` builder for all the events of this contract.
        pub fn events(
            &self,
        ) -> ::ethers::contract::builders::Event<
            ::std::sync::Arc<M>,
            M,
            HelloWorldEventFilter,
        > {
            self.0.event_with_filter(::core::default::Default::default())
        }
    }
    impl<M: ::ethers::providers::Middleware> From<::ethers::contract::Contract<M>>
    for Helloworld<M> {
        fn from(contract: ::ethers::contract::Contract<M>) -> Self {
            Self::new(contract.address(), contract.client())
        }
    }
    #[derive(
        Clone,
        ::ethers::contract::EthEvent,
        ::ethers::contract::EthDisplay,
        Default,
        Debug,
        PartialEq,
        Eq,
        Hash
    )]
    #[ethevent(name = "HelloWorldEvent", abi = "HelloWorldEvent(address,string)")]
    pub struct HelloWorldEventFilter {
        #[ethevent(indexed)]
        pub sender: ::ethers::core::types::Address,
        pub message: ::std::string::String,
    }
    ///Container type for all input parameters for the `sayHello` function with signature `sayHello()` and selector `0xef5fb05b`
    #[derive(
        Clone,
        ::ethers::contract::EthCall,
        ::ethers::contract::EthDisplay,
        Default,
        Debug,
        PartialEq,
        Eq,
        Hash
    )]
    #[ethcall(name = "sayHello", abi = "sayHello()")]
    pub struct SayHelloCall;
}
