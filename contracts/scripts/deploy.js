const hre = require("hardhat");

async function main() {
  console.log("Deploying FraudGuard contract...");
  
  // Deploy the contract
  const FraudGuard = await hre.ethers.getContractFactory("FraudGuard");
  const fraudGuard = await FraudGuard.deploy();
  
  // Wait for deployment to complete
  await fraudGuard.deployed();
  
  console.log(`FraudGuard deployed to: ${fraudGuard.address}`);
  
  // Verify the contract on Etherscan (if on a live network)
  if (process.env.ETHERSCAN_API_KEY) {
    console.log("Waiting for block confirmations...");
    await fraudGuard.deployTransaction.wait(6);
    
    console.log("Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: fraudGuard.address,
        constructorArguments: [],
      });
      console.log("Contract verified on Etherscan!");
    } catch (error) {
      console.log("Verification failed:", error);
    }
  }
  
  return {
    address: fraudGuard.address,
    abi: JSON.parse(fraudGuard.interface.format("json")),
  };
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
