import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://postgres:Pymapass%40111@db.qqyuvxbtqlblcvxryxud.supabase.co:5432/postgres')
    rows = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'organizations';")
    print([r['column_name'] for r in rows])
    await conn.close()

asyncio.run(check())
