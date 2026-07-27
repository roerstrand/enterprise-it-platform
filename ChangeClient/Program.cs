using Grpc.Net.Client;
using ChangeService.Grpc;

using var channel = GrpcChannel.ForAddress("http://localhost:50054");
var client = new ChangeService.Grpc.ChangeService.ChangeServiceClient(channel);

var created = await client.CreateChangeAsync(new CreateChangeRequest
{
    Title = "Upgrade Postgres to 17",
    Description = "Planned maintenance window",
    RiskLevel = "MEDIUM",
    CiId = 12
});
Console.WriteLine($"Created: id={created.Id}, status={created.Status}");

var approved = await client.ApproveChangeAsync(new ChangeIdRequest { Id = created.Id });
Console.WriteLine($"Approved: id={approved.Id}, status={approved.Status}");

var all = await client.ListChangesAsync(new Empty());
Console.WriteLine("\nAll changes:");
foreach (var c in all.Changes)
    Console.WriteLine($"  id={c.Id}, title={c.Title}, status={c.Status}");