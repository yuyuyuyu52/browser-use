import asyncio
import os
import random

from browser_use import Agent, BrowserProfile, BrowserSession


def make_llm():
	provider = os.environ.get('LLM_PROVIDER', 'openrouter')
	if provider == 'google':
		from browser_use.llm.google.chat import ChatGoogle
		return ChatGoogle(
			model='gemini-3-flash-preview',
			api_key=os.environ['GOOGLE_API_KEY'],
		)
	else:
		from browser_use.llm.openrouter.chat import ChatOpenRouter
		return ChatOpenRouter(
			model='google/gemini-3-flash-preview',
			api_key=os.environ['OPENROUTER_API_KEY'],
		)


LLM = make_llm()

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

操作步骤（严格按顺序，每步只做一个动作）：
1. 在 feed 中选一条感兴趣的帖子，点击帖子正文进入详情页
2. 阅读完整内容（feed 里的帖子经常被截断，必须点进去看全文）
3. 找到详情页底部的回复输入框，点击输入框使其获得焦点
4. 在回复输入框中输入你的回复文字（这一步只输入文字，不要点击任何按钮）
5. 输入完成后，找到回复输入框旁边的蓝色"回复"或"Reply"提交按钮并点击
   注意：这个提交按钮是回复框右侧/下方的蓝色按钮，不是帖子底部带数字的回复图标！
   带数字的按钮（如"63 回复"）是查看回复数的按钮，点了会重新弹出回复框，不会提交！
6. 等待看到"你的帖子已发送"提示后，再调用 done 结束任务

回复要求：
- 只回复一条！回复一条之后立即 done，不要继续找下一条
- 表现得像真人，不要像机器人
- 如果原帖是中文，用中文回复；如果原帖是英文，用英文回复。只回复中文或英文
- 回复 1-2 句话，简短、有见地、口语化，像朋友之间聊天
- 可以表达观点、提问、补充信息、或者开个玩笑，不要只说"说得好""赞"这种废话
- 回复内容要体现你看过完整帖子，不要泛泛而谈
- 不要使用 emoji 或表情符号，纯文字回复
- 不要回复以下已经回复过的作者：{authors_str}

重要：必须先点进帖子看完全文再回复！提交一条回复后立刻结束任务！
重要：必须看到"你的帖子已发送"的提示才算提交成功，否则不要调用 done！

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
	)

	print('👀 打开 x.com 并浏览 feed...')
	await agent.run(max_steps=10)

	for i in range(REPLY_COUNT):
		print(f'\n{"=" * 60}')
		print(f'📝 第 {i + 1}/{REPLY_COUNT} 次回复')
		print(f'{"=" * 60}')

		print('💬 寻找帖子并回复...')
		agent.add_new_task(make_reply_task(replied_authors))
		result = await agent.run(max_steps=15)

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
			await agent.run(max_steps=8)

	print(f'\n{"=" * 60}')
	print(f'🎉 任务完成！共尝试 {REPLY_COUNT} 次回复')
	print(f'已回复: {replied_authors}')
	print(f'{"=" * 60}')

	await browser_session.stop()


if __name__ == '__main__':
	asyncio.run(main())
