using Microsoft.EntityFrameworkCore;
using ChangeService.Models;

namespace ChangeService.Data;

public class ChangeDbContext : DbContext
{
    public ChangeDbContext(DbContextOptions<ChangeDbContext> options) : base(options) { }

    public DbSet<Change> Changes => Set<Change>();
}
