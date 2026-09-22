using CommerceLab.Data;
using Microsoft.EntityFrameworkCore;

var connectionString = Environment.GetEnvironmentVariable("COMMERCE_DB")
    ?? throw new InvalidOperationException(
        "Set COMMERCE_DB before running the SQL Server demo.");

var options = new DbContextOptionsBuilder<CommerceDbContext>()
    .UseSqlServer(connectionString)
    .EnableDetailedErrors()
    .Options;

await using var db = new CommerceDbContext(options);
await db.Database.EnsureDeletedAsync();
await db.Database.EnsureCreatedAsync();
await SeedData.SeedAsync(db);

var customerId = await db.Customers
    .Where(customer => customer.Email == "an@example.com")
    .Select(customer => customer.CustomerId)
    .SingleAsync();

var productId = await db.Products
    .Where(product => product.Sku == "KB-01")
    .Select(product => product.ProductId)
    .SingleAsync();

var checkout = new CheckoutService(db);
var orderId = await checkout.CheckoutAsync(customerId, productId, quantity: 2);

var readService = new OrderReadService(db);
var recent = await readService.GetRecentAsync(customerId, take: 10);

var remainingStock = await db.Stocks
    .Where(stock => stock.ProductId == productId)
    .Select(stock => stock.Quantity)
    .SingleAsync();

Console.WriteLine($"OrderId={orderId}");
Console.WriteLine($"Orders={recent.Count}");
Console.WriteLine($"Total={recent.Single().TotalAmount:0.##}");
Console.WriteLine($"RemainingStock={remainingStock}");
