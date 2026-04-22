import asyncio
import os
import random

from browser_use import Agent, BrowserProfile, BrowserSession
from browser_use.llm.anthropic.chat import ChatAnthropic

LLM = ChatAnthropic(
	model='MiniMax-M2.7',
	api_key=os.environ['MINIMAX_API_KEY'],
	base_url=os.environ.get('MINIMAX_BASE_URL', 'https://api.minimaxi.chat/v1'),
)

CDP_URL = 'http://10.0.0.175:9223'
REPLY_COUNT = 5
INTERVAL_BASE = 120
INTERVAL_JITTER = 60


def make_read_task(is_first: bool) -> str:
	if is_first:
		return '打开 x.com 首页，像正常人一样浏览 feed，慢慢往下滚动看看有什么帖子，浏览几条即可。'
	return '继续在首页 feed 浏览，往下滚动看看新的帖子内容，随便看看就行。'


def make_reply_task(replied_authors: list[str]) -> str:
	authors_str = '、'.join(replied_authors) if replied_authors else '无'
	return f"""\
在当前 feed 中找一条你觉得有意思的帖子，点进去看完完整内容后，写一条自然的回复并提交。

操作步骤：
1. 在 feed 中选一条感兴趣的帖子
2. 点击该帖子进入详情页，阅读完整内容（feed 里的帖子经常被截断，必须点进去看全文）
3. 看完之后再点击回复按钮，输入回复内容并提交
4. 提交后立刻结束任务（done）

回复要求：
- 只回复一条！回复一条之后立即 done，不要继续找下一条
- 表现得像真人，不要像机器人
- 如果原帖是中文，用中文回复；如果原帖是英文，用英文回复。只回复中文或英文
- 回复 1-2 句话，简短、有见地、口语化，像朋友之间聊天
- 可以表达观点、提问、补充信息、或者开个玩笑，不要只说"说得好""赞"这种废话
- 回复内容要体现你看过完整帖子，不要泛泛而谈
- 不要使用 emoji 或表情符号，纯文字回复
- 不要回复以下已经回复过的作者：{authors_str}

重要：必须先点进帖子看完全文再回复，不要在 feed 流里直接回复截断的内容！提交一条回复后立刻结束任务！

提交后报告：你回复了谁（@用户名）的什么内容的帖子，以及你的回复原文。"""


async def main():
	browser_session = BrowserSession(
		browser_profile=BrowserProfile(
			cdp_url=CDP_URL,
			keep_alive=True,
		)
	)

	replied_authors: list[str] = []

	agent = Agent(
		task=make_read_task(is_first=True),
		llm=LLM,
		browser_session=browser_session,
		max_steps=8,
	)

	print('👀 打开 x.com 并浏览 feed...')
	await agent.run()

	for i in range(REPLY_COUNT):
		print(f'\n{"=" * 60}')
		print(f'📝 第 {i + 1}/{REPLY_COUNT} 次回复')
		print(f'{"=" * 60}')

		print('💬 寻找帖子并回复...')
		agent.add_new_task(make_reply_task(replied_authors))
		result = await agent.run()

		content = result.final_result()
		if content:
			print(f'✅ 回复完成: {content[:300]}')
			replied_authors.append(content[:100])
		else:
			print('⚠️ 回复可能未成功，继续下一轮')

		if i < REPLY_COUNT - 1:
			delay = INTERVAL_BASE + random.randint(-INTERVAL_JITTER, INTERVAL_JITTER)
			print(f'\n⏳ 静默等待 {delay} 秒...')
			await asyncio.sleep(delay)

			print('👀 继续浏览 feed...')
			agent.add_new_task(make_read_task(is_first=False))
			await agent.run()

	print(f'\n{"=" * 60}')
	print(f'🎉 任务完成！共尝试 {REPLY_COUNT} 次回复')
	print(f'已回复: {replied_authors}')
	print(f'{"=" * 60}')

	await browser_session.stop()


if __name__ == '__main__':
	asyncio.run(main())
