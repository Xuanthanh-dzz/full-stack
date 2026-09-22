using CommerceLab.Data.Entities;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace CommerceLab.Data.Tests;

public sealed class CommerceDataTests
{
    [Fact]
    public async Task Projection_returns_recent_order_without_tracking_entities()
    {
        await using var connection = new SqliteConnection("Data Source=:memory:");
        await connection.OpenAsync();

        var options = new DbContextOptionsBuilder<CommerceDbContext>()
            .UseSqlite(connection)
            .Options;

        await using var db = new CommerceDbContext(options);
        await db.Database.EnsureCreatedAsync();
        await SeedData.SeedAsync(db);

        var customerId = await db.Customers
            .Select(customer => customer.CustomerId)
            .SingleAsync();
        var product = await db.Products.SingleAsync(product => product.Sku == "KB-01");

        var order = new Order
        {
            CustomerId = customerId,
            Status = "Paid",
            ShippingName = "Nguyễn An",
            ShippingAddress = "1 Demo Street",
            TotalAmount = product.Price,
            OrderedAt = new DateTime(2026, 9, 22, 0, 0, 0, DateTimeKind.Utc),
            ConcurrencyToken = Guid.NewGuid(),
        };

        order.Items.Add(new OrderItem
        {
            ProductId = product.ProductId,
            ProductNameSnapshot = product.Name,
            UnitPriceSnapshot = product.Price,
            Quantity = 1,
        });

        db.Orders.Add(order);
        await db.SaveChangesAsync();
        db.ChangeTracker.Clear();

        var result = await new OrderReadService(db).GetRecentAsync(customerId, 10);

        var summary = Assert.Single(result);
        Assert.Equal("an@example.com", summary.CustomerEmail);
        Assert.Equal(1, summary.ItemCount);
        Assert.Empty(db.ChangeTracker.Entries());
    }

    [Fact]
    public async Task Global_filter_hides_inactive_products_but_can_be_ignored_explicitly()
    {
        await using var connection = new SqliteConnection("Data Source=:memory:");
        await connection.OpenAsync();

        var options = new DbContextOptionsBuilder<CommerceDbContext>()
            .UseSqlite(connection)
            .Options;

        await using var db = new CommerceDbContext(options);
        await db.Database.EnsureCreatedAsync();

        db.Products.AddRange(
            new Product
            {
                Sku = "ACTIVE",
                Name = "Active product",
                Price = 100m,
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
            },
            new Product
            {
                Sku = "INACTIVE",
                Name = "Inactive product",
                Price = 100m,
                IsActive = false,
                CreatedAt = DateTime.UtcNow,
            });

        await db.SaveChangesAsync();
        db.ChangeTracker.Clear();

        Assert.Equal(1, await db.Products.CountAsync());
        Assert.Equal(2, await db.Products.IgnoreQueryFilters().CountAsync());
    }
}
