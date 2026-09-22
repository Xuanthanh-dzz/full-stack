using CommerceLab.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace CommerceLab.Data;

public sealed class CheckoutService(CommerceDbContext db)
{
    public async Task<long> CheckoutAsync(
        long customerId,
        long productId,
        int quantity,
        CancellationToken cancellationToken = default)
    {
        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(quantity));
        }

        await using var transaction = await db.Database.BeginTransactionAsync(cancellationToken);

        var product = await db.Products
            .AsNoTracking()
            .SingleOrDefaultAsync(x => x.ProductId == productId, cancellationToken)
            ?? throw new InvalidOperationException("Product not available.");

        var affected = await db.Stocks
            .Where(x => x.ProductId == productId && x.Quantity >= quantity)
            .ExecuteUpdateAsync(
                setters => setters.SetProperty(
                    stock => stock.Quantity,
                    stock => stock.Quantity - quantity),
                cancellationToken);

        if (affected != 1)
        {
            throw new InvalidOperationException("Not enough stock.");
        }

        var total = product.Price * quantity;
        var order = new Order
        {
            CustomerId = customerId,
            Status = "Pending",
            ShippingName = "Nguyễn An",
            ShippingAddress = "1 Demo Street, Hà Nội",
            TotalAmount = total,
            OrderedAt = DateTime.UtcNow,
            ConcurrencyToken = Guid.NewGuid(),
        };

        order.Items.Add(new OrderItem
        {
            ProductId = product.ProductId,
            ProductNameSnapshot = product.Name,
            UnitPriceSnapshot = product.Price,
            Quantity = quantity,
        });

        order.Payments.Add(new Payment
        {
            Provider = "DemoPay",
            Status = "Pending",
            Amount = total,
            CreatedAt = DateTime.UtcNow,
        });

        db.Orders.Add(order);
        await db.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        return order.OrderId;
    }
}
