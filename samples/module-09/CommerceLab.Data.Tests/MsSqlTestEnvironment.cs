using Testcontainers.MsSql;

namespace CommerceLab.Data.Tests;

public static class MsSqlTestEnvironment
{
    public static MsSqlContainer Create()
    {
        return new MsSqlBuilder("mcr.microsoft.com/mssql/server:2025-latest")
            .Build();
    }
}
