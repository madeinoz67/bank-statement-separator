# Changelog

## [3.0.6](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.5...v3.0.6) (2025-09-07)


### Bug Fixes

* resolve release workflow infinite loop issue ([27eb384](https://github.com/madeinoz67/bank-statement-separator/commit/27eb38417c1674bd944ed173d82e2ebbd511fab7))

## [3.0.5](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.4...v3.0.5) (2025-09-06)


### Bug Fixes

* add API key dependency to multi-statement test ([4a6d85c](https://github.com/madeinoz67/bank-statement-separator/commit/4a6d85c99216897db0eec692a4631dc6ca663ec6))
* add debug logging for LLM metadata extraction failures ([65e41b2](https://github.com/madeinoz67/bank-statement-separator/commit/65e41b296e83dbde4ffe14aa46a857a9cafd9ea1))
* resolve intermittent metadata extraction failures ([1b39643](https://github.com/madeinoz67/bank-statement-separator/commit/1b396438340542b4c33654a7787686d6ed96d4b1))
* update paths-ignore to allow PR creation for code changes ([aff1ab9](https://github.com/madeinoz67/bank-statement-separator/commit/aff1ab950be0c49d6b294061f67fc82d489509f8))


### Styles

* format code with ruff ([1ad1bc5](https://github.com/madeinoz67/bank-statement-separator/commit/1ad1bc5383538e9e121797d2a1b9a3cec19f7ee3))
* improve code formatting and documentation ([cdfbc0d](https://github.com/madeinoz67/bank-statement-separator/commit/cdfbc0db501ef252103d44f490c435a6b6329bb2))

## [3.0.4](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.3...v3.0.4) (2025-09-06)


### Bug Fixes

* resolve documentation workflow contention and race conditions ([625f291](https://github.com/madeinoz67/bank-statement-separator/commit/625f2919d177ceb8d33214dd0f51fa1862a60f55))
* resolve release-please conflict with existing releases ([7736d79](https://github.com/madeinoz67/bank-statement-separator/commit/7736d79529cbca20e03881546d74ee7bc07d0333))

## [3.0.3](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.2...v3.0.3) (2025-09-06)


### Bug Fixes

* ensure release workflow triggers docs deployment ([3b4877d](https://github.com/madeinoz67/bank-statement-separator/commit/3b4877d438814302eafdb26496c197bb0651b8cf))
* update release-please workflow to properly trigger release workflow ([112a442](https://github.com/madeinoz67/bank-statement-separator/commit/112a442fac4dcea7ca43a8e1521d3e9a759f85c6))


### Styles

* format code with ruff ([9bea643](https://github.com/madeinoz67/bank-statement-separator/commit/9bea64383d45c260ca0653f369b4bbca6118ac17))

## [3.0.2](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.1...v3.0.2) (2025-09-06)


### Bug Fixes

* restore release triggering by removing skip-github-release ([ed5fc4e](https://github.com/madeinoz67/bank-statement-separator/commit/ed5fc4e6d291d5285f0cb49ff21484ca4ef9db0f))


### Documentation

* update AGENTS.md with automated semantic versioning implementation ([5b7bdc6](https://github.com/madeinoz67/bank-statement-separator/commit/5b7bdc694a68ac151c599906b6f7dc17390c644e))
* update AGENTS.md with latest changes ([3ed3864](https://github.com/madeinoz67/bank-statement-separator/commit/3ed386433d84ecbeb5f24723cafe088cb345fdb5))

## [3.0.1](https://github.com/madeinoz67/bank-statement-separator/compare/v3.0.0...v3.0.1) (2025-09-06)


### Bug Fixes

* resolve workflow conflict by disabling GitHub release creation in release-please ([90ccf1e](https://github.com/madeinoz67/bank-statement-separator/commit/90ccf1ef003ca66a0fe66b95d6393a597b80ea9c))

## [3.0.0](https://github.com/madeinoz67/bank-statement-separator/compare/v2.1.5...v3.0.0) (2025-09-06)


### ⚠ BREAKING CHANGES

* Release process now requires conventional commits

### Features

* add automated semantic versioning with release-please ([c73d9db](https://github.com/madeinoz67/bank-statement-separator/commit/c73d9db792f2b648518539e921fcb23773460368))
* enhance PyPI package metadata ([d3a3f6a](https://github.com/madeinoz67/bank-statement-separator/commit/d3a3f6a92d96a5487708394354f5a76d920bb416))


### Bug Fixes

* add id-token permission to release-please workflow ([13a8a2b](https://github.com/madeinoz67/bank-statement-separator/commit/13a8a2be58d813a9cab4b00f08300ce33c14d959))
* add include-component-in-tag setting for clean tag format ([2f77978](https://github.com/madeinoz67/bank-statement-separator/commit/2f779784570f615fbd037b6ee513acd921cff23c))
* add manual trigger support to release workflow ([374993f](https://github.com/madeinoz67/bank-statement-separator/commit/374993fbf8fa5bb692875350e73a3467dd187e75))
* add repository checkout before git commands in release-please workflow ([86f9a94](https://github.com/madeinoz67/bank-statement-separator/commit/86f9a94439243c171229ab77189e8ea81ea1415f))
* add tag-format configuration for release-please ([0dbd111](https://github.com/madeinoz67/bank-statement-separator/commit/0dbd1116ab6bc635f7a68d8e4b0b5e99d61a7391))
* add workflow_dispatch trigger to release workflow ([5466877](https://github.com/madeinoz67/bank-statement-separator/commit/54668772d29ed8543cde63dad829abf3773571d0))
* correct JSON format in release-please manifest ([0dc2257](https://github.com/madeinoz67/bank-statement-separator/commit/0dc225769990cbc552f60ce3c43d70477caca33f))
* correct pyproject.toml structure for classifiers ([9fd2854](https://github.com/madeinoz67/bank-statement-separator/commit/9fd28541697709c5e84ce169d0d064854c48e81a))
* correct pyproject.toml structure for dependencies ([830f0ef](https://github.com/madeinoz67/bank-statement-separator/commit/830f0efbcbdb2321c7e05a6d0517c3c6ffd6a131))
* correct versioned documentation workflow configuration ([6db9abb](https://github.com/madeinoz67/bank-statement-separator/commit/6db9abbe48f90d2cf8fe1ecca4dd6605672a9058))
* enable publish and docs jobs for repository_dispatch events ([f8bdcee](https://github.com/madeinoz67/bank-statement-separator/commit/f8bdceeffe8866c348f345d3ab1f29d20c21d3a8))
* expand metadata extraction to all statement pages ([6202451](https://github.com/madeinoz67/bank-statement-separator/commit/62024518383960aef62879cbb8763c30d6bd266d))
* implement workflow chaining to resolve release trigger issue ([974b8b5](https://github.com/madeinoz67/bank-statement-separator/commit/974b8b560ce884ef2e3bbab4c573cff49b1fccaa))
* remove deprecated license classifier ([cd08b9b](https://github.com/madeinoz67/bank-statement-separator/commit/cd08b9b750c2f1f63491fa0a2a7a0255c0633b15))
* resolve shell script syntax error in release-please debug output ([055c9c9](https://github.com/madeinoz67/bank-statement-separator/commit/055c9c93e2b54fb37dbadf9970e925de5a822085))
* skip conflicting version v2.1.4 to resolve release conflict ([b324df1](https://github.com/madeinoz67/bank-statement-separator/commit/b324df1f2a232f07e261f20ffea50e5ad814e38e))
* update PyPI publishing to use command-line credentials ([8fff33a](https://github.com/madeinoz67/bank-statement-separator/commit/8fff33a71d06fe8b40f2d73ae6841b0b18ff3f90))
* update release-please action to correct repository ([2787d3e](https://github.com/madeinoz67/bank-statement-separator/commit/2787d3ed251cead666b076924065ad10861f0cfe))


### Chores

* **main:** release 2.0.0 ([5d66f43](https://github.com/madeinoz67/bank-statement-separator/commit/5d66f438e4e09938ac2ddd18f15d4fae4c0a6db6))
* **main:** release 2.0.0 ([893a427](https://github.com/madeinoz67/bank-statement-separator/commit/893a4271f50580dd20bf855892ae7774fa695e2c))
* **main:** release 2.1.0 ([c107a16](https://github.com/madeinoz67/bank-statement-separator/commit/c107a166058a1314f1213cd08589824ba1681e66))
* **main:** release 2.1.0 ([840e716](https://github.com/madeinoz67/bank-statement-separator/commit/840e716a98585294af0efa471a38cbf981dffeba))
* **main:** release 2.1.1 ([6f71b9f](https://github.com/madeinoz67/bank-statement-separator/commit/6f71b9f2f9b986bc5d93a29537e6ffc577c6463e))
* **main:** release 2.1.1 ([b207d79](https://github.com/madeinoz67/bank-statement-separator/commit/b207d791b2983b1e451e7919e62c0068c0d2f3b7))
* **main:** release 2.1.2 ([fa77f96](https://github.com/madeinoz67/bank-statement-separator/commit/fa77f96a4c5e04a970f7d1418814366f5b69bf30))
* **main:** release 2.1.2 ([b490e28](https://github.com/madeinoz67/bank-statement-separator/commit/b490e283eccea1891d2481cb2d2f46852706b795))
* **main:** release 2.1.3 ([57db767](https://github.com/madeinoz67/bank-statement-separator/commit/57db7674b05955cf9a25559fc141c7768075c7af))
* **main:** release 2.1.3 ([33e4c28](https://github.com/madeinoz67/bank-statement-separator/commit/33e4c2835fbc4bcd5b1406e332f8ac4ddac7d658))
* **main:** release 2.1.4 ([8383631](https://github.com/madeinoz67/bank-statement-separator/commit/8383631205cd25f8590045ffb73e7be1bf58f518))
* **main:** release 2.1.4 ([5017622](https://github.com/madeinoz67/bank-statement-separator/commit/50176229b73bfc7e5bc2cd659fafaff8292eae89))
* **main:** release bank-statement-separator 1.0.0 ([b6b736a](https://github.com/madeinoz67/bank-statement-separator/commit/b6b736ab88d502c716ea9d2d98f61f8f79ddb9aa))
* **main:** release bank-statement-separator 1.0.0 ([ef2b2c9](https://github.com/madeinoz67/bank-statement-separator/commit/ef2b2c973e98e9f0ac9161f4842c0e92addd7b94))
* **main:** release bank-statement-separator 1.0.1 ([f9c84a3](https://github.com/madeinoz67/bank-statement-separator/commit/f9c84a35d24f667bd86bd61006299ed7c58188d9))
* **main:** release bank-statement-separator 1.0.1 ([6d34b7c](https://github.com/madeinoz67/bank-statement-separator/commit/6d34b7c08c87b011e4756c1f8c025ad88cb01bdf))
* update version to 2.0.2 for manual release ([9f583cf](https://github.com/madeinoz67/bank-statement-separator/commit/9f583cf52de43fc956396f389d30ca79517f510c))


### Documentation

* add comprehensive Mermaid workflow diagram to release management ([9695bb0](https://github.com/madeinoz67/bank-statement-separator/commit/9695bb02d088b3e55fbb003808daadee3841e7d3))
* add comprehensive release management documentation ([5ab9133](https://github.com/madeinoz67/bank-statement-separator/commit/5ab91336c462323a38cb514bf0fd2c01894c8883))
* update workflow diagrams to show complete CI/CD pipeline ([bace503](https://github.com/madeinoz67/bank-statement-separator/commit/bace5036ea43b04279ea4981ebdeba09a3185939))
* update working notes with manual release flow documentation ([e5a7de0](https://github.com/madeinoz67/bank-statement-separator/commit/e5a7de0942259c456c1b4a229f8695841d477d09))
* update working-notes with recent fixes and improvements ([d11cdc8](https://github.com/madeinoz67/bank-statement-separator/commit/d11cdc8dec5fb9ef35be5220037457f1a2e8e6bc))

## [2.1.4](https://github.com/madeinoz67/bank-statement-separator/compare/v2.1.3...v2.1.4) (2025-09-06)


### Bug Fixes

* correct versioned documentation workflow configuration ([6db9abb](https://github.com/madeinoz67/bank-statement-separator/commit/6db9abbe48f90d2cf8fe1ecca4dd6605672a9058))


### Documentation

* add comprehensive Mermaid workflow diagram to release management ([9695bb0](https://github.com/madeinoz67/bank-statement-separator/commit/9695bb02d088b3e55fbb003808daadee3841e7d3))

## [2.1.3](https://github.com/madeinoz67/bank-statement-separator/compare/v2.1.2...v2.1.3) (2025-09-06)


### Bug Fixes

* enable publish and docs jobs for repository_dispatch events ([f8bdcee](https://github.com/madeinoz67/bank-statement-separator/commit/f8bdceeffe8866c348f345d3ab1f29d20c21d3a8))

## [2.1.2](https://github.com/madeinoz67/bank-statement-separator/compare/v2.1.1...v2.1.2) (2025-09-06)


### Bug Fixes

* implement workflow chaining to resolve release trigger issue ([974b8b5](https://github.com/madeinoz67/bank-statement-separator/commit/974b8b560ce884ef2e3bbab4c573cff49b1fccaa))

## [2.1.1](https://github.com/madeinoz67/bank-statement-separator/compare/v2.1.0...v2.1.1) (2025-09-06)


### Bug Fixes

* add repository checkout before git commands in release-please workflow ([86f9a94](https://github.com/madeinoz67/bank-statement-separator/commit/86f9a94439243c171229ab77189e8ea81ea1415f))
* resolve shell script syntax error in release-please debug output ([055c9c9](https://github.com/madeinoz67/bank-statement-separator/commit/055c9c93e2b54fb37dbadf9970e925de5a822085))


### Documentation

* update working notes with manual release flow documentation ([e5a7de0](https://github.com/madeinoz67/bank-statement-separator/commit/e5a7de0942259c456c1b4a229f8695841d477d09))

## [2.1.0](https://github.com/madeinoz67/bank-statement-separator/compare/v2.0.0...v2.1.0) (2025-09-06)


### Features

* enhance PyPI package metadata ([d3a3f6a](https://github.com/madeinoz67/bank-statement-separator/commit/d3a3f6a92d96a5487708394354f5a76d920bb416))


### Bug Fixes

* add manual trigger support to release workflow ([374993f](https://github.com/madeinoz67/bank-statement-separator/commit/374993fbf8fa5bb692875350e73a3467dd187e75))
* add workflow_dispatch trigger to release workflow ([5466877](https://github.com/madeinoz67/bank-statement-separator/commit/54668772d29ed8543cde63dad829abf3773571d0))
* correct pyproject.toml structure for classifiers ([9fd2854](https://github.com/madeinoz67/bank-statement-separator/commit/9fd28541697709c5e84ce169d0d064854c48e81a))
* correct pyproject.toml structure for dependencies ([830f0ef](https://github.com/madeinoz67/bank-statement-separator/commit/830f0efbcbdb2321c7e05a6d0517c3c6ffd6a131))
* remove deprecated license classifier ([cd08b9b](https://github.com/madeinoz67/bank-statement-separator/commit/cd08b9b750c2f1f63491fa0a2a7a0255c0633b15))


### Chores

* update version to 2.0.2 for manual release ([9f583cf](https://github.com/madeinoz67/bank-statement-separator/commit/9f583cf52de43fc956396f389d30ca79517f510c))


### Documentation

* add comprehensive release management documentation ([5ab9133](https://github.com/madeinoz67/bank-statement-separator/commit/5ab91336c462323a38cb514bf0fd2c01894c8883))

## [2.0.0](https://github.com/madeinoz67/bank-statement-separator/compare/v1.0.1...v2.0.0) (2025-09-06)


### ⚠ BREAKING CHANGES

* Release process now requires conventional commits

### Features

* add automated semantic versioning with release-please ([c73d9db](https://github.com/madeinoz67/bank-statement-separator/commit/c73d9db792f2b648518539e921fcb23773460368))


### Bug Fixes

* add id-token permission to release-please workflow ([13a8a2b](https://github.com/madeinoz67/bank-statement-separator/commit/13a8a2be58d813a9cab4b00f08300ce33c14d959))
* add include-component-in-tag setting for clean tag format ([2f77978](https://github.com/madeinoz67/bank-statement-separator/commit/2f779784570f615fbd037b6ee513acd921cff23c))
* add tag-format configuration for release-please ([0dbd111](https://github.com/madeinoz67/bank-statement-separator/commit/0dbd1116ab6bc635f7a68d8e4b0b5e99d61a7391))
* update PyPI publishing to use command-line credentials ([8fff33a](https://github.com/madeinoz67/bank-statement-separator/commit/8fff33a71d06fe8b40f2d73ae6841b0b18ff3f90))
* update release-please action to correct repository ([2787d3e](https://github.com/madeinoz67/bank-statement-separator/commit/2787d3ed251cead666b076924065ad10861f0cfe))


### Chores

* **main:** release bank-statement-separator 1.0.0 ([b6b736a](https://github.com/madeinoz67/bank-statement-separator/commit/b6b736ab88d502c716ea9d2d98f61f8f79ddb9aa))
* **main:** release bank-statement-separator 1.0.0 ([ef2b2c9](https://github.com/madeinoz67/bank-statement-separator/commit/ef2b2c973e98e9f0ac9161f4842c0e92addd7b94))
* **main:** release bank-statement-separator 1.0.1 ([f9c84a3](https://github.com/madeinoz67/bank-statement-separator/commit/f9c84a35d24f667bd86bd61006299ed7c58188d9))
* **main:** release bank-statement-separator 1.0.1 ([6d34b7c](https://github.com/madeinoz67/bank-statement-separator/commit/6d34b7c08c87b011e4756c1f8c025ad88cb01bdf))


### Documentation

* update working-notes with recent fixes and improvements ([d11cdc8](https://github.com/madeinoz67/bank-statement-separator/commit/d11cdc8dec5fb9ef35be5220037457f1a2e8e6bc))

## [1.0.1](https://github.com/madeinoz67/bank-statement-separator/compare/bank-statement-separator-v1.0.0...bank-statement-separator-v1.0.1) (2025-09-06)


### Bug Fixes

* add tag-format configuration for release-please ([0dbd111](https://github.com/madeinoz67/bank-statement-separator/commit/0dbd1116ab6bc635f7a68d8e4b0b5e99d61a7391))

## [1.0.0](https://github.com/madeinoz67/bank-statement-separator/compare/bank-statement-separator-v0.1.0...bank-statement-separator-v1.0.0) (2025-09-06)


### ⚠ BREAKING CHANGES

* Release process now requires conventional commits

### Features

* add automated semantic versioning with release-please ([c73d9db](https://github.com/madeinoz67/bank-statement-separator/commit/c73d9db792f2b648518539e921fcb23773460368))


### Bug Fixes

* add id-token permission to release-please workflow ([13a8a2b](https://github.com/madeinoz67/bank-statement-separator/commit/13a8a2be58d813a9cab4b00f08300ce33c14d959))
* update PyPI publishing to use command-line credentials ([8fff33a](https://github.com/madeinoz67/bank-statement-separator/commit/8fff33a71d06fe8b40f2d73ae6841b0b18ff3f90))
* update release-please action to correct repository ([2787d3e](https://github.com/madeinoz67/bank-statement-separator/commit/2787d3ed251cead666b076924065ad10861f0cfe))
