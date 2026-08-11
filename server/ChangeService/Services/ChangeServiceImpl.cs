using Grpc.Core;
using Microsoft.EntityFrameworkCore;
using ChangeService.Data;
using ChangeService.Grpc;
using Grpc.Net.Client;

namespace ChangeService.Services;

public class ChangeServiceImpl : ChangeService.Grpc.ChangeService.ChangeServiceBase
{
    private readonly ChangeDbContext _db;
    public ChangeServiceImpl(ChangeDbContext db)
    {
        _db = db;
    }

    private static ChangeResponse ToResponse(Models.Change change) => new()
    {
        Id = change.Id,
        Title = change.Title,
        Description = change.Description,
        Status = change.Status,
        RiskLevel = change.RiskLevel,
        CiId = change.CiId
    };

    public override async Task<ChangeResponse> CreateChange(CreateChangeRequest request, ServerCallContext context)
    {
        var change = new Models.Change
        {
            Title = request.Title,
            Description = request.Description,
            RiskLevel = request.RiskLevel,
            CiId = request.CiId
        };
        _db.Changes.Add(change);
        await _db.SaveChangesAsync();
        return ToResponse(change);
    }

    public override async Task<ChangeResponse> GetChange(ChangeIdRequest request, ServerCallContext context)
    {
        var change = await _db.Changes.FindAsync(request.Id);
        if (change is null) throw new RpcException(new Status(StatusCode.NotFound, $"Change {request.Id} not found"));
        return ToResponse(change);
    }

    public override async Task<ChangeList> ListChanges(Empty request, ServerCallContext context)
    {
        var changes = await _db.Changes.ToListAsync();
        var list = new ChangeList();
        list.Changes.AddRange(changes.Select(ToResponse));
        return list;
    }

    public override async Task<ChangeResponse> ApproveChange(ChangeIdRequest request, ServerCallContext context)
    {
        var change = await _db.Changes.FindAsync(request.Id);
        if (change is null) throw new RpcException(new Status(StatusCode.NotFound, $"Change {request.Id} not found"));
        change.Status = "approved";
        await _db.SaveChangesAsync();
        return ToResponse(change);
    }

    public override async Task<ChangeWithCIResponse> GetChangeWithCI(ChangeIdRequest request, ServerCallContext context)
    {
        var change = await _db.Changes.FindAsync(request.Id);
        if (change is null) throw new RpcException(new Status(StatusCode.NotFound, $"Change {request.Id} not found"));

        var cmdbServiceAddr = Environment.GetEnvironmentVariable("CMDB_SERVICE_ADDR") ?? "localhost:50052";
        using var channel = GrpcChannel.ForAddress($"http://{cmdbServiceAddr}");
        var cmdbClient = new Cmdb.Grpc.CmdbService.CmdbServiceClient(channel);
        var ciWithOwner = await cmdbClient.GetCIWithOwnerAsync(new Cmdb.Grpc.CIIdRequest { Id = change.CiId });

        return new ChangeWithCIResponse
        {
            Change = ToResponse(change),
            CiName = ciWithOwner.Ci.Name,
            CiEnvironment = ciWithOwner.Ci.Environment,
            OwnerName = ciWithOwner.OwnerName,
            OwnerEmail = ciWithOwner.OwnerEmail
        };

    }

}