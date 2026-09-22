using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace CommerceLab.Data;

public sealed class CommerceDbContextFactory : IDesignTimeDbContextFactory<CommerceDbContext>
{
    public CommerceDbContext CreateDbContext(string[] args)
    {
        var connectionString = Environment.GetEnvironmentVariable("COMMERCE_DB")
            ?? "Server=localhost,1433;Database=CommerceLab09;User Id=sa;Password=SqlLab!2026Strong;TrustServerCertificate=True";

        var options = new DbContextOptionsBuilder<CommerceDbContext>()
            .UseSqlServer(connectionString)
            .Options;

        return new CommerceDbContext(options);
    }
}
