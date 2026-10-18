using CommerceLab.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace CommerceLab.Data;

public static class SeedData
{
    public static async Task SeedAsync(
        CommerceDbContext db,
        CancellationToken cancellationToken = default)
    {
        if (await db.Customers.AnyAsync(cancellationToken))
        {
            return;
        }

        var customer = new Customer
        {
            Email = "an@example.com",
            FullName = "Nguyễn An",
            CreatedAt = new DateTime(2026, 9, 1, 0, 0, 0, DateTimeKind.Utc),
        };

        var keyboard = new Product
        {
            Sku = "KB-01",
            Name = "Keyboard Pro",
            Price = 1_200_000m,
            CreatedAt = new DateTime(2026, 9, 1, 0, 0, 0, DateTimeKind.Utc),
        };

        var mouse = new Product
        {
            Sku = "MS-01",
            Name = "Mouse Pro",
            Price = 700_000m,
            CreatedAt = new DateTime(2026, 9, 1, 0, 0, 0, DateTimeKind.Utc),
        };

        db.AddRange(customer, keyboard, mouse);
        db.Stocks.AddRange(
            new Stock { Product = keyboard, Quantity = 10 },
            new Stock { Product = mouse, Quantity = 20 });

        await db.SaveChangesAsync(cancellationToken);
    }
}
