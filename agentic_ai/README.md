# 構成
## Azure AI Foundry Agent Service
### 01_foundry_agent_service_single_agent
1.  シングルエージェント
    - MCP ツールを操作 (MicrosoftDocs)
    - （参考）Deep Research Tool

### 02_foundry_agent_service_multi_agent
1.  Connected Agents でマルチエージェントを作成

### Memo
- BingSearch どうしようか
---

## Semancit Kernel 演習
### 03_sk_agent_framework
1. シングルエージェント
    - ChatCompletionAgent
    - AzureAIAgent
2. マルチエージェント（Plugin）

### 04_sk_multi_agent_orchestration
1. Handoffs
2. GroupChat - RoundRobin(競争型)
3. GroupChat - 
4. Magentic

### 05_sk_process_framework
1. 概念および概要説明
2. 各パターン紹介
3. 実践（シーケンスで Deep Research with MicrosftDocs）

## Memo
- メモリー機能実装
- ツールの動的取得
- トレース
- 
---

# 比較
- Azure AI Foundry Agent Service
    - メリット
        - マネージドでインフラの管理不要
        - セキュリティやオブザーバビリティが豊富
        - Microsoft 純正ツールが利用可能
    - デメリット
        - 複雑なマルチエージェント実装が弱い
        - 一部クライアント側で制御できないこともある
- Semancit Kernel および AutoGen などの OSS フレームワーク
    - メリット
        - 柔軟なマルチエージェント・オーケストレーションをサポート
        - コードをオーバーライドして書き換えることも可能（柔軟性が高い）
    - デメリット
        - セキュリティやオブザーバビリティのスキルが必須

# 結論
- まずは Azure AI Foundry Agent Service でシングルエージェントで対応
- マルチエージェントへ拡張する必要性があれば OSS フレームワークを検討

---
最後にやること
- GPT4.1 の TPM を 50 にアップグレード！
