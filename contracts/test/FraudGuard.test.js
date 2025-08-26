const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FraudGuard", function () {
  let FraudGuard;
  let fraudGuard;
  let owner;
  let relayer;
  let user1;
  let user2;

  beforeEach(async function () {
    // Get signers from Hardhat
    [owner, relayer, user1, user2] = await ethers.getSigners();

    // Deploy the contract
    FraudGuard = await ethers.getContractFactory("FraudGuard");
    fraudGuard = await FraudGuard.deploy();
    await fraudGuard.deployed();

    // Set up relayer for testing
    await fraudGuard.setRelayer(relayer.address, true);
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await fraudGuard.owner()).to.equal(owner.address);
    });

    it("Should set the deployer as the initial relayer", async function () {
      expect(await fraudGuard.relayer()).to.equal(owner.address);
    });
  });

  describe("Transaction Submission", function () {
    const txHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test-tx"));
    const amount = ethers.utils.parseEther("1.0");

    it("Should allow submitting a new transaction", async function () {
      await expect(fraudGuard.submitTxHash(txHash, user1.address, amount))
        .to.emit(fraudGuard, "TxSubmitted")
        .withArgs(txHash, user1.address, amount, (s) => s > 0);

      const txStatus = await fraudGuard.getTransactionStatus(txHash);
      expect(txStatus).to.equal("PENDING");
    });

    it("Should prevent duplicate transaction submissions", async function () {
      await fraudGuard.submitTxHash(txHash, user1.address, amount);
      
      await expect(
        fraudGuard.submitTxHash(txHash, user1.address, amount)
      ).to.be.revertedWith("Transaction already exists");
    });
  });

  describe("Transaction Verification", function () {
    const txHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test-verify"));
    const amount = ethers.utils.parseEther("1.0");
    const reason = "Suspicious activity detected";

    beforeEach(async function () {
      await fraudGuard.connect(user1).submitTxHash(txHash, user1.address, amount);
    });

    it("Should allow relayer to verify a transaction", async function () {
      await expect(
        fraudGuard.connect(relayer).setVerification(txHash, true, "Verified")
      )
        .to.emit(fraudGuard, "TxVerified")
        .withArgs(txHash, true, "Verified", (s) => s > 0);

      const status = await fraudGuard.getTransactionStatus(txHash);
      expect(status).to.equal("VERIFIED");
    });

    it("Should allow relayer to reject a transaction", async function () {
      await expect(
        fraudGuard.connect(relayer).setVerification(txHash, false, reason)
      )
        .to.emit(fraudGuard, "TxVerified")
        .withArgs(txHash, false, reason, (s) => s > 0);

      const status = await fraudGuard.getTransactionStatus(txHash);
      expect(status).to.equal("REJECTED");
    });

    it("Should prevent non-relayers from verifying transactions", async function () {
      await expect(
        fraudGuard.connect(user2).setVerification(txHash, true, "Should fail")
      ).to.be.revertedWith("Only relayer can call this function");
    });
  });

  describe("Transaction Holding", function () {
    const txHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test-hold"));
    const amount = ethers.utils.parseEther("5.0");
    const reason = "High risk transaction";

    beforeEach(async function () {
      await fraudGuard.connect(user1).submitTxHash(txHash, user1.address, amount);
    });

    it("Should allow relayer to hold a transaction", async function () {
      await expect(fraudGuard.connect(relayer).holdTransaction(txHash, reason))
        .to.emit(fraudGuard, "TxHeld")
        .withArgs(txHash, reason, (s) => s > 0);

      const status = await fraudGuard.getTransactionStatus(txHash);
      expect(status).to.equal("HELD");
    });

    it("Should allow owner to release a held transaction", async function () {
      // First hold the transaction
      await fraudGuard.connect(relayer).holdTransaction(txHash, reason);

      // Then release it
      await expect(
        fraudGuard.connect(owner).releaseHeldTransaction(txHash, true, "Approved")
      )
        .to.emit(fraudGuard, "TxVerified")
        .withArgs(txHash, true, "Approved", (s) => s > 0);

      const status = await fraudGuard.getTransactionStatus(txHash);
      expect(status).to.equal("VERIFIED");
    });

    it("Should prevent non-owners from releasing held transactions", async function () {
      await fraudGuard.connect(relayer).holdTransaction(txHash, reason);
      
      await expect(
        fraudGuard.connect(user2).releaseHeldTransaction(txHash, true, "Should fail")
      ).to.be.revertedWith("Only owner can call this function");
    });
  });

  describe("Access Control", function () {
    it("Should allow owner to transfer ownership", async function () {
      await fraudGuard.connect(owner).transferOwnership(user1.address);
      expect(await fraudGuard.owner()).to.equal(user1.address);
    });

    it("Should prevent non-owners from transferring ownership", async function () {
      await expect(
        fraudGuard.connect(user1).transferOwnership(user1.address)
      ).to.be.revertedWith("Only owner can call this function");
    });

    it("Should allow owner to add/remove relayers", async function () {
      // Add relayer
      await fraudGuard.connect(owner).setRelayer(user2.address, true);
      expect(await fraudGuard.authorizedRelayers(user2.address)).to.be.true;

      // Remove relayer
      await fraudGuard.connect(owner).setRelayer(user2.address, false);
      expect(await fraudGuard.authorizedRelayers(user2.address)).to.be.false;
    });

    it("Should prevent non-owners from managing relayers", async function () {
      await expect(
        fraudGuard.connect(user1).setRelayer(user2.address, true)
      ).to.be.revertedWith("Only owner can call this function");
    });
  });
});
