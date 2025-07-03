pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";
import "forge-std/Test.sol";
import {stdToml} from "forge-std/StdToml.sol";

import {HelloWorld} from "../contracts/HelloWorld.sol";

contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        new HelloWorld(); // constructor args if needed
        vm.stopBroadcast();
    }
}