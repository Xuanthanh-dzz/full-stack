using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace CommerceLab.Data;

public sealed class CommerceDbContextFactory : IDesignTimeDbContextFactory<CommerceDbContext>
{
    public CommerceDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable("COMMERCE_DB")
            ?? throw new InvalidOperationException(
                "Set COMMERCE_DB before running EF Core design-time commands.");

        var options = new DbContextOptionsBuilder<CommerceDbContext>()
            .UseSqlServer(connectionString)
            .Options;

        return new CommerceDbContext(options);
    }
}
