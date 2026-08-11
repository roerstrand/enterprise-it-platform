from grpc_clients.user_client import list_users, create_user, UserServiceUnavailable

async def get_demo_users():
    return await list_users()

async def create_demo_user(name: str, email: str, password: str):
    return await create_user(name, email, password)

    