import grpc
from protos import user_pb2
from protos import user_pb2_grpc

def run():
    # Öppna en kanal t grpc-servern
    with grpc.insecure_channel("localhost:50051") as channel:

        # Skapa en stub - klientens proxy mot servern
        stub = user_pb2_grpc.UserServiceStub(channel)

        response = stub.GetAllUsers(user_pb2.Empty())
        print("Alla användare:")
        for user in response.users:
            print(f" id={user.id}, name={user.name}")

        new_user = stub.CreateUser(user_pb2.CreateUserRequest(name="Anna", email="anna@example.com"))
        print(f"\nSkapade: id={new_user.id}, name={new_user.name}")

        found = stub.GetUserById(user_pb2.UserIdRequest(id=new_user.id))
        print(f"Hittade: id={found.id}, name={found.name}")

if __name__ == "__main__":
    run()

