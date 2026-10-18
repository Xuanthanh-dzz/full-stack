using Microsoft.EntityFrameworkCore;

namespace CommerceLab.Data;

public sealed record OrderSummary(
    long OrderId,
    string CustomerEmail,
    string Status,
    decimal TotalAmount,
    DateTime OrderedAt,
    int ItemCount);

public sealed class OrderReadService(CommerceDbContext db)
{
    public Task<List<OrderSummary>> GetRecentAsync(
        long customerId,
        int take,
        CancellationToken cancellationToken = default)
    {
        return db.Orders
            .AsNoTracking()
            .Where(order => order.CustomerId == customerId)
            .OrderByDescending(order => order.OrderedAt)
            .ThenByDescending(order => order.OrderId)
            .Select(order => new OrderSummary(
                order.OrderId,
                order.Customer.Email,
                order.Status,
                order.TotalAmount,
                order.OrderedAt,
                order.Items.Count))
            .Take(take)
            .ToListAsync(cancellationToken);
    }
}
