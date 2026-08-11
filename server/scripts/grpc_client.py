import grpc
from protos import user_pb2
from protos import user_pb2_grpc

def run():
    # Open a channel to the grpc server
    with grpc.insecure_channel("localhost:50051") as channel:

        # Create a stub - the client's proxy to the server
        stub = user_pb2_grpc.UserServiceStub(channel)

        response = stub.GetAllUsers(user_pb2.Empty())
        print("All users:")
        for user in response.users:
            print(f" id={user.id}, name={user.name}")

        new_user = stub.CreateUser(user_pb2.CreateUserRequest(name="Anna", email="anna@example.com", password="test1234"))
        print(f"\nCreated: id={new_user.id}, name={new_user.name}")

        found = stub.GetUserById(user_pb2.UserIdRequest(id=new_user.id))
        print(f"Found: id={found.id}, name={found.name}")

if __name__ == "__main__":
    run()

