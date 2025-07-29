# Copyright (c) Microsoft. All rights reserved.
import os
import asyncio
from dotenv import load_dotenv

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.functions import kernel_function


load_dotenv(override=True)

PROJECT_ENDPOINT=os.getenv("PROJECT_ENDPOINT")
AZURE_DEPLOYMENT_NAME=os.getenv("AZURE_DEPLOYMENT_NAME")
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY=os.getenv("AZURE_OPENAI_API_KEY")

FOUNDRY_CODE_INTERPRETER_AGENT_ID=os.getenv("FOUNDRY_CODE_INTERPRETER_AGENT_ID")
FOUNDRY_FILE_SEARCH_AGENT_ID=os.getenv("FOUNDRY_FILE_SEARCH_AGENT_ID")

class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """注文の状況を確認します。"""
        # 注文状況の確認をシミュレート
        return f"注文 {order_id} は発送済みで、2-3日で到着予定です。"


class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """注文の返金処理を行います。"""
        # 返金処理をシミュレート
        print(f"注文 {order_id} の返金処理中 - 理由: {reason}")
        return f"注文 {order_id} の返金処理が正常に完了しました。"


class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """注文の返品処理を行います。"""
        # 返品処理をシミュレート
        print(f"注文 {order_id} の返品処理中 - 理由: {reason}")
        return f"注文 {order_id} の返品処理が正常に完了しました。"


# Chat Completion API クライアントの初期化
azure_completion_service  = AzureChatCompletion(
    service_id="azure_completion_agent",
    deployment_name=AZURE_DEPLOYMENT_NAME,
    endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY
)



def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """ハンドオフオーケストレーションに参加するエージェントのリストとハンドオフ関係を返します。

    エージェントとハンドオフ接続は自由に追加または削除できます。
    """
    
    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="問題をトリアージするカスタマーサポートエージェント。",
        instructions="""
        顧客のリクエストを処理してください。
        返金、注文状況、注文返品に関する問題を特定し、適切なエージェントに転送してください。
        """,
        service=azure_completion_service,
    )

    refund_agent = ChatCompletionAgent(
        name="RefundAgent",
        description="返金を処理するカスタマーサポートエージェント。",
        instructions="""
        返金リクエストを処理してください。
        処理が完了したら、他に依頼がないか丁寧に確認して下さい。
        """,
        service=azure_completion_service,
        plugins=[OrderRefundPlugin()],
    )

    order_status_agent = ChatCompletionAgent(
        name="OrderStatusAgent",
        description="注文状況を確認するカスタマーサポートエージェント。",
        instructions="""
        注文状況リクエストを処理してください。
        処理が完了したら、他に依頼がないか丁寧に確認して下さい。
        """,
        service=azure_completion_service,
        plugins=[OrderStatusPlugin()],
    )

    order_return_agent = ChatCompletionAgent(
        name="OrderReturnAgent",
        description="注文の返品を処理するカスタマーサポートエージェント。",
        instructions="""
        注文返品リクエストを処理してください。
        処理が完了したら、他に依頼がないか丁寧に確認して下さい。
        """,
        service=azure_completion_service,
        plugins=[OrderReturnPlugin()],
    )

    # エージェント間のハンドオフ関係を定義
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=support_agent.name,
            target_agents={
                refund_agent.name: "問題が返金関連の場合、このエージェントに転送してください",
                order_status_agent.name: "問題が注文状況関連の場合、このエージェントに転送してください",
                order_return_agent.name: "問題が注文返品関連の場合、このエージェントに転送してください",
            },
        )
        .add(
            source_agent=refund_agent.name,
            target_agent=support_agent.name,
            description="問題が返金関連でない場合、このエージェントに転送してください",
        )
        .add(
            source_agent=order_status_agent.name,
            target_agent=support_agent.name,
            description="問題が注文状況関連でない場合、このエージェントに転送してください",
        )
        .add(
            source_agent=order_return_agent.name,
            target_agent=support_agent.name,
            description="問題が注文返品関連でない場合、このエージェントに転送してください",
        )
    )

    return [support_agent, refund_agent, order_status_agent, order_return_agent], handoffs


def agent_response_callback(message: ChatMessageContent) -> None:
    """エージェントからのメッセージを表示するオブザーバー関数。

    この関数は、エージェントが応答を生成するたびに呼び出されることに注意してください。
    これには、オーケストレーション内の他のエージェントには見えない内部処理メッセージ
    （ツール呼び出しなど）も含まれます。
    """
    print(f"{message.name}: {message.content}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"'{item.name}' を引数 '{item.arguments}' で呼び出し中")
        if isinstance(item, FunctionResultContent):
            print(f"'{item.name}' からの結果: '{item.result}'")


def human_response_function() -> ChatMessageContent:
    """エージェントからのメッセージを表示するオブザーバー関数。"""
    user_input = input("ユーザー: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """エージェントを実行するメイン関数。"""
    # 1. 複数のエージェントでハンドオフオーケストレーションを作成
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. ランタイムを作成して開始
    runtime = InProcessRuntime()
    runtime.start()

    # 3. タスクとランタイムでオーケストレーションを呼び出し
    orchestration_result = await handoff_orchestration.invoke(
        task="サポートを求めている顧客に挨拶してください。",
        runtime=runtime,
    )

    # 4. 結果を待機
    value = await orchestration_result.get()
    print(value)

    # 5. 呼び出し完了後にランタイムを停止
    await runtime.stop_when_idle()

    """
    Sample output:
    TriageAgent: こんにちは！カスタマーサポートにご連絡いただきありがとうございます。ご用件をお伺いします。返金、注文状況、または返品に関するご質問がございましたら、お気軽にお知らせください。どうぞよろしくお願いいたします。
    ユーザー: 返金対応です。
    TriageAgent: 
    'Handoff-transfer_to_RefundAgent' を引数 '{}' で呼び出し中
    TriageAgent:
    'Handoff-transfer_to_RefundAgent' からの結果: 'None'
    TriageAgent:
    RefundAgent: かしこまりました。返金をご希望とのことですね。

    ご対応のため、以下の情報を教えていただけますか？
    - 注文番号
    - 返金理由

    ご提供いただき次第、迅速に返金処理を開始いたします。
    ユーザー: 注文番号123で、色違いでした。
    注文 123 の返金処理中 - 理由: 色違い
    RefundAgent: 
    'OrderRefundPlugin-process_refund' を引数 '{"order_id":"123","reason":"色違い"}' で呼び出し中
    RefundAgent:
    'OrderRefundPlugin-process_refund' からの結果: '注文 123 の返金処理が正常に完了しました。'
    RefundAgent: 注文番号123の返金処理が完了いたしました。ご不便をおかけし申し訳ございませんでした。

    他にご不明な点やご依頼がございましたら、どうぞお知らせください。
    ユーザー: ありがとうございます。先日注文した商品の注文ステータスを確認したいです
    RefundAgent: 承知いたしました。注文ステータスをご確認いたしますので、対象となるご注文番号を教えていただけますか？
    ユーザー: 345
    RefundAgent: 
    'Handoff-transfer_to_TriageAgent' を引数 '{}' で呼び出し中
    RefundAgent:
    'Handoff-transfer_to_TriageAgent' からの結果: 'None'
    RefundAgent:
    TriageAgent: 
    'Handoff-transfer_to_OrderStatusAgent' を引数 '{}' で呼び出し中
    TriageAgent:
    'Handoff-transfer_to_OrderStatusAgent' からの結果: 'None'
    TriageAgent:
    OrderStatusAgent: 
    'OrderStatusPlugin-check_order_status' を引数 '{"order_id":"345"}' で呼び出し中
    OrderStatusAgent:
    'OrderStatusPlugin-check_order_status' からの結果: '注文 345 は発送済みで、2-3日で到着予定です。'
    OrderStatusAgent: 注文番号345の商品は発送済みで、到着予定は2〜3日後となっております。

    他にご不明な点やご依頼はございますか？
    ユーザー: ありがとうございました。
    Task is completed with summary: お客様の注文番号123の返金処理と、注文番号345の注文ステータス確認を行い、ご案内しました。
    OrderStatusAgent: 
    'Handoff-complete_task' を引数 '{"task_summary":"お客様の注文番号123の返金処理と、注文番号345の注文ステータス確認を行い、ご案内しました。"}' で呼び出し中
    OrderStatusAgent:
    'Handoff-complete_task' からの結果: 'None'
    OrderStatusAgent:
    """


if __name__ == "__main__":
    asyncio.run(main())