# Azure AI Agent Workshop

Azure 上で AI エージェントの開発手法を学ぶための実践的なワークショップです。Azure AI Foundry Agent ServiceとSemantic Kernelを使用して、高度なAIエージェントアプリケーションの構築方法を学習できます。

## 概要

このワークショップでは、以下の技術とコンセプトを学習します：
- **Azure AI Foundry Agent Service**: Azureクラウドでのエージェント開発
- **Semantic Kernel**: マイクロソフトのAIオーケストレーションフレームワーク
- **マルチエージェントシステム**: 複数のAIエージェントによる協調処理
- **データベース統合**: PostgreSQLとCosmosDBとの連携
- **Model Context Protocol (MCP)**: エージェント間の標準化された通信

## クイックスタート

### 前提条件

- Azureサブスクリプション
- GitHub Codespaces環境（推奨）またはPython 3.11+
- Azure CLI

### セットアップ

詳細なセットアップ手順は [SETUP.md](./SETUP.md) をご確認ください。

## 学習コンテンツ

### 01. Azure AI Foundry Agent Service

Azure AI Foundryを使用したエージェント開発の基礎を学習します。

| ノートブック | 内容 | 学習項目 |
|-------------|------|---------|
| `01_single_agent_custom_functions.ipynb` | カスタム関数エージェント | 関数呼び出し、ツール統合 |
| `02_single_agent_code_interpreter.ipynb` | コードインタープリター | Python実行、データ分析 |
| `03_single_agent_file_search.ipynb` | ファイル検索エージェント | ファイル処理、検索機能 |
| `04_single_agent_mcp.ipynb` | MCPエージェント | Model Context Protocol |
| `05_connected_agents.ipynb` | Connected エージェント | エージェント間連携 |

### 02. Semantic Kernel

Semantic Kernelを使用した高度なマルチエージェントシステムを構築します。

| ノートブック | 内容 | 学習項目 |
|-------------|------|---------|
| `01_single_agent_chat_completion.ipynb` | Chat Completion API で作るシングルエージェント | SK基礎、プロンプト管理 |
| `02_single_agent_azure_ai.ipynb` | Azure AI Foundry 統合 | Azure AIサービス連携 |
| `03_plugin_agents.ipynb` | プラグインエージェント | プラグイン開発、拡張性 |
| `04_handoffs_terminal.py` | ハンドオフシステム | エージェント移譲 |
| `05_group_chat.ipynb` | グループチャット | 複数エージェント対話 |
| `06_group_chat_custom.ipynb` | カスタムグループチャット | 高度な制御フロー |
| `07_magentic.ipynb` | Magentic | 自動制御、DB統合 |
| `08_process_framework_simple.ipynb` | プロセスフレームワーク | ワークフロー自動化 |


## 技術スタック

- **AI フレームワーク**: Azure AI Foundry, Semantic Kernel
- **言語**: Python 3.11+
- **データベース**: Azure Database for PostgreSQL, Azure Cosmos DB
- **クラウド**: Microsoft Azure
- **プロトコル**: Model Context Protocol (MCP)
- **開発環境**: GitHub Codespaces, Jupyter Notebook

## プロジェクト構造

```
Azure-AI-Agent-Workshop/
├── agentic_ai/                    # メインの学習コンテンツ
│   ├── 01_azure_ai_foundry_agent_service/  # Azure AI Foundryチュートリアル
│   ├── 02_semantic_kernel/                  # Semantic Kernelチュートリアル
│   └── README.md
├── infra/                         # インフラストラクチャ設定
│   ├── init_setup.sh             # Azure リソース作成スクリプト
│   ├── main.bicep                # Azure Bicep テンプレート
│   └── backend_services/         # MCPサーバー実装
├── docs/                          # ドキュメント
├── requirements.txt               # Python依存関係
├── SETUP.md                      # 詳細セットアップ手順
└── README.md                     # このファイル
```

## トラブルシューティング

### よくある問題

1. **Azure OpenAI クォータ制限**
   ```
   Error: TPM (Tokens Per Minute) quota exceeded
   ```
   → Azure Portalでクォータ設定を確認してください

2. **環境変数の設定ミス**
   ```
   Error: Environment variable not found
   ```
   → `.env`ファイルの設定を再確認してください

3. **依存関係の問題**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## ライセンス

このプロジェクトは [MIT License](./LICENSE) の下で公開されています。

## 謝辞

- Microsoft Partner Azure AI チーム

---