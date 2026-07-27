using Grpc.Core;
using Microsoft.EntityFrameworkCore;
using ChangeService.Data;
using ChangeService.Grpc;

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

}