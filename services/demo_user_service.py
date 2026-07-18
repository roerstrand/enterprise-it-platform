from grpc_clients.user_client import list_users, create_user, UserServiceUnavailable

def get_demo_users():
    return list_users()

def create_demo_user(name: str, email: str, password: str):
    return create_user(name, email, password)

    