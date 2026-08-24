using System.Text.Json;
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

    // Best-effort, precis som audit_client.py pa Python-sidan: en nere audit-service
    // ska aldrig fa en change-mutation att misslyckas.
    private static async Task RecordAuditEventAsync(int actorUserId, string actorEmail, string action, int entityId, object? before, object? after)
    {
        try
        {
            var auditServiceAddr = Environment.GetEnvironmentVariable("AUDIT_SERVICE_ADDR") ?? "localhost:50055";
            using var channel = GrpcChannel.ForAddress($"http://{auditServiceAddr}");
            var auditClient = new AuditService.Grpc.AuditService.AuditServiceClient(channel);
            await auditClient.RecordAuditEventAsync(new AuditService.Grpc.RecordAuditEventRequest
            {
                ActorUserId = actorUserId,
                ActorEmail = actorEmail ?? "",
                Action = action,
                EntityType = "change",
                EntityId = entityId.ToString(),
                BeforeJson = before is null ? "" : JsonSerializer.Serialize(before),
                AfterJson = after is null ? "" : JsonSerializer.Serialize(after),
            });
        }
        catch (Exception e)
        {
            Console.WriteLine($"[ChangeServiceImpl] failed to record audit event ({action} change#{entityId}): {e.Message}");
        }
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

        await RecordAuditEventAsync(request.ActorUserId, request.ActorEmail, "change.created", change.Id,
            before: null, after: new { title = change.Title, riskLevel = change.RiskLevel, ciId = change.CiId, status = change.Status });

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

    public override async Task<ChangeResponse> ApproveChange(ChangeActionRequest request, ServerCallContext context)
    {
        var change = await _db.Changes.FindAsync(request.Id);
        if (change is null) throw new RpcException(new Status(StatusCode.NotFound, $"Change {request.Id} not found"));
        if (change.Status == "approved")
        {
            // Ingen lifecycle-graf ännu för Change (bara requested -> approved finns idag), men
            // en redan godkänd change ska inte tyst kunna "godkännas" om igen och skriva en ny audit-post.
            throw new RpcException(new Status(StatusCode.FailedPrecondition, $"Change {request.Id} is already approved"));
        }
        var previousStatus = change.Status;
        change.Status = "approved";
        await _db.SaveChangesAsync();

        await RecordAuditEventAsync(request.ActorUserId, request.ActorEmail, "change.approved", change.Id,
            before: new { status = previousStatus }, after: new { status = change.Status });

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