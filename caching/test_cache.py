import grpc, time
from protos import cmdb_pb2, cmdb_pb2_grpc

channel = grpc.insecure_channel("localhost:50052")
stub = cmdb_pb2_grpc.CmdbServiceStub(channel)

start = time.perf_counter()
stub.GetCI(cmdb_pb2.CIIdRequest(id=4))
print(f"1st call: {time.perf_counter() - start:.4f}s")

start = time.perf_counter()
stub.GetCI(cmdb_pb2.CIIdRequest(id=4))
print(f"2nd call: {time.perf_counter() - start:.4f}s")