# Azure AI Foundry Agent Service
## 01_azure_ai_foundry_agent_service_singleagent
1.  シングルエージェント
    - MCP ツールを操作 (MicrosoftDocs)
## 02_azure_ai_foundry_agent_service_multiagent
2.  Connected Agents でマルチエージェントを作成
3. （参考）Deep Research Tool

# Memo
- BingSearch
---

# Semancit Kernel 演習
1. シングルエージェント
    - ChatCompletionAgent
    - AzureAIAgent
2. マルチエージェント（Plugin）
3. マルチエージェント・オーケストレーション
    - Handoffs
    - GroupChat - RoundRobin(競争型)
    - GroupChat - 
    - Magentic
4. プロセスフレームワーク
    - 概念および概要説明
    - シーケンス

# Memo
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