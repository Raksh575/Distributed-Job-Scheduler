import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:Pymapass%40111@db.qqyuvxbtqlblcvxryxud.supabase.co:5432/postgres"

async def test_conn():
    print("Creating async engine...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    print("Connecting to database...")
    try:
        async with engine.connect() as conn:
            print("Successfully connected!")
            result = await conn.execute(text("SELECT version();"))
            row = result.fetchone()
            print("PostgreSQL Version:", row[0])
            
            result_users = await conn.execute(text("SELECT id, email, hashed_password, is_active, is_verified FROM users;"))
            rows = result_users.fetchall()
            print("Users in table:")
            for r in rows:
                print(r)
            
    except Exception as e:
        print("Connection failed!")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_conn())
