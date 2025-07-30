# Azure AI Agent Workshop

Azure 上で AI エージェントの開発手法を学ぶための実践的なワークショップです。Azure AI Foundry Agent Service と Semantic Kernel を使用して、高度な AI エージェントアプリケーションの構築方法を学習できます。


## クイックスタート

### 前提条件

- Azureサブスクリプション
- GitHub Codespaces環境（推奨）または Python 3.11+
- Azure CLI

### セットアップ

環境構築手順は [SETUP.md](./SETUP.md) をご確認ください。

## 学習コンテンツ

### 01. Azure AI Foundry Agent Service

Azure AI Foundryを使用したエージェント開発の基礎を学習します。

| ノートブック | 内容 |
|-------------|------|
| `01_single_agent_custom_functions.ipynb` | カスタム関数エージェントを用いた関数呼び出し |
| `02_single_agent_code_interpreter.ipynb` | コードインタープリターエージェントを用いたデータ分析・可視化 |
| `03_single_agent_file_search.ipynb` | ファイル検索エージェント RAG の実装 |
| `04_single_agent_mcp.ipynb` | MCP をツールとして利用するエージェント |
| `05_connected_agents.ipynb` | Connected Agents によるエージェント間連携 |

### 02. Semantic Kernel

Semantic Kernelを使用した高度なマルチエージェントシステムを構築します。

| ノートブック | 内容 |
|-------------|------|
| `01_single_agent_chat_completion.ipynb` | Chat Completion API で作るシングルエージェント |
| `02_single_agent_azure_ai.ipynb` | Semantic Kernel で Azure AI Foundry Agent Service 上のエージェントを操作する |
| `03_plugin_agents.ipynb` | エージェントをプラグインとして統合しエージェント間連携を実装 |
| `04_handoffs_terminal.py` | 会話の流れに応じて動的に移譲するハンズオフ・オーケストレーション |
| `05_group_chat.ipynb` | 柔軟なマルチエージェントオーケストレーションを実現するグループチャット・オーケストレーションの入門 |
| `06_group_chat_custom.ipynb` | グループチャット・オーケストレーションの中級編、カスタムグループチャットによる協調連携の柔軟な制御 |
| `07_magentic.ipynb` | 高度なマルチエージェント・オーケストレーションである Magentic で Text-to-SQL を実装 |
| `08_process_framework_simple.ipynb` | ワークフローを自動化するプロセスフレームワークの紹介 |


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