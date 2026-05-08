import asyncio
import asyncpg

async def run():
    try:
        # 替换为你 .env 里的实际参数
        conn = await asyncpg.connect(
    user='postgres', 
    password='2004',
    database='media_publisher', 
    host='127.0.0.1',
    ssl=False  # 强制关闭 SSL
)
        print("连接成功！")
        await conn.close()
    except Exception as e:
        print(f"连接失败: {e}")

asyncio.run(run())